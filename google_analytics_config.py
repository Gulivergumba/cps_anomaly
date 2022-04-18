import os
import requests

google_client_id = os.environ.get("GOOGLE_CLIENT_ID", None)
google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", None)
google_access_scope = ["https://www.googleapis.com/auth/analytics.readonly", "openid", "email", "profile"]
google_discovery_url = "https://accounts.google.com/.well-known/openid-configuration"

google_analytics_3_base_url = "https://www.googleapis.com/analytics/v3/management/accounts/"
google_analytics_4_base_url = "https://analyticsadmin.googleapis.com/v1alpha"

flask_secret_key = os.environ.get("FLASK_SECRET_KEY")


def get_google_provider_cfg():
    return requests.get(google_discovery_url).json()
