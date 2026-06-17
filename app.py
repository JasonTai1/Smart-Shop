# ════════════════════════════════════════════
# app.py — Smart Shop
# ════════════════════════════════════════════

from flask import Flask, render_template, request, redirect, session
from routes.main import main 
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
# random = built-in Python library to generate random numbers
import smtplib
# smtplib = built-in Python library to send emails
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# MIMEText, MIMEMultipart = helps us build email content

import os
from werkzeug.utils import secure_filename
# secure_filename = makes filename safe to save
# Example: "my photo!.jpg" → "my_photo_.jpg"


app = Flask(__name__)
app.secret_key = "smartshop_secret_key_2024"

# ── Email Settings ──────────────────
SMTP_EMAIL    = "smartshop.noreply1234@gmail.com"
# The Gmail that SENDS the OTP

SMTP_PASSWORD = "hnusxqjfcvupcdeq"
# The App Password we just created (no spaces!)

SMTP_HOST     = "smtp.gmail.com"
# Gmail's SMTP server address

SMTP_PORT     = 587
# Port 587 = standard port for sending email securely

# Allowed image types 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# Only these file types allowed 

UPLOAD_FOLDER = 'static/uploads'
# Where uploaded images are saved 

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# MAX_CONTENT_LENGTH = maximum file size = 16MB

# ════════════════════════════════════════════
# DATABASE 
# ════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect("database.db",
        check_same_thread=False,
        timeout=10
    )
    # check_same_thread=False = allow multiple threads to use database
    # timeout=10 = wait up to 10 seconds if database is locked
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            username    TEXT NOT NULL,
            email       TEXT NOT NULL,
            password    TEXT NOT NULL,
            role        TEXT DEFAULT 'buyer',
            city        TEXT,
            state       TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(email, role)
        )
    """)
    # OTP table — stores OTP codes temporarily
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT NOT NULL,
            otp        TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Why separate table? Because OTP is temporary
    # After user verifies, we delete it

        # ── Products Tablem ──────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id   INTEGER NOT NULL,
            name        TEXT NOT NULL,
            description TEXT,
            price       REAL NOT NULL,
            stock       INTEGER DEFAULT 0,
            category    TEXT,
            image_url   TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users(id)
        )
    """)
    # id          = unique number for each product 
    # seller_id   = which seller owns this product 
    # name        = product name 
    # description = product description 
    # price       = REAL means decimal number like 9.99 
    # stock       = how many items available 
    # category    = product category
    # image_url   = link to product image 
    # FOREIGN KEY = links seller_id to users table id

    # Cart table 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id   INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity   INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_id)   REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    # buyer_id   = which buyer added this item
    # product_id = which product was added
    # quantity   = how many pieces 
    # FOREIGN KEY = links to other tables

    # Orders table 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id      INTEGER NOT NULL,
            total_amount  REAL NOT NULL,
            full_name     TEXT NOT NULL,
            phone         TEXT NOT NULL,
            address       TEXT NOT NULL,
            city          TEXT NOT NULL,
            state         TEXT NOT NULL,
            postcode      TEXT NOT NULL,
            status        TEXT DEFAULT 'pending',
            payment_proof TEXT,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_id) REFERENCES users(id)
        )
    """)
    # payment_proof = filename of uploaded screenshot
    # id           = unique order number 
    # buyer_id     = who placed the order
    # total_amount = total price 
    # full_name    = delivery name 
    # phone        = contact number 
    # address      = street address 
    # city         = delivery city 
    # state        = delivery state 
    # postcode     = postcode 
    # status       = pending/paid/shipped 
    # created_at   = when order was placed 

    # Order Items table 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity   INTEGER NOT NULL,
            price      REAL NOT NULL,
            FOREIGN KEY (order_id)   REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    # order_id   = which order this item belongs to 
    # product_id = which product
    # quantity   = how many
    # price      = price at time of order

# Seller payout info table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seller_payout (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id      INTEGER NOT NULL UNIQUE,
            tng_phone      TEXT,
            bank_name      TEXT,
            bank_account   TEXT,
            bank_holder    TEXT,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users(id)
        )
    """)
    # tng_phone    = TNG registered phone number 
    # bank_name    = bank name 
    # bank_account = account number 
    # bank_holder  = account holder name 
    conn.commit()
    conn.close()

# ════════════════════════════════════════════
# OTP FUNCTIONS 
# ════════════════════════════════════════════

def generate_otp():
    # Generate a random 6-digit number
    otp = random.randint(100000, 999999)
    # random.randint(min, max) = random number between min and max
    # Example: random.randint(100000, 999999) → 483921
    return str(otp)
    # str() = convert number to string "483921"

