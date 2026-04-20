from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# Database setup
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

# Home → redirect to login
@app.route("/")
def home():
    return redirect("/login")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        location = request.form["location"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Check duplicate email
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        if cursor.fetchone():
            error = "Email already registered"
            conn.close()
            return render_template("register.html", error=error)

        # Password validation
        if len(password) < 6:
            error = "Password must be at least 6 characters"
            conn.close()
            return render_template("register.html", error=error)

        # Insert user
        cursor.execute(
            "INSERT INTO users (username, email, password, role, location) VALUES (?, ?, ?, ?, ?)",
            (username, email, password, role, location)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html", error=error)

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user is None:
            error = "User not registered"

        elif user[3] != password:
            error = "Wrong password"

        else:
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["email"] = user[2]
            session["role"] = user[4]
            session["location"] = user[5]

            # Role redirect
            if user[4] == "seller":
                return redirect("/seller_dashboard")
            else:
                return redirect("/buyer_dashboard")

    return render_template("login.html", error=error)

# Profile
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("profile.html",
        username=session["username"],
        email=session["email"],
        role=session["role"],
        location=session["location"]
    )

# Seller Dashboard
@app.route("/seller_dashboard")
def seller_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("seller.html")

# Buyer Dashboard
@app.route("/buyer_dashboard")
def buyer_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("buyer.html")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Run
if __name__ == "__main__":
    init_db()
    app.run(debug=True)