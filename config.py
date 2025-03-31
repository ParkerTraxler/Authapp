import os

class Config:
    AUTHORITY = os.getenv("AUTHORITY")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    SCOPE = ["User.Read"]
    SESSION_TYPE = "filesystem"
    SECRET_KEY = os.getenv("SECRET_KEY")