def send_otp_email(to_email, otp):
    # This function sends OTP email to the user
    try:
        # Build the email 
        msg = MIMEMultipart()
        # MIMEMultipart = email that can have multiple parts

        msg["From"]    = SMTP_EMAIL
        # Who is sending 

        msg["To"]      = to_email
        # Who receives 

        msg["Subject"] = "Smart Shop - Your OTP Code"
        # Email subject line 

        # Email body content 
        body = f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <div style="max-width: 400px; margin: 0 auto; 
                        border: 1px solid #ddd; border-radius: 10px; 
                        padding: 30px; text-align: center;">
                
                <h2 style="color: #800000;"> Smart Shop</h2>
                <p>Your OTP verification code is:</p>
                
                <h1 style="color: #800000; font-size: 40px; 
                           letter-spacing: 8px; background: #fff0f0;
                           padding: 15px; border-radius: 8px;">
                    {otp}
                </h1>
                
                <p style="color: #888;">
                    This code expires in <b>5 minutes</b>.<br>
                </p>
                <p style="color: #888; font-size: 12px;">
                    If you didn't request this, ignore this email.<br>
                </p>
            </div>
        </body>
        </html>
        """
        # f"..." = f-string, {otp} inserts the OTP value

        msg.attach(MIMEText(body, "html"))
        # attach = add the body to the email
        # "html" = tell email client to render as HTML

        # Connect to Gmail and send
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        # Create connection to Gmail's SMTP server

        server.starttls()
        # starttls() = upgrade to secure encrypted connection

        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        # Login to Gmail with our email and app password

        server.send_message(msg)
        # Actually send the email!

        server.quit()
        # Close the connection

        return True
        # True = email sent successfully

    except Exception as e:
        # If anything goes wrong, print error and return False
        print(f"Email error: {e}")
        return False
        # False = email failed to send

def save_otp(email, otp):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        # Delete old OTP first 
        cursor.execute("DELETE FROM otp_codes WHERE email=?", (email,))
        # Save new OTP 
        cursor.execute(
            "INSERT INTO otp_codes (email, otp) VALUES (?, ?)",
            (email, otp)
        )
        conn.commit()
        # try/except = if anything goes wrong, catch the error
    except Exception as e:
        print(f"save_otp error: {e}")
    finally:
        if conn:
            conn.close()
        # finally = ALWAYS runs, even if error happens
        # Makes sure connection is always closed!

def verify_otp(email, entered_otp):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT otp FROM otp_codes
            WHERE email=?
            AND created_at >= datetime('now', '-5 minutes')
        """, (email,))
        result = cursor.fetchone()

        if result and result["otp"] == entered_otp:
            # OTP matches! Delete it
            cursor.execute(
                "DELETE FROM otp_codes WHERE email=?",
                (email,)
            )
            conn.commit()
            return True
        return False

    except Exception as e:
        print(f"verify_otp error: {e}")
        return False
    finally:
        if conn:
            conn.close()
   
   # upload photo
def allowed_file(filename):
    # Check if file extension is allowed
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    # rsplit('.', 1) = split by dot, keep last part
    # Example: "photo.JPG" → ["photo", "JPG"]
    # [1].lower() → "jpg"
    # "jpg" in ALLOWED_EXTENSIONS → True 

# ════════════════════════════════════════════
# ROUTES 
# ════════════════════════════════════════════

@app.route("/")
def home():
    return redirect("/login")

# ── REGISTER STEP 1: Fill form  ──────
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        first_name       = request.form["first_name"].strip()
        last_name        = request.form["last_name"].strip()
        username         = request.form["username"].strip()
        email            = request.form["email"].strip().lower()
        password         = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role             = request.form["role"]
        city             = request.form.get("city", "").strip()
        state            = request.form.get("state", "").strip()

        # Validation 
        if not first_name or not last_name or not username or not email or not password:
            error = "Please fill all required fields."
            return render_template("register.html", error=error)

        # Check if email has valid format 
        # Must have @ and a dot after @ 
        if "@" not in email or "." not in email.split("@")[-1]:
            error = "Please enter a valid email address. "
            return render_template("register.html", error=error)
        # This allows ALL emails! 
        # gmail.com ✅
        # icloud.com ✅
        # yahoo.com ✅
        # hotmail.com ✅
        # student.edu.my ✅
        # anything@anything.com ✅

        if len(password) < 6:
            error = "Password must be at least 6 characters."
            return render_template("register.html", error=error)

        if password != confirm_password:
            error = "Passwords do not match."
            return render_template("register.html", error=error)

      # Check if same email + same role already exists
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE email=? AND role=?",
            (email, role)
        )
        # Now we check BOTH email AND role
        # Same email + different role = ALLOWED!
        # Same email + same role = NOT allowed!

        if cursor.fetchone():
            error = f"This email is already registered as a {role}."
            conn.close()
            return render_template("register.html", error=error)
        conn.close()

        # Save form data in session temporarily
        # We don't create account yet — wait for OTP first!
        session["pending_user"] = {
            "first_name": first_name,
            "last_name":  last_name,
            "username":   username,
            "email":      email,
            "password":   generate_password_hash(password),
            "role":       role,
            "city":       city,
            "state":      state
        }
        # "pending_user" = user waiting to be verified

        # Generate and send OTP
        otp = generate_otp()
        save_otp(email, otp)

        success = send_otp_email(email, otp)

        if success:
            return redirect("/verify_otp")
            # Go to OTP verification page
        else:
            error = "Failed to send OTP. Please try again."
            return render_template("register.html", error=error)

    return render_template("register.html", error=error)

