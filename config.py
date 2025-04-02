import os

class Config:
    # Flask settings
    AUTHORITY = os.getenv("AUTHORITY")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    SCOPE = ["User.Read"]
    SESSION_TYPE = "filesystem"
    SECRET_KEY = os.getenv("SECRET_KEY")
    UPLOAD_FOLDER = 'uploads/signatures'
    FORM_FOLDER = 'uploads/forms'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
