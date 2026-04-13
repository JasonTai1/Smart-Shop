# Import Flask and required functions
from flask import Flask, render_template, request, redirect, session

# Import SQLite for database
import sqlite3

# Create Flask app
app = Flask(__name__)

# Secret key for session (required for login system)
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


# Home route (redirect to login page)
@app.route("/")
def home():
    return redirect("/login")   # Redirect user to login page


# Register route
@app.route("/register", methods=["GET", "POST"])
def register():

    # Initialize error message
    error = None

    # If form is submitted
    if request.method == "POST":

        # Get data from form
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        location = request.form["location"]

        # Connect to database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = cursor.fetchone()

        # If email already registered
        if existing_user:
            error = "Email already registered"
            conn.close()
            return render_template("register.html", error=error)

        # Check password length
        if len(password) < 6:
            error = "Password must be at least 6 characters"
            conn.close()
            return render_template("register.html", error=error)

        # Insert new user into database
        cursor.execute(
            "INSERT INTO users (username, email, password, role, location) VALUES (?, ?, ?, ?, ?)",
            (username, email, password, role, location)
        )

        # Save changes
        conn.commit()

        # Close database
        conn.close()

        # Redirect to login page after register
        return redirect("/login")

    # Show register page
    return render_template("register.html", error=error)


# Login route
@app.route("/login", methods=["GET", "POST"])
def login():

    # Initialize error message
    error = None

    # If form submitted
    if request.method == "POST":

        # Get form data
        email = request.form["email"]
        password = request.form["password"]

        # Connect database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Check if email exists
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        # Close database
        conn.close()

        # If email not found
        if user is None:
            error = "User not registered"

        # If password incorrect
        elif user[3] != password:
            error = "Wrong password"

        else:
            # Save user data in session
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["email"] = user[2]
            session["role"] = user[4]
            session["location"] = user[5]

            # Redirect to profile page
            return redirect("/profile")

    # Show login page
    return render_template("login.html", error=error)


# Profile page
@app.route("/profile")
def profile():

    # If user not logged in
    if "user_id" not in session:
        return redirect("/login")

    # Show user info
    return render_template(
        "profile.html",
        username=session["username"],
        email=session["email"],
        role=session["role"],
        location=session["location"]
    )


# Logout route
@app.route("/logout")
def logout():

    # Clear all session data
    session.clear()

    # Redirect to login page
    return redirect("/login")


# Run app
if __name__ == "__main__":
    init_db()              # Initialize database
    app.run(debug=True)   # Run Flask app in debug mode