from flask import Flask, render_template, request, send_file, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from passlib.hash import sha256_crypt
import dotenv
import os
from binascii import hexlify
from flask_login import login_required

dotenv.load_dotenv(".env")
plt.style.use("ggplot")
secret_key = hexlify(os.urandom(24)).decode()
app = Flask(__name__)
app.secret_key = secret_key

# Google API Setup
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
client = gspread.authorize(creds)

# Admin
username = os.getenv("AUTH_USERNAME")
password = os.getenv("AUTH_PASSWORD")

login_manager = LoginManager()
login_manager.init_app(app)

users = {"admin": {"username": "admin", "password": sha256_crypt.hash("password")}}


class User(UserMixin):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_id(self):
        return self.username


@login_manager.user_loader
def load_user(username):
    if username in users:
        user_data = users.get(username)
        return User(user_data["username"], user_data["password"])
    return None


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users:
            user_data = users.get(username)
            if sha256_crypt.verify(password, user_data["password"]):
                user = User(user_data["username"], user_data["password"])
                login_user(user)
                return redirect(url_for("dashboard"))
        errormsg = "Invalid username or password"
        return render_template("login.html", error=errormsg)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login_page"))


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/chatbot", methods=["GET", "POST"])
@login_required
def chatbot():
    return render_template("chatbot.html")

@app.route("/")
def indexroot():
    return render_template("index.html")

@app.route("/data-guest", methods=["GET", "POST"])
def display_data_guest():
    if request.method == "POST":
        extras = request.args.get("extras")
        wkname = request.form["worksheetName"]
        sheet = client.open("Indian Millet Information").worksheet(wkname)
        data = sheet.get_all_records()
        keys = data[0].keys()
        if extras == None:
            extras = "URL"
        return render_template(
            "data.html", data=data, keys=keys, wkname=wkname, extras=extras
        )
    try:
        wkname = request.args.get("worksheetName")
        extras = request.args.get("extras")
        sheet = client.open("Indian Millet Information").worksheet(wkname)
        data = sheet.get_all_records()
        keys = data[0].keys()
        if extras == None:
            extras = "URL"
        return render_template(
            "data.html", data=data, keys=keys, wkname=wkname, extras=extras
        )
    except Exception as e:
        return render_template("dev.html")


@app.route("/data-admin", methods=["GET", "POST"])
@login_required
def display_data():
    if request.method == "POST":
        extras = request.args.get("extras")
        wkname = request.form["worksheetName"]
        sheet = client.open("Indian Millet Information").worksheet(wkname)
        data = sheet.get_all_records()
        keys = data[0].keys()
        if extras == None:
            extras = "URL"
        return render_template(
            "data.html", data=data, keys=keys, wkname=wkname, extras=extras
        )
    try:
        wkname = request.args.get("worksheetName")
        extras = request.args.get("extras")
        sheet = client.open("Indian Millet Information").worksheet(wkname)
        data = sheet.get_all_records()
        keys = data[0].keys()
        if extras == None:
            extras = "URL"
        return render_template(
            "data.html", data=data, keys=keys, wkname=wkname, extras=extras
        )
    except Exception as e:
        return render_template("dev.html")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_data():
    if request.method == "POST":
        wkname = request.form["worksheetName"]
        sheet = client.open("Indian Millet Information").worksheet(wkname)
        data = sheet.get_all_records()
        keys = data[0].keys()
        new_row = []
        for key in keys:
            new_row.append(request.form[key])
        sheet.append_row(new_row)
        data = sheet.get_all_records()
        keys = data[0].keys()
        return render_template("data.html", data=data, keys=keys, wkname=wkname)
    wkname = request.args.get("worksheetName")
    sheet = client.open("Indian Millet Information").worksheet(wkname)
    data = sheet.get_all_records()
    keys = data[0].keys()
    return render_template(
        "add.html", wkname=wkname, data=data, keys=keys, next=len(data) + 1
    )


@app.route("/update", methods=["GET", "POST"])
@login_required
def update_data():
    if request.method == "POST":
        wkname = request.form["worksheetName"]
        sheet = client.open("Indian Millet Information").worksheet(wkname)
        data = sheet.get_all_records()
        keys = data[0].keys()
        col = 1
        row = sheet.find(request.form["S.No."]).row
        for key in keys:
            sheet.update_cell(row, col, request.form[key])
            col = col + 1
        data = sheet.get_all_records()
        keys = data[0].keys()
        return render_template("data.html", data=data, keys=keys, wkname=wkname)
    wkname = request.args.get("worksheetName")
    index = int(request.args.get("rowIndex"))
    sheet = client.open("Indian Millet Information").worksheet(wkname)
    data = sheet.get_all_records()
    keys = data[0].keys()
    known = []
    known.append(index)
    for key in keys:
        known.append(data[index - 1][key])
    return render_template(
        "update.html", wkname=wkname, data=data, keys=keys, known=known
    )


@app.route("/image/", methods=["GET"])
def imageshow():
    fig, _ = plt.subplots(figsize=(19.2, 10.8))
    wkname = request.args.get("wkname")
    sheet = client.open("Indian Millet Information").worksheet(wkname)
    data = sheet.get_all_records()
    df = pd.DataFrame.from_dict(data)
    districts = df["District"]
    production = df["Production 2019-20 (Tonnes) Ragi"]
    plt.bar(districts, production)
    plt.xlabel("Districts")
    plt.ylabel("Production 2019-20 (Tonnes) Ragi")
    plt.title("Test Plot for " + wkname)
    plt.xticks(rotation=90)
    canvas = FigureCanvas(fig)
    img = BytesIO()
    fig.savefig(img)
    img.seek(0)
    return send_file(img, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