# ── REGISTER STEP 2: Verify OTP  ──────
@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp_page():

    if "pending_user" not in session:
        return redirect("/register")

    error   = None
    success = None
    # success = message to show when something good happens
    email   = session["pending_user"]["email"]

    if request.method == "POST":
        entered_otp = request.form["otp"].strip()

        if verify_otp(email, entered_otp):
            # ✅ OTP CORRECT! Create account now
            user = session["pending_user"]

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users
                    (first_name, last_name, username, email, password, role, city, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user["first_name"], user["last_name"],
                user["username"],   user["email"],
                user["password"],   user["role"],
                user["city"],       user["state"]
            ))
            conn.commit()
            conn.close()

            session.pop("pending_user", None)

            # Save a success message in session
            session["flash"] = "🎉 Account created successfully! Please login."

            return redirect("/login")

        else:
            # ❌ OTP WRONG or expired
            error = "Wrong or expired OTP. Please try again. "

    return render_template("verify_otp.html",
        email=email,
        error=error,
        success=success
    )

# ── RESEND OTP  ───────────────────
@app.route("/resend_otp")
def resend_otp():
    if "pending_user" not in session:
        return redirect("/register")

    email = session["pending_user"]["email"]
    otp   = generate_otp()
    save_otp(email, otp)
    send_otp_email(email, otp)

    return redirect("/verify_otp")

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email    = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        # Get ALL accounts with this email
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        users_found = cursor.fetchall()
        # fetchall() = get ALL matching rows (not just one)
        conn.close()

        if not users_found:
            # No account found 
            error = "Email not registered.。"

        else:
            # Check password using first account found
            if not check_password_hash(users_found[0]["password"], password):
                error = "Wrong password."

            elif len(users_found) == 2:
                # This email has BOTH buyer and seller accounts!
                # Ask user which role to login as
                session["pending_login_email"] = email
                return redirect("/choose_role")
                # We go to a new page to choose role

            else:
                # Only one account, login directly
                user = users_found[0]
                session["user_id"]    = user["id"]
                session["first_name"] = user["first_name"]
                session["last_name"]  = user["last_name"]
                session["username"]   = user["username"]
                session["email"]      = user["email"]
                session["role"]       = user["role"]
                session["city"]       = user["city"]
                session["state"]      = user["state"]
                session["created_at"] = user["created_at"]

                if user["role"] == "seller":
                    return redirect("/seller_dashboard")
                else:
                    return redirect("/buyer_dashboard")

    return render_template("login.html", error=error)

# ── CHOOSE ROLE PAGE  ─────────────
# This page shows when user has BOTH buyer and seller accounts
@app.route("/choose_role", methods=["GET", "POST"])
def choose_role():

    if "pending_login_email" not in session:
        return redirect("/login")

    if request.method == "POST":
        chosen_role = request.form["role"]
        # Get the role the user clicked

        email = session["pending_login_email"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email=? AND role=?",
            (email, chosen_role)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            # Save chosen role's account in session
            session.pop("pending_login_email", None)
            session["user_id"]    = user["id"]
            session["first_name"] = user["first_name"]
            session["last_name"]  = user["last_name"]
            session["username"]   = user["username"]
            session["email"]      = user["email"]
            session["role"]       = user["role"]
            session["city"]       = user["city"]
            session["state"]      = user["state"]
            session["created_at"] = user["created_at"]

            if chosen_role == "seller":
                return redirect("/seller_dashboard")
            else:
                return redirect("/buyer_dashboard")

    return render_template("choose_role.html")

# ── PROFILE ──────────────────────────
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("profile.html",
        first_name = session["first_name"],
        last_name  = session["last_name"],
        username   = session["username"],
        email      = session["email"],
        role       = session["role"],
        city       = session.get("city", ""),
        state      = session.get("state", ""),
        created_at = session.get("created_at", "")
    )

# ════════════════════════════════════════════
# SELLER SYSTEM 
# ════════════════════════════════════════════

# ── SELLER DASHBOARD  ──────────────
@app.route("/seller_dashboard")
def seller_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "seller":
        return redirect("/buyer_dashboard")

    # Get all products belonging to this seller
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM products
        WHERE seller_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],))
    # WHERE seller_id = ? = only get THIS seller's products
    # ORDER BY created_at DESC = newest first 
    products = cursor.fetchall()
    conn.close()

    return render_template("seller_dashboard.html",
        first_name = session["first_name"],
        products   = products
    )

