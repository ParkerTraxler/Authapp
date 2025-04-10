from msal import ConfidentialClientApplication
from flask import current_app

def get_msal_app():
    return ConfidentialClientApplication(
        current_app.config['CLIENT_ID'],
        client_credential=current_app.config['CLIENT_SECRET'],
        authority=current_app.config['AUTHORITY']
    )