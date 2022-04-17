import os

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_SCOPE = ["https://www.googleapis.com/auth/analytics.readonly", "openid", "email", "profile"]
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