# ── ADD PRODUCT  ──────────────────────
@app.route("/seller/add_product", methods=["GET", "POST"])
def add_product():
    if "user_id" not in session or session["role"] != "seller":
        return redirect("/login")

    error   = None
    success = None

    if request.method == "POST":
        name        = request.form["name"].strip()
        description = request.form["description"].strip()
        price       = request.form["price"]
        stock       = request.form["stock"]
        category    = request.form["category"].strip()

        # Handle image upload 
        image_path = None
        # image_path = where we save the image path

        if 'image' in request.files:
            # request.files = contains uploaded files
            file = request.files['image']

            if file and file.filename != '':
                # file.filename != '' = user actually selected a file

                if allowed_file(file.filename):
                    # Make filename safe 
                    filename = secure_filename(file.filename)

                    # Add unique number to avoid same filename conflicts
                    import time
                    filename = str(int(time.time())) + "_" + filename
                    # time.time() = current timestamp e.g. 1714900000
                    # Result: "1714900000_nike_shoes.jpg"

                    # Save file to uploads folder
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    # os.path.join = combines folder + filename
                    # Result: "static/uploads/1714900000_nike_shoes.jpg"

                    image_path = 'uploads/' + filename
                    # We save relative path (without 'static/')
                    # Because Flask's url_for('static') already adds it
                else:
                    error = "Only images allowed (PNG, JPG, GIF, WEBP). "
                    return render_template("add_product.html", error=error, success=success)

        # Validation 
        if not name or not price or not stock:
            error = "Please fill all required fields."
        else:
            try:
                price = float(price)
                stock = int(stock)

                if price <= 0:
                    error = "Price must be more than 0."
                elif stock < 0:
                    error = "Stock cannot be negative."
                else:
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO products
                            (seller_id, name, description,
                             price, stock, category, image_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session["user_id"],
                        name, description,
                        price, stock,
                        category, image_path
                        # Save image_path to database
                    ))
                    conn.commit()
                    conn.close()
                    success = f"✅ Product '{name}' added successfully!"

            except ValueError:
                error = "Price and stock must be numbers. "

    return render_template("add_product.html",
        error=error, success=success)

# ── LOGOUT  ──────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ── EDIT PRODUCT  ─────────────────────
@app.route("/seller/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    # <int:product_id> = gets ID number from URL
    # Example: /seller/edit_product/3 → product_id = 3

    if "user_id" not in session or session["role"] != "seller":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Get this product — only if it belongs to THIS seller
    cursor.execute("""
        SELECT * FROM products
        WHERE id = ? AND seller_id = ?
    """, (product_id, session["user_id"]))
    # AND seller_id = ? = security check!
    # Sellers can ONLY edit their OWN products!
    product = cursor.fetchone()
    conn.close()

    if not product:
        # Product not found or doesn't belong to this seller
        return redirect("/seller_dashboard")

    error   = None
    success = None

    if request.method == "POST":
        name        = request.form["name"].strip()
        description = request.form["description"].strip()
        price       = request.form["price"]
        stock       = request.form["stock"]
        category    = request.form["category"].strip()

        # Handle new image upload 
        image_path = product["image_url"]
        # Keep old image by default

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    import time
                    filename = str(int(time.time())) + "_" + secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_path = 'uploads/' + filename
                    # New image uploaded! Replace old path
                else:
                    error = "Only images allowed."
                    return render_template("edit_product.html",
                        product=product, error=error, success=success)

        if not name or not price or not stock:
            error = "Please fill all required fields."
        else:
            try:
                price = float(price)
                stock = int(stock)

                if price <= 0:
                    error = "Price must be more than 0."
                elif stock < 0:
                    error = "Stock cannot be negative."
                else:
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE products
                        SET name=?, description=?, price=?,
                            stock=?, category=?, image_url=?
                        WHERE id=? AND seller_id=?
                    """, (
                        name, description, price,
                        stock, category, image_path,
                        product_id, session["user_id"]
                    ))
                    # UPDATE = change existing data in database
                    # SET = which columns to change 
                    # WHERE = which row to change 
                    conn.commit()
                    conn.close()
                    success = "✅ Product updated successfully!"

                    # Refresh product data to show updated values
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
                    product = cursor.fetchone()
                    conn.close()

            except ValueError:
                error = "Price and stock must be numbers."

    return render_template("edit_product.html",
        product = product,
        error   = error,
        success = success
    )


# ── DELETE PRODUCT ───────────────────
@app.route("/seller/delete_product/<int:product_id>")
def delete_product(product_id):
    if "user_id" not in session or session["role"] != "seller":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM products
        WHERE id = ? AND seller_id = ?
    """, (product_id, session["user_id"]))
    # DELETE = remove a row from database
    # WHERE id=? AND seller_id=? = security check!
    # Only delete if product belongs to THIS seller
    conn.commit()
    conn.close()

    return redirect("/seller_dashboard")

