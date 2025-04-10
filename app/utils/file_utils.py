import os
from flask import current_app

def create_upload_folders(form_folder, upload_folder):
    os.makedirs(form_folder, exist_ok=True)
    os.makedirs(upload_folder, exist_ok=True)