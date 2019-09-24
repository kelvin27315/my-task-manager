from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
from mastodon import Mastodon
from datetime import date
import json

def read_fitbit_key():
    with open("key/fitbit_token.secret") as f:
        key = f.readlines()
    client_id = key[0][:-1]
    client_secret = key[1][:-1]
    access_token = key[2][:-1]
    refresh_token = key[3]
    return(client_id, client_secret, access_token, refresh_token)

class fitbit_client(object):
    refresh_token_url="https://api.fitbit.com/oauth2/token"
    def __init__(self, client_id, client_secret, access_token, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        token = {"access_token": access_token, "refresh_token": refresh_token}
        self.session = OAuth2Session(
            client_id,
            token = token,
            auto_refresh_url = "https://api.fitbit.com/oauth2/token",
        )

    def refresh_call_back(token):
            with open("key/fitbit_token.secret", "w") as f:
                f.write(client_id + "\n")
                f.write(client_secret + "\n")
                f.write(token["access_token"] + "\n")
                f.write(token["refresh_token"])
            self.access_token = token["access_token"]
            self.refresh_token = token["refresh_token"]

    def refresh_token(self):
        token = self.session.refresh_token(
            self.refresh_token_url,
            auth=HTTPBasicAuth(self.client_id, self.client_secret)
        )
        self.refresh_call_back(token)
        return(token)

    def make_request(self, url):
        header = {"Accept-Language": None}
        headers = {"headers": header}
        method = "GET"
        response = self.session.request(method, url, client_id=self.client_id, client_secret=self.client_secret, **headers)
        if response.status_code == 401:
            d = json.loads(response.content.decode("utf8"))
            if d["errors"][0]["errorType"] == "expired_token":
                self.refresh_token()
                response = self.session.request(method, url, client_id=self.client_id, client_secret=self.client_secret, **headers)
        return(response)

    def get_sleep(self):
        url = "https://api.fitbit.com/1.2/user/-/sleep/date/{}.json".format(date.today())
        return(self.make_request(url))

    def get_heart_rate(self):
        url = "https://api.fitbit.com/1/user/-/activities/heart/date/today/1d/5min.json"
        return(self.make_request(url))

def get_user_status(client):
    heart_rate_data = json.loads(client.get_heart_rate().content.decode("utf8"))
    heart_rate_zone = heart_rate_data["activities-heart"][0]["value"]["heartRateZones"]
    heart_rate = heart_rate_data["activities-heart-intraday"]["dataset"][-1]["value"]
    status_name = "non"
    for zone in heart_rate_zone:
        if zone["min"] < heart_rate and heart_rate <= zone["max"]:
            status_name = zone["name"]
    status_dic = {"Out of Range": " 😐","Fat Burn": " 😐","Cardio": " 😓","Peak": " 😅", "non": " 🤔"}
    status = status_dic[status_name]
    return(status)

def mstdn_name_update(status):
    mastodon = Mastodon(
        access_token="key/username-updater-usercred.secret",
        api_base_url="https://mstdn.maud.io"
    )
    with open("mstdn-id.txt", "r") as f:
        id = int(f.read())
    display_name = mastodon.account(id)["display_name"][:-2]
    mastodon.account_update_credentials(display_name = display_name + status)

if __name__ == "__main__":
    client_id, client_secret, access_token, refresh_token = read_fitbit_key()
    client = fitbit_client(client_id, client_secret, access_token, refresh_token)
    status = get_user_status(client)
    mstdn_name_update(status)