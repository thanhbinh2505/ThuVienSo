import os
from dotenv import load_dotenv

load_dotenv()

from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "k8HDLZbie2T8UWvC70S7f-SukGY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:1234@localhost/thuviensodb?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID", "")
app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET", "")
app.config["FACEBOOK_CLIENT_ID"] = os.environ.get("FACEBOOK_CLIENT_ID", "")
app.config["FACEBOOK_CLIENT_SECRET"] = os.environ.get("FACEBOOK_CLIENT_SECRET", "")

db = SQLAlchemy(app)
login = LoginManager(app=app)
login.login_view = "login_process"

oauth = OAuth(app)

oauth.register(
    name="google",
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="facebook",
    client_id=app.config["FACEBOOK_CLIENT_ID"],
    client_secret=app.config["FACEBOOK_CLIENT_SECRET"],
    access_token_url="https://graph.facebook.com/oauth/access_token",
    authorize_url="https://www.facebook.com/dialog/oauth",
    api_base_url="https://graph.facebook.com/",
    client_kwargs={"scope": "email public_profile"},
)
