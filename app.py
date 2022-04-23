#!/usr/bin/env python3

# Load python libraries
import json

# Internal imports
from anomaly_user import AnomalyUser
from detection_config import AnomalyConfig
from google_analytics_user import GoogleAnalyticsUser
import google_analytics_config as ga

# Load all the flask stuff
from flask import Flask, session, request, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SelectField
from flask_login import LoginManager, login_required, login_user, logout_user

from oauthlib.oauth2 import WebApplicationClient

# Create the app
app = Flask(__name__)
app.config['SECRET_KEY'] = ga.flask_secret_key
Bootstrap(app)

# OAuth2 client setup
client = WebApplicationClient(ga.google_client_id)

# Flask login management
login_manager = LoginManager()
login_manager.init_app(app)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return AnomalyUser.get(user_id)


# Text to be shown if unauthorized and 403 HTML response
@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


# Class for the selection fields
class SelectForm(FlaskForm):
    select = SelectField('', choices=[], render_kw={"onchange": "this.form.submit()"})


@app.route('/', methods=['GET', 'POST'])
def select():
    current_user = 0  # TODO: replace in login function
    my_user = AnomalyUser.get(current_user)
    my_ga_user = GoogleAnalyticsUser(token=json.loads(my_user.code))

    if "submit" in request.form:
        # TODO: Rename dc (detection_config)
        AnomalyConfig.add_config(current_user,
                                 session['account_id'],
                                 session['property_id'],
                                 session['view_id'])
        return redirect(url_for("success"))

    selection = request.form.getlist('select')
    account_name = selection[0] if selection else ''
    property_name = selection[1] if selection else ''
    view_name = selection[2] if len(selection) > 2 else ''

    # Set account options and define defaults
    account_form = SelectForm()
    account_name_list = my_ga_user.get_account_names()
    account_form.select.choices = account_name_list
    account_id = account_name_list.index(account_name) if account_name in account_name_list else 0
    account_form.select.default = account_form.select.choices[account_id]
    account_form.process()
    session['account_id'] = account_id

    # Set property options and define defaults
    property_form = SelectForm()
    property_name_list = my_ga_user.get_property_names(account_id)
    property_form.select.choices = property_name_list
    property_id = property_name_list.index(property_name) if property_name in property_name_list else 0
    property_form.select.default = property_form.select.choices[property_id]
    property_form.process()
    session['property_id'] = property_id

    # Set view options and define defaults
    view_form = SelectForm()
    view_name_list = my_ga_user.get_view_names(account_id, property_id)
    view_form.select.choices = view_name_list
    view_id = view_name_list.index(view_name) if view_name in view_name_list else 0
    if view_name_list:
        view_form.select.default = view_form.select.choices[view_id]
    view_form.process()
    session['view_id'] = view_id

    return render_template('select.html', account_form=account_form, property_form=property_form, view_form=view_form)


@app.route("/success")
def success():
    current_user = 0  # replace in login function
    my_user = AnomalyUser.get(current_user)  # Security risk?

    my_ga_user = GoogleAnalyticsUser(token=json.loads(my_user.code))
    config_list = AnomalyConfig.get_config(current_user)

    data = []
    for account_id, property_id, view_id in config_list:
        account_name = my_ga_user.get_account_names()[account_id]
        property_name = my_ga_user.get_property_names(account_id)[property_id]
        view_name_list = my_ga_user.get_view_names(account_id, property_id)
        view_name = view_name_list[view_id] if view_name_list else ""
        data.append((account_name, property_name, view_name))

    return render_template('success.html', data=data)


@app.route("/home", methods=['GET', 'POST'])
def home():
    return render_template('home.html')


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = ga.get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    # noinspection PyNoneFunctionAssignment
    request_uri = client.prepare_request_uri(
        uri=authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=ga.google_access_scope,
        access_type="offline",
    )

    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    google_analytics_user = GoogleAnalyticsUser(code=code)
    email = google_analytics_user.get_email()

    # Write user to database:
    user = AnomalyUser(AnomalyUser.replace(google_analytics_user.token, email), google_analytics_user.token, email)

    # TODO: very the user exists and login was completed
    # Begin user session by logging the user in
    login_user(user)

    return redirect(url_for("select"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(ssl_context="adhoc", host="127.0.0.1", debug=True)