# ════════════════════════════════════════════
# SHOPPING CART 
# ════════════════════════════════════════════

# ── BUYER HOME — Show all products ──
@app.route("/buyer_dashboard")
def buyer_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    # Get ALL products from ALL sellers
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT products.*, users.username as seller_name
        FROM products
        JOIN users ON products.seller_id = users.id
        WHERE products.stock > 0
        ORDER BY products.created_at DESC
    """)
    # JOIN = combine products table with users table
    # users.username as seller_name = get seller's name
    # WHERE stock > 0 = only show products with stock
    products = cursor.fetchall()

    # Get cart count for this buyer
    cursor.execute("""
        SELECT SUM(quantity) FROM cart WHERE buyer_id = ?
    """, (session["user_id"],))
    # SUM(quantity) = add up all quantities
    result = cursor.fetchone()
    cart_count = result[0] if result[0] else 0
    # if result[0] is None (empty cart), use 0
    conn.close()

#Jason part-----------
    for alert in PRICE_ALERTS:
        p_id = alert['product_id']
        target = alert['target_price']
        
        product = PRODUCTS.get(p_id)
        if product:
            try:
                current_price_num = float(product.price.replace('RM', '').replace(',', '').strip())
                if current_price_num <= target:
                    # 以前是 print，现在换成 flash 发送给网页
                    flash(f"🚨 Price Alert：{product.name} is now {product.price}，reaching your target of RM{target}！", "warning")
            except ValueError:
                pass 


    return render_template("buyer_dashboard.html",
        first_name = session["first_name"],
        products   = products,
        cart_count = cart_count
    )

# ── ADD TO CART  ────────────────────
@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    # Only buyers can add to cart
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    quantity = int(request.form.get("quantity", 1))
    # request.form.get("quantity", 1) = get quantity, default 1

    conn = get_db()
    cursor = conn.cursor()

    # Check if product exists and has enough stock
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        return redirect("/buyer_dashboard")

    if product["stock"] < quantity:
        # Not enough stock!
        conn.close()
        return redirect("/buyer_dashboard")

    # Check if this product already in buyer's cart
    cursor.execute("""
        SELECT * FROM cart
        WHERE buyer_id=? AND product_id=?
    """, (session["user_id"], product_id))
    existing = cursor.fetchone()

    if existing:
        # Already in cart! Just increase quantity
        cursor.execute("""
            UPDATE cart
            SET quantity = quantity + ?
            WHERE buyer_id=? AND product_id=?
        """, (quantity, session["user_id"], product_id))
        # quantity + ? = add to existing quantity
    else:
        # Not in cart yet, add new item
        cursor.execute("""
            INSERT INTO cart (buyer_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (session["user_id"], product_id, quantity))

    conn.commit()
    conn.close()

    return redirect("/cart")
    # After adding, go to cart page

# ── VIEW CART  ──────────────────────
@app.route("/cart")
def view_cart():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    conn = get_db()
    cursor = conn.cursor()

    # Get all cart items with product details
    cursor.execute("""
        SELECT
            cart.id        as cart_id,
            cart.quantity,
            products.id    as product_id,
            products.name,
            products.price,
            products.image_url,
            products.stock,
            products.price * cart.quantity as subtotal
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.buyer_id = ?
        ORDER BY cart.created_at DESC
    """, (session["user_id"],))
    # products.price * cart.quantity as subtotal
    # = price × quantity = subtotal for each item
    items = cursor.fetchall()

    # Calculate total price 
    total = sum(item["subtotal"] for item in items)
    # sum() = adds up all subtotals

    conn.close()

    return render_template("cart.html",
        items      = items,
        total      = total,
        first_name = session["first_name"]
    )

# ── UPDATE CART QUANTITY ─────────
@app.route("/cart/update/<int:cart_id>", methods=["POST"])
def update_cart(cart_id):
    if "user_id" not in session:
        return redirect("/login")

    quantity = int(request.form.get("quantity", 1))

    if quantity < 1:
        # If quantity less than 1, remove item
        return redirect(f"/cart/remove/{cart_id}")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cart SET quantity=?
        WHERE id=? AND buyer_id=?
    """, (quantity, cart_id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect("/cart")

# ── REMOVE FROM CART ─────────────
@app.route("/cart/remove/<int:cart_id>")
def remove_from_cart(cart_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM cart
        WHERE id=? AND buyer_id=?
    """, (cart_id, session["user_id"]))
    # DELETE only if belongs to THIS buyer (security!)
    conn.commit()
    conn.close()

    return redirect("/cart")

# ════════════════════════════════════════════
# CHECKOUT SYSTEM 
# ════════════════════════════════════════════

