# Load external python libraries
import json as js
from datetime import datetime, timezone
from oauthlib.oauth2 import WebApplicationClient
from flask import request as flask_request
import requests as http_request
# Load internal python libraries
from anomaly_user import AnomalyUser
import google_analytics_config as ga_config


class GoogleAnalyticsUser:

    def __init__(self, code=None, token=None):
        # Get the Google URL to hit to get tokens
        self.google_provider_cfg = ga_config.get_google_provider_cfg()
        self.client = WebApplicationClient(ga_config.google_client_id)
        # Email, code and token for Google Analytics access
        self.email = None
        self.code = code
        self.token = token
        if token is None:
            self.set_token()
        self.refresh_token()
        self.client.parse_request_body_response(js.dumps(self.token))
        # Only attempt to set self.email after tokens exist and are refreshed
        self.set_email()
        # Accounts and properties associated with current Google Analytics account
        self.account_list = []
        self.property_list = []
        self.view_list = []

    def set_email(self):
        uri, headers, body = self.client.add_token(uri=self.google_provider_cfg["userinfo_endpoint"])
        userinfo_response = http_request.get(url=uri, headers=headers, data=body)
        if userinfo_response.status_code == 200:
            self.email = userinfo_response.json()["email"]
        else:
            self.email = None

    def get_email(self):
        if not self.email:
            self.set_email()
        return self.email

    def set_token(self):
        # Prepare request to get token
        url, headers, body = self.client.prepare_token_request(
            token_url=self.google_provider_cfg["token_endpoint"],
            authorization_response=flask_request.url,
            redirect_url=flask_request.base_url,
            code=self.code,
        )
        # Send request to get token
        token_response = http_request.post(
            url=url,
            headers=headers,
            data=body,
            auth=(ga_config.google_client_id, ga_config.google_client_secret),
        )
        # Set token
        self.token = token_response.json()
        self.token["issue_time"] = datetime.now().timestamp()
        # Add token to client
        self.client.parse_request_body_response(js.dumps(token_response.json()))
        # Update token for anomaly user in database
        AnomalyUser.replace(self.token, self.get_email())

    def refresh_token(self):
        # Get current time and token expiration time
        time_expires = self.token['issue_time'] + self.token['expires_in']
        time_now = datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()
        # If token expired then get a new token
        if time_expires < time_now - 100:
            # Prepare request to get token
            url, headers, body = self.client.prepare_refresh_token_request(
                token_url=self.google_provider_cfg["token_endpoint"],
                refresh_token=self.token['refresh_token'],
                scope=self.token['scope'],
            )
            # Send request to get token
            token_response = http_request.post(
                url=url,
                headers=headers,
                data=body,
                auth=(ga_config.google_client_id, ga_config.google_client_secret),
            )   
            # Set new token and keep refresh token
            refresh_token = self.token['refresh_token']    
            self.token = token_response.json()
            self.token['refresh_token'] = refresh_token
            self.token["issue_time"] = datetime.now().timestamp()
            # Add token to client
            self.client.parse_request_body_response(js.dumps(token_response.json()))
            # Update token for anomaly user in database
            AnomalyUser.replace(self.token, self.get_email())

    def set_account_list(self):
        self.refresh_token()
        uri, headers, body = self.client.add_token(ga_config.google_analytics_3_base_url)
        userinfo_response = http_request.get(uri, headers=headers, data=body)
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
        # noinspection PyTypeChecker
        account_id = self.account_list[selected_account]["id"]
        self.property_list = []

        # Check for UA properties:
        uri, headers, body = self.client.add_token(ga_config.google_analytics_3_base_url
                                                   + account_id + "/webproperties")
        userinfo_response = http_request.get(uri, headers=headers, data=body)
        if userinfo_response.status_code == 200:
            for item in userinfo_response.json()["items"]:
                property_item = {
                    "type": 'UA',
                    "id": item['id'],
                    "name": item['name']
                }
                self.property_list.append(property_item)

        # Check for GA properties:
        uri, headers, body = self.client.add_token(ga_config.google_analytics_4_base_url
                                                   + "/properties")
        payload = {'filter': 'parent:accounts/'+account_id}
        userinfo_response = http_request.get(uri, params=payload, headers=headers, data=body)
        if userinfo_response.status_code == 200:
            for item in userinfo_response.json()["properties"]:
                property_item = {
                    "type": 'GA4',
                    "id": item['name'],
                    "name": item['displayName']
                }
                self.property_list.append(property_item)

    def get_property_names(self, selected_account):
        if not self.property_list:
            self.set_property_list(selected_account)
        return [item['name'] for item in self.property_list]

    def set_view_list(self, selected_account, selected_property):
        self.refresh_token()
        self.view_list = []
        # noinspection PyTypeChecker
        if self.property_list[selected_property]["type"] == "UA":
            # noinspection PyTypeChecker
            account_id = self.account_list[selected_account]["id"]
            # noinspection PyTypeChecker
            property_id = self.property_list[selected_property]["id"]
            uri, headers, body = self.client.add_token(ga_config.google_analytics_3_base_url
                                                       + account_id + "/webproperties/"
                                                       + property_id + "/profiles")
            userinfo_response = http_request.get(uri, headers=headers, data=body)
            if userinfo_response.status_code == 200:
                self.view_list = userinfo_response.json()["items"]
   
    def get_view_names(self, selected_account, selected_property):
        if not self.view_list:
            self.set_view_list(selected_account, selected_property)
        return [view['name'] for view in self.view_list]
