from flask import Flask, render_template, request, redirect, url_for,jsonify, session
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin import firestore
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__, template_folder='templates')
app.secret_key = "MY_secret_key_is_a_secret"
socketio = SocketIO(app)

cred = credentials.Certificate('C:\\Users\\91934\\Desktop\\Python-Live-Chat-App-main\\flaskchatapplication-firebase-adminsdk-xgstb-a02b020936.json')
firebase_admin.initialize_app(cred)

firebase_auth = auth
@app.route("/", methods=["GET"])
def splash():
    return render_template("splash.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if len(password) < 8:
            error_message = "Password is incorrect or username is incorrect"
            return render_template("login.html", error_message=error_message)

        try:
            user = auth.get_user_by_email(email)  

            user = auth.update_user(
                user.uid,
                password=password
            )

            session["user_email"] = email  

            return redirect(url_for("home"))

        except auth.AuthError as e:
            error_message = str(e)
            return render_template("login.html", error_message=error_message)

    return render_template("login.html")




@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            user = firebase_auth.create_user(email=email, password=password)
            session["user_email"] = email  
            return redirect(url_for("home"))
        except Exception as e:
            error_message = str(e)
            return render_template("signup.html", error_message=error_message)

    return render_template("signup.html")



rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code
@app.route("/home", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["message"],
        "type": data["type"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['message']}")

@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")



if __name__ == "__main__":
    socketio.run(app, debug=True)

