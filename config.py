import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'mysql+pymysql://root:zoo12345@localhost:3306/flask_app')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'signatures')
    FORM_FOLDER = os.path.join(BASE_DIR, 'uploads', 'forms')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Microsoft Entra ID settings
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    AUTHORITY = os.getenv('AUTHORITY')
    SCOPE = os.getenv('SCOPE', '').split()
    REDIRECT_URI = os.getenv('REDIRECT_URI')
