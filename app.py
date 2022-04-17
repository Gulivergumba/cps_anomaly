#!/usr/bin/env python3

# Load python libraries
import json

# Internal imports
from user import User
from detection_config import dc
import ga_loader

import google_config as gc

# Load all the flask stuff
from flask import Flask, session, request, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SelectField
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient

# Create the app
app = Flask(__name__)
app.config['SECRET_KEY'] = gc.FLASK_SECRET_KEY
Bootstrap(app)

# OAuth2 client setup
client = WebApplicationClient(gc.GOOGLE_CLIENT_ID)

# Flask login management
login_manager = LoginManager()
login_manager.init_app(app)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# Text to be shown if unauthorized and 403 HTML response
@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


# Class for the selection fields
class Form(FlaskForm):
    select = SelectField('', choices=[], render_kw={"onchange": "this.form.submit()"})


@app.route('/', methods=['GET', 'POST'])
def select():
    current_user = 0  # TODO: replace in login function
    my_user = User.get(current_user)
    my_ga_user = ga_loader.ga_user(token=json.loads(my_user.code))

    if "submit" in request.form:
        # TODO: Rename dc (detection_config)
        dc.add_config(current_user,
                      session['selected_account_id'],
                      session['selected_property_id'],
                      session['selected_view_id'])
        return redirect(url_for("success"))

    selection = request.form.getlist('select')
    selected_account_name = selection[0] if selection else ''
    selected_property_name = selection[1] if selection else ''
    selected_view_name = selection[2] if len(selection) > 2 else ''

    # Set account options and define defaults
    account_form = Form()
    account_names = my_ga_user.get_account_names()
    account_form.select.choices = account_names
    selected_account_id = account_names.index(selected_account_name) if selected_account_name in account_names else 0
    account_form.select.default = account_form.select.choices[selected_account_id]
    account_form.process()
    session['account_id'] = selected_account_id

    # Set property options and define defaults
    property_form = Form()
    property_names = my_ga_user.get_property_names(selected_account_id)
    property_form.select.choices = property_names
    selected_property_id = property_names.index(selected_property_name) if selected_property_name in property_names else 0
    property_form.select.default = property_form.select.choices[selected_property_id]
    property_form.process()
    session['selected_property_id'] = selected_property_id

    # Set view options and define defaults
    view_form = Form()
    view_names = my_ga_user.get_view_names(selected_account_id, selected_property_id)
    selected_view_id = view_names.index(selected_view_name) if selected_view_name in view_names else 0
    view_form.select.choices = view_names
    view_form.select.default = view_form.select.choices[selected_view_id]
    view_form.process()
    session['selected_view_id'] = selected_view_id

    return render_template('select.html', account_form=account_form, property_form=property_form, view_form=view_form)


@app.route("/success")
def success():

    current_user = 0  # replace in login function
    my_user = User.get(current_user)  # Security risk?

    my_ga_user = ga_loader.ga_user(token=json.loads(my_user.code))
    config_list = dc.get_config(current_user)

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
    google_provider_cfg = gc.get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=gc.GOOGLE_SCOPE,
        access_type="offline",
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    my_ga_user = ga_loader.ga_user(code=code)
    email = my_ga_user.get_email()

    # Write user to database:
    user = User(User.update(my_ga_user.token, email), my_ga_user.token, email)

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
