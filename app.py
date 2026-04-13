from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# Database
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT,
        role TEXT,
        location TEXT
    )
    """)

    conn.commit()
    conn.close()

# Home go login
@app.route("/")
def home():
    return redirect("/login")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        location = request.form["location"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, email, password, role, location) VALUES (?, ?, ?, ?, ?)",
            (username, email, password, role, location)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# login 
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # check email first 
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        conn.close()

        if user is None:
            error = "User not registered"

        elif user[3] != password:
            error = "Wrong password"

        else:
            session["user_id"] = user[0]
            session["email"] = user[2]
            session["role"] = user[4]

            return redirect("/profile")

    return render_template("login.html", error=error)

# Profile
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("profile.html", email=session["email"], role=session["role"])

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Run
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
