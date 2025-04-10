import os

class Config:
    # MSAL settings
    AUTHORITY = os.getenv("AUTHORITY")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    SCOPE = ["User.Read"]
    SESSION_TYPE = "filesystem"
    SECRET_KEY = os.getenv("SECRET_KEY")

    # PDF/Form settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'signatures')
    FORM_FOLDER = os.path.join(BASE_DIR, 'uploads', 'forms')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
