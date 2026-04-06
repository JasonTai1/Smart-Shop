import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Welcome to Smart Shop"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
         )

        conn.commit()
        conn.close()

        return "Register Success!"

    return render_template("register.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

