from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

online_users = {}

def db():
    if not os.path.exists("users.db"):
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        cur.execute("CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)")
        cur.execute("INSERT INTO users(username,password) VALUES('user1','123')")
        cur.execute("INSERT INTO users(username,password) VALUES('user2','123')")
        con.commit()
        con.close()
    return sqlite3.connect("users.db")

@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["password"]

        con=db()
        cur=con.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
        user=cur.fetchone()
        con.close()

        if user:
            session["user"]=username
            return redirect("/home")

    return render_template("login.html")

@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")
    con=db()
    cur=con.cursor()
    cur.execute("SELECT username FROM users")
    users=cur.fetchall()
    con.close()
    return render_template("home.html", users=users)

@app.route("/chat/<user>")
def chat(user):
    return render_template("chat.html", user=user)

@socketio.on("connect")
def connect():
    username=session.get("user")
    if username:
        online_users[username]=request.sid

@socketio.on("message")
def message(data):
    to=data["to"]
    msg=data["msg"]
    if to in online_users:
        emit("message", {"user":session["user"],"msg":msg}, room=online_users[to])

# Render port
if __name__ == "__main__":
    port=int(os.environ.get("PORT",10000))
    socketio.run(app, host="0.0.0.0", port=port)