# ── CHECKOUT PAGE  ────────────────────
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    conn = get_db()
    cursor = conn.cursor()

    # Get cart items
    cursor.execute("""
        SELECT
            cart.id        as cart_id,
            cart.quantity,
            products.id    as product_id,
            products.name,
            products.price,
            products.image_url,
            products.stock,
            products.price * cart.quantity as subtotal
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.buyer_id = ?
        ORDER BY cart.created_at DESC
    """, (session["user_id"],))
    items = cursor.fetchall()

    # If cart is empty redirect back
    if not items:
        conn.close()
        return redirect("/cart")

    # Calculate total 
    total = sum(item["subtotal"] for item in items)

    if request.method == "POST":
        # Get delivery details from form
        full_name = request.form["full_name"].strip()
        phone     = request.form["phone"].strip()
        address   = request.form["address"].strip()
        city      = request.form["city"].strip()
        state     = request.form["state"].strip()
        postcode  = request.form["postcode"].strip()

        # Validation 
        if not full_name or not phone or not address or not city or not state or not postcode:
            conn.close()
            return render_template("checkout.html",
                items=items, total=total,
                error="Please fill all delivery details. ",
                session=session
            )

        # Create order in database 
        cursor.execute("""
            INSERT INTO orders
                (buyer_id, total_amount, full_name, phone,
                 address, city, state, postcode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session["user_id"], total, full_name, phone,
              address, city, state, postcode))

        order_id = cursor.lastrowid
        # lastrowid = the ID of the row just inserted

        # Save each cart item as order item
        for item in items:
            cursor.execute("""
                INSERT INTO order_items
                    (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item["product_id"],
                  item["quantity"], item["price"]))

            # Reduce product stock 
            cursor.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
            """, (item["quantity"], item["product_id"]))
            # stock = stock - quantity

        # Clear the cart after order placed
        cursor.execute("""
            DELETE FROM cart WHERE buyer_id = ?
        """, (session["user_id"],))

        conn.commit()
        conn.close()

        # Save order_id in session for payment page
        session["last_order_id"] = order_id
        session["last_order_total"] = total

        return redirect("/payment")

    conn.close()
    return render_template("checkout.html",
        items    = items,
        total    = total,
        error    = None,
        # Pre-fill with user's saved info
        full_name = session.get("first_name","") + " " + session.get("last_name",""),
        phone     = session.get("phone", ""),
        city      = session.get("city", ""),
        state     = session.get("state", "")
    )

# ════════════════════════════════════════════
# PAYMENT SYSTEM
# ════════════════════════════════════════════

# ── PAYMENT PAGE ─────────────────────
@app.route("/payment", methods=["GET", "POST"])
def payment():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    order_id    = session.get("last_order_id")
    order_total = session.get("last_order_total")

    if not order_id:
        return redirect("/buyer_dashboard")

    error = None

    if request.method == "POST":
        # Check if proof image uploaded
        proof_path = None

        if 'payment_proof' in request.files:
            file = request.files['payment_proof']

            if file and file.filename != '':
                if allowed_file(file.filename):
                    import time
                    filename = "proof_" + str(int(time.time())) + "_" + secure_filename(file.filename)
                    # proof_ prefix = easy to identify payment proofs

                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    proof_path = 'uploads/' + filename
                else:
                    error = "Only image files allowed. "
                    return render_template("payment.html",
                        order_id=order_id, order_total=order_total, error=error)

        # Update order status and save proof
        conn = get_db()
        cursor = conn.cursor()

        if proof_path:
            # With proof
            cursor.execute("""
                UPDATE orders
                SET status = 'payment_pending',
                    payment_proof = ?
                WHERE id = ? AND buyer_id = ?
            """, (proof_path, order_id, session["user_id"]))
        else:
            # Without proof (still allowed)
            cursor.execute("""
                UPDATE orders
                SET status = 'payment_pending'
                WHERE id = ? AND buyer_id = ?
            """, (order_id, session["user_id"]))

        conn.commit()
        conn.close()

        session.pop("last_order_id", None)
        session.pop("last_order_total", None)

        return redirect("/payment_success")

    # Check if TNG QR exists 
    tng_qr_exists = os.path.exists('static/images/tng_qr.png')

    return render_template("payment.html",
        order_id      = order_id,
        order_total   = order_total,
        error         = error,
        tng_qr_exists = tng_qr_exists
    )

# ── PAYMENT SUCCESS PAGE  ────────────
@app.route("/payment_success")
def payment_success():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("payment_success.html",
        first_name = session["first_name"]
    )

# ════════════════════════════════════════════
# SELLER PAYOUT SETUP 
# ════════════════════════════════════════════

# ── SELLER PAYOUT SETTINGS  ─────────
@app.route("/seller/payout", methods=["GET", "POST"])
def seller_payout():
    if "user_id" not in session or session["role"] != "seller":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Get existing payout info
    cursor.execute("""
        SELECT * FROM seller_payout WHERE seller_id = ?
    """, (session["user_id"],))
    payout_info = cursor.fetchone()

    error   = None
    success = None

    if request.method == "POST":
        tng_phone    = request.form.get("tng_phone", "").strip()
        bank_name    = request.form.get("bank_name", "").strip()
        bank_account = request.form.get("bank_account", "").strip()
        bank_holder  = request.form.get("bank_holder", "").strip()

        # Must have at least one payment method
        if not tng_phone and not bank_account:
            error = "Please fill in at least one payment method."
        else:
            if payout_info:
                # Update existing 
                cursor.execute("""
                    UPDATE seller_payout
                    SET tng_phone=?, bank_name=?,
                        bank_account=?, bank_holder=?
                    WHERE seller_id=?
                """, (tng_phone, bank_name,
                      bank_account, bank_holder,
                      session["user_id"]))
            else:
                # Insert new 
                cursor.execute("""
                    INSERT INTO seller_payout
                        (seller_id, tng_phone, bank_name,
                         bank_account, bank_holder)
                    VALUES (?, ?, ?, ?, ?)
                """, (session["user_id"], tng_phone, bank_name,
                      bank_account, bank_holder))

            conn.commit()
            success = " Payout info saved!"

            # Refresh payout info
            cursor.execute("""
                SELECT * FROM seller_payout WHERE seller_id = ?
            """, (session["user_id"],))
            payout_info = cursor.fetchone()

    conn.close()
    return render_template("seller_payout.html",
        payout_info = payout_info,
        error       = error,
        success     = success
    )

# ── SELLER ORDERS  ──────────────────────
@app.route("/seller/orders")
def seller_orders():
    if "user_id" not in session or session["role"] != "seller":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Get all orders that contain this seller's products
    cursor.execute("""
        SELECT DISTINCT
            orders.id,
            orders.created_at,
            orders.status,
            orders.total_amount,
            orders.full_name,
            orders.phone,
            orders.address,
            orders.city,
            orders.state,
            users.email as buyer_email
        FROM orders
        JOIN order_items ON orders.id = order_items.order_id
        JOIN products    ON order_items.product_id = products.id
        JOIN users       ON orders.buyer_id = users.id
        WHERE products.seller_id = ?
        ORDER BY orders.created_at DESC
    """, (session["user_id"],))
    orders = cursor.fetchall()
    conn.close()

    return render_template("seller_orders.html",
        orders     = orders,
        first_name = session["first_name"]
    )


# ── BUYER ORDER HISTORY  ─────────────
@app.route("/buyer/orders")
def buyer_orders():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    conn = get_db()
    cursor = conn.cursor()

    # Get all orders by this buyer
    cursor.execute("""
        SELECT * FROM orders
        WHERE buyer_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],))
    orders = cursor.fetchall()

    # For each order, get the items
    orders_with_items = []
    for order in orders:
        cursor.execute("""
            SELECT
                order_items.*,
                products.name,
                products.image_url
            FROM order_items
            JOIN products ON order_items.product_id = products.id
            WHERE order_items.order_id = ?
        """, (order["id"],))
        items = cursor.fetchall()
        orders_with_items.append({
            "order": order,
            "items": items
        })

    conn.close()

    return render_template("buyer_orders.html",
        orders_with_items = orders_with_items,
        first_name        = session["first_name"]
    )
# ── CANCEL ORDER ─────────────────────
@app.route("/buyer/cancel_order/<int:order_id>")
def cancel_order(order_id):
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    conn = get_db()
    cursor = conn.cursor()

    # Only cancel if status is pending or payment_pending
    cursor.execute("""
        UPDATE orders SET status = 'cancelled'
        WHERE id = ?
        AND buyer_id = ?
        AND status IN ('pending', 'payment_pending')
    """, (order_id, session["user_id"]))
    # AND status IN (...) = security check!
    # Cannot cancel if already paid or shipped!

    # Restore product stock 
    cursor.execute("""
        SELECT product_id, quantity FROM order_items
        WHERE order_id = ?
    """, (order_id,))
    items = cursor.fetchall()

    for item in items:
        cursor.execute("""
            UPDATE products SET stock = stock + ?
            WHERE id = ?
        """, (item["quantity"], item["product_id"]))
    # stock + quantity = add back the cancelled items

    conn.commit()
    conn.close()

    return redirect("/buyer/orders")

# ════════════════════════════════════════════
# FORGOT PASSWORD 
# ════════════════════════════════════════════

# ── STEP 1: Enter email ──────────────
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    error   = None
    success = None

    if request.method == "POST":
        email = request.form["email"].strip().lower()

        if not email:
            error = "Please enter your email. "
        else:
            # Check if email exists in database 
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                error = "Email not registered. "
            else:
                # Generate and send OTP
                otp = generate_otp()
                save_otp(email, otp)
                sent = send_otp_email(email, otp)

                if sent:
                    # Save email in session for next step
                    session["reset_email"] = email
                    return redirect("/reset_verify_otp")
                else:
                    error = "Failed to send OTP. Please try again. "

    return render_template("forgot_password.html",
        error=error, success=success)


