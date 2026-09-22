import os
from dotenv import load_dotenv

load_dotenv()

from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "k8HDLZbie2T8UWvC70S7f-SukGY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:Admin%40123@localhost/thuviensodb?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False

app.config["MAIL_USERNAME"] = os.environ.get(
    "MAIL_USERNAME",
    ""
)
app.config["MAIL_PASSWORD"] = os.environ.get(
    "MAIL_PASSWORD",
    ""
)

app.config["MAIL_DEFAULT_SENDER"] = app.config["MAIL_USERNAME"]

app.config['TWILIO_ACCOUNT_SID'] = 'YOUR_ACCOUNT_SID'
app.config['TWILIO_AUTH_TOKEN'] = 'YOUR_AUTH_TOKEN'
app.config['TWILIO_PHONE_NUMBER'] = 'YOUR_TWILIO_PHONE_NUMBER'
app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID", "")
app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET", "")
app.config["FACEBOOK_CLIENT_ID"] = os.environ.get("FACEBOOK_CLIENT_ID", "")
app.config["FACEBOOK_CLIENT_SECRET"] = os.environ.get("FACEBOOK_CLIENT_SECRET", "")

db = SQLAlchemy(app)
mail = Mail(app)
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

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    'static',
    'images',
    'sach'
)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(
    app.config['UPLOAD_FOLDER'],
    exist_ok=True
)