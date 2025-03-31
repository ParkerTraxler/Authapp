import os
from flask import Flask, render_template, redirect, url_for, request, session
from msal import ConfidentialClientApplication
# Load environment variables
from dotenv import load_dotenv
load_dotenv()
# Import config file
import config

# Define app and load configurations
app = Flask(__name__)
app.config.from_object(config.Config)

# MSAL client
app_instance = ConfidentialClientApplication(
    app.config['CLIENT_ID'],
    client_credential=app.config['CLIENT_SECRET'],
    authority=app.config['AUTHORITY']
)

# Display name of user if logged in or redirects to /login
@app.route('/')
@app.route('/home')
def home():
    # Check if user is logged in
    logged_in = session.get('logged_in', False)

    if logged_in:
        return render_template('index.html', logged_in=logged_in, user=session['user'])
    return render_template('index.html', logged_in=logged_in)

@app.route('/login')
def login():
    auth_url = app_instance.get_authorization_request_url(app.config['SCOPE'], redirect_uri=app.config['REDIRECT_URI'])
    return redirect(auth_url)

@app.route('/get_token')
def get_token():
    if "code" in request.args:
        result = app_instance.acquire_token_by_authorization_code(
            request.args['code'], app.config['SCOPE'], redirect_uri=app.config['REDIRECT_URI']
        )
        if "access_token" in result:
            session["user"] = result.get("id_token_claims")
            return redirect(url_for("home"))
        
    return "Login failed", 401

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')

if __name__ == "__main__":
    app.run(debug=True)
