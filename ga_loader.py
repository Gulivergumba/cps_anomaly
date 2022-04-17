# Load python libraries
import json
import datetime
from user import User
from flask import request
from oauthlib.oauth2 import WebApplicationClient
import requests
import google_config as gc


class ga_user():

    def __init__(self, code=None, token=None, acc=None, prop=None, view=None):
        self.code = code
        self.token = token
        self.client = WebApplicationClient(gc.GOOGLE_CLIENT_ID)
        self.account_list = []
        self.property_list = []
        self.view_list = []
        self.email = None
        if token is None:
            self.prepare_request()
        else:
            self.client.parse_request_body_response(json.dumps(self.token))
        self.get_email()

    def get_email(self):
        self.refresh_token()
        if self.email is None:
            google_provider_cfg = gc.get_google_provider_cfg()
            userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
            uri, headers, body = self.client.add_token(userinfo_endpoint)
            userinfo_response = requests.get(uri, headers=headers, data=body)
            
            if userinfo_response.status_code == 200:
                self.email = userinfo_response.json()["email"]
            
        return self.email


    def prepare_request(self):

        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = gc.get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send request to get tokens! Yay tokens!
        token_url, headers, body = self.client.prepare_token_request(
  	    token_endpoint,
            authorization_response=request.url,
	    redirect_url=request.base_url,
	    code=self.code,
        )

        token_response = requests.post(
	    token_url,
	    headers=headers,
	    data=body,
	    auth=(gc.GOOGLE_CLIENT_ID, gc.GOOGLE_CLIENT_SECRET),
        )
        
        self.token = token_response.json()
        self.token["issue_time"]=datetime.datetime.now().timestamp()

        # Parse the tokens!
        self.client.parse_request_body_response(json.dumps(token_response.json()))
       
        if self.email is None:
            self.get_email()
        User.update(self.token, self.email)


    def refresh_token(self):
        time_expires = self.token['issue_time'] + self.token['expires_in']
        time_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).timestamp()
        if(time_expires < time_now - 100):
            #refresh token      
            # Find out what URL to hit to get tokens that allow you to ask for
            # things on behalf of a user
            google_provider_cfg = gc.get_google_provider_cfg()
            token_endpoint = google_provider_cfg["token_endpoint"]

            # Prepare and send request to get tokens! Yay tokens!
            token_url, headers, body = self.client.prepare_refresh_token_request(
                token_endpoint,
                refresh_token=self.token['refresh_token'],
                scope=self.token['scope'],
            )   

            token_response = requests.post(
                token_url,
                headers=headers,
                data=body,
                auth=(gc.GOOGLE_CLIENT_ID, gc.GOOGLE_CLIENT_SECRET),
            )   
            
            refresh_token = self.token['refresh_token']    
            self.token = token_response.json()
            self.token['refresh_token'] = refresh_token
            self.token["issue_time"]=datetime.datetime.now().timestamp()

            # Parse the tokens!
            self.client.parse_request_body_response(json.dumps(token_response.json()))  
            
            if self.email is None:
               self.get_email()
            User.update(self.token, self.email) 


    def set_account_list(self):
        self.refresh_token()
        uri, headers, body = self.client.add_token("https://www.googleapis.com/analytics/v3/management/accounts")
        userinfo_response = requests.get(uri, headers=headers, data=body)
        if userinfo_response.status_code == 200:
            self.account_list = userinfo_response.json()["items"]
        else:
            self.account_list = []

    def get_account_names(self):
        if not self.account_list:
            self.set_account_list()
        return [item['name'] for item in self.account_list]

    def set_property_list(self, selected_account):
        self.refresh_token()

        account_id = self.account_list[selected_account]["id"]
        self.property_list = []

        # Check for UA properties:
        uri, headers, body = self.client.add_token("https://www.googleapis.com/analytics/v3/management/accounts/"+account_id+"/webproperties")
        userinfo_response = requests.get(uri, headers=headers, data=body)
        if userinfo_response.status_code == 200:
            for item in userinfo_response.json()["items"]:
                property_item = {}
                property_item["type"] = 'UA'
                property_item["id"] = item['id']
                property_item["name"] = item['name']
                self.property_list.append(property_item)

        # Check for GA properties:
        uri, headers, body = self.client.add_token("https://analyticsadmin.googleapis.com/v1alpha/properties")
        payload = {'filter':'parent:accounts/'+account_id}
        userinfo_response = requests.get(uri, params=payload, headers=headers, data=body)
        if userinfo_response.status_code == 200:
            for item in userinfo_response.json()["properties"]:
                property_item = {}
                property_item["type"] = 'GA4'
                property_item["id"] = item['name']
                property_item["name"] = item['displayName']
                self.property_list.append(property_item)

    def get_property_names(self, selected_account):
        if not self.property_list:
            self.set_property_list(selected_account)
        return [item['name'] for item in self.property_list]

    def set_view_list(self, selected_account, selected_property):
        self.refresh_token()
        self.view_list = []
        if self.property_list[selected_property]["type"] == "UA":
            account_id = self.account_list[selected_account]["id"]
            property_id = self.property_list[selected_property]["id"]
            uri, headers, body = self.client.add_token("https://www.googleapis.com/analytics/v3/management/accounts/"
                                                       +account_id+"/webproperties/"+property_id+"/profiles")
            userinfo_response = requests.get(uri, headers=headers, data=body)
            print(userinfo_response.status_code)
            if userinfo_response.status_code == 200:
                self.view_list = userinfo_response.json()["items"]
   
    def get_view_names(self, selected_account, selected_property):
        if not self.view_list:
            self.set_view_list(selected_account, selected_property)
        return [view['name'] for view in self.view_list]