# ── STEP 2: Verify OTP  ────────────────
@app.route("/reset_verify_otp", methods=["GET", "POST"])
def reset_verify_otp():

    # Check if email is in session
    if "reset_email" not in session:
        return redirect("/forgot_password")

    email   = session["reset_email"]
    error   = None

    if request.method == "POST":
        entered_otp = request.form["otp"].strip()

        if verify_otp(email, entered_otp):
            # OTP correct! Allow password reset
            session["reset_verified"] = True
            # reset_verified = True means OTP passed
            return redirect("/reset_password")
        else:
            error = "Wrong or expired OTP. "

    return render_template("reset_verify_otp.html",
        email=email, error=error)


# ── STEP 3: Reset Password ──────────
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():

    # Must have verified OTP first
    if "reset_email" not in session or not session.get("reset_verified"):
        return redirect("/forgot_password")

    email   = session["reset_email"]
    error   = None
    success = None

    if request.method == "POST":
        new_password     = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        # Validation 
        if not new_password or not confirm_password:
            error = "Please fill all fields. "

        elif len(new_password) < 6:
            error = "Password must be at least 6 characters. "

        elif new_password != confirm_password:
            error = "Passwords do not match. "

        else:
            # Hash new password
            hashed = generate_password_hash(new_password)

            conn = None
            try:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM users WHERE email = ?",
                    (email,)
                )
                user = cursor.fetchone()
            finally:
                if conn:
                    conn.close()

            # Clear reset session data
            session.pop("reset_email", None)
            session.pop("reset_verified", None)

            # Save flash message for login page
            session["flash"] = " Password reset successful! Please login. "

            return redirect("/login")

    return render_template("reset_password.html",
        email=email, error=error, success=success)


# ── RESEND OTP for reset──────
@app.route("/reset_resend_otp")
def reset_resend_otp():
    if "reset_email" not in session:
        return redirect("/forgot_password")

    email = session["reset_email"]
    otp   = generate_otp()
    save_otp(email, otp)
    send_otp_email(email, otp)

    return redirect("/reset_verify_otp")

# Jason part
# ============================================================
# PRODUCT CLASS
# ============================================================

class Product:
    def __init__(self, name, price, image, description):
        self.name        = name
        self.price       = price
        self.image       = image
        self.description = description


# ============================================================
# ROUTES
# ============================================================



@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/policy')
def policy():
    return render_template('policy.html')

@app.route('/returnpolicy')
def returnpolicy():
    return render_template('returnpolicy.html')

@app.route('/premium')
def premium():
    return render_template('premium.html')


@app.route('/warranty')
def warranty():
    return render_template('warranty.html')

@app.route('/product/<int:id>')
def product_detail(id):
    product = PRODUCTS.get(id)

    if product is None:
        return render_template('404.html'), 404

    return render_template(
        'product_detail.html',
        product = product,
        product_id = id
    )

@app.route('/set-alert/<int:id>/<int:target>')
def set_alert(id, target):
    already_exists = False
    for alert in PRICE_ALERTS:
        if alert['product_id'] == id:
            alert['target_price'] = target
            already_exists = True
            break
            
    if not already_exists:
        PRICE_ALERTS.append({
            'product_id': id,
            'target_price': target
        })

    print(PRICE_ALERTS)

    return redirect(f'/product/{id}')

@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect("/login")
        
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE('now', 'localtime')")
    orders_today = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'payment_pending'")
    pending_count = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(total_amount) FROM orders WHERE status IN ('paid', 'shipped', 'completed')")
    revenue = cursor.fetchone()[0] or 0.0
    
    cursor.execute("""
        SELECT orders.id, users.email AS buyer_email, orders.total_amount, 
               orders.payment_proof, orders.full_name
        FROM orders
        JOIN users ON orders.buyer_id = users.id
        WHERE orders.status = 'payment_pending'
        ORDER BY orders.created_at DESC
    """)
    pending_approval_list = cursor.fetchall()
    
    conn.close()
    
    return render_template(
        "Admin/dashboard.html",
        total_products=total_products,
        orders_today=orders_today,
        pending_count=pending_count,
        revenue=revenue,
        pending_orders=pending_approval_list 
    )

@app.route("/admin/approve_payment/<int:order_id>")
def admin_approve_payment(order_id):
    if "user_id" not in session:
        return redirect("/login")
        
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE orders 
        SET status = 'paid' 
        WHERE id = ? AND status = 'payment_pending'
    """, (order_id,))
    
    conn.commit()
    conn.close()
    
    return redirect("/admin")

@app.route('/helpcentre')
def helpcentre():
    return render_template('helpcentre.html')

# ── RUN  ─────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)