# ════════════════════════════════════════════
# app.py — Smart Shop with OTP Email
# ════════════════════════════════════════════

from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
# random = built-in Python library to generate random numbers
# random = Python内置库，用来生成随机数字
import smtplib
# smtplib = built-in Python library to send emails
# smtplib = Python内置库，用来发送邮件
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# MIMEText, MIMEMultipart = helps us build email content
# 帮我们构建邮件内容

import os
from werkzeug.utils import secure_filename
# secure_filename = makes filename safe to save
# secure_filename = 让文件名安全可以保存
# Example: "my photo!.jpg" → "my_photo_.jpg"
# 例如：把特殊字符转换成安全字符


app = Flask(__name__)
app.secret_key = "smartshop_secret_key_2024"

# ── Email Settings 邮件设置 ──────────────────
SMTP_EMAIL    = "smartshop.noreply1234@gmail.com"
# The Gmail that SENDS the OTP
# 发送OTP的Gmail

SMTP_PASSWORD = "hnusxqjfcvupcdeq"
# The App Password we just created (no spaces!)
# 我们刚创建的应用密码（没有空格！）

SMTP_HOST     = "smtp.gmail.com"
# Gmail's SMTP server address
# Gmail的SMTP服务器地址

SMTP_PORT     = 587
# Port 587 = standard port for sending email securely
# 587端口 = 安全发送邮件的标准端口

# Allowed image types 允许的图片类型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# Only these file types allowed 只允许这些文件类型

UPLOAD_FOLDER = 'static/uploads'
# Where uploaded images are saved 上传图片保存的位置

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# MAX_CONTENT_LENGTH = maximum file size = 16MB
# 最大文件大小 = 16MB

# ════════════════════════════════════════════
# DATABASE 数据库
# ════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table 用户表
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
    # OTP表 — 临时存储OTP代码
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT NOT NULL,
            otp        TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Why separate table? Because OTP is temporary
    # 为什么单独一个表？因为OTP是临时的
    # After user verifies, we delete it
    # 用户验证后我们就删除它

        # ── Products Table 商品表 ──────────────────
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
    # id          = unique number for each product 每个商品的唯一编号
    # seller_id   = which seller owns this product 哪个卖家拥有这个商品
    # name        = product name 商品名称
    # description = product description 商品描述
    # price       = REAL means decimal number like 9.99 小数数字
    # stock       = how many items available 有多少件库存
    # category    = product category 商品类别
    # image_url   = link to product image 商品图片链接
    # FOREIGN KEY = links seller_id to users table id
    #               把seller_id连接到users表的id

    # Cart table 购物车表
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
    # buyer_id   = 哪个买家添加了这个商品
    # product_id = which product was added
    # product_id = 哪个商品被添加了
    # quantity   = how many pieces 几件
    # FOREIGN KEY = links to other tables
    # FOREIGN KEY = 连接到其他表

    conn.commit()
    conn.close()

# ════════════════════════════════════════════
# OTP FUNCTIONS OTP功能
# ════════════════════════════════════════════

def generate_otp():
    # Generate a random 6-digit number
    # 生成一个随机6位数字
    otp = random.randint(100000, 999999)
    # random.randint(min, max) = random number between min and max
    # random.randint(最小值, 最大值) = 在最小值和最大值之间的随机数
    # Example: random.randint(100000, 999999) → 483921
    # 例如：random.randint(100000, 999999) → 483921
    return str(otp)
    # str() = convert number to string "483921"
    # str() = 把数字转换成字符串 "483921"

def send_otp_email(to_email, otp):
    # This function sends OTP email to the user
    # 这个函数发送OTP邮件给用户
    try:
        # Build the email 构建邮件
        msg = MIMEMultipart()
        # MIMEMultipart = email that can have multiple parts
        # MIMEMultipart = 可以有多个部分的邮件

        msg["From"]    = SMTP_EMAIL
        # Who is sending 谁发送

        msg["To"]      = to_email
        # Who receives 谁接收

        msg["Subject"] = "Smart Shop - Your OTP Code"
        # Email subject line 邮件主题

        # Email body content 邮件正文内容
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
        # f"..." = f字符串，{otp} 插入OTP的值

        msg.attach(MIMEText(body, "html"))
        # attach = add the body to the email
        # attach = 把正文加到邮件里
        # "html" = tell email client to render as HTML
        # "html" = 告诉邮件客户端以HTML格式显示

        # Connect to Gmail and send 连接Gmail并发送
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        # Create connection to Gmail's SMTP server
        # 创建到Gmail SMTP服务器的连接

        server.starttls()
        # starttls() = upgrade to secure encrypted connection
        # starttls() = 升级到安全加密连接

        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        # Login to Gmail with our email and app password
        # 用我们的邮箱和应用密码登录Gmail

        server.send_message(msg)
        # Actually send the email!
        # 真正发送邮件！

        server.quit()
        # Close the connection
        # 关闭连接

        return True
        # True = email sent successfully
        # True = 邮件发送成功

    except Exception as e:
        # If anything goes wrong, print error and return False
        # 如果出现任何错误，打印错误并返回False
        print(f"Email error: {e}")
        return False
        # False = email failed to send
        # False = 邮件发送失败

def save_otp(email, otp):
    # Save OTP to database
    # 把OTP保存到数据库
    conn = get_db()
    cursor = conn.cursor()

    # Delete any old OTP for this email first
    # 先删除这个邮箱的旧OTP
    cursor.execute("DELETE FROM otp_codes WHERE email=?", (email,))

    # Save new OTP
    # 保存新OTP
    cursor.execute(
        "INSERT INTO otp_codes (email, otp) VALUES (?, ?)",
        (email, otp)
    )
    conn.commit()
    conn.close()

def verify_otp(email, entered_otp):
    # Check if OTP is correct and not expired
    # 检查OTP是否正确且未过期
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT otp FROM otp_codes 
        WHERE email=? 
        AND created_at >= datetime('now', '-5 minutes')
    """, (email,))
    # datetime('now', '-5 minutes') = 5 minutes ago
    # 5分钟前
    # This makes OTP expire after 5 minutes!
    # 这让OTP在5分钟后过期！

    result = cursor.fetchone()
    conn.close()

    if result and result["otp"] == entered_otp:
        # OTP matches! Delete it so it can't be used again
        # OTP匹配！删除它，这样不能再次使用
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM otp_codes WHERE email=?", (email,))
        conn.commit()
        conn.close()
        return True
    return False
   
   # upload photo
def allowed_file(filename):
    # Check if file extension is allowed
    # 检查文件扩展名是否允许
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    # rsplit('.', 1) = split by dot, keep last part
    # rsplit('.', 1) = 用点分割，保留最后一部分
    # Example: "photo.JPG" → ["photo", "JPG"]
    # [1].lower() → "jpg"
    # "jpg" in ALLOWED_EXTENSIONS → True ✅

# ════════════════════════════════════════════
# ROUTES 路由
# ════════════════════════════════════════════

@app.route("/")
def home():
    return redirect("/login")

# ── REGISTER STEP 1: Fill form 填写表单 ──────
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

        # Validation 验证
        if not first_name or not last_name or not username or not email or not password:
            error = "Please fill all required fields."
            return render_template("register.html", error=error)

        # Check if email has valid format 检查邮箱格式是否有效
        # Must have @ and a dot after @ 必须有@和@后面的点
        if "@" not in email or "." not in email.split("@")[-1]:
            error = "Please enter a valid email address. 请输入有效的邮箱地址。"
            return render_template("register.html", error=error)
        # This allows ALL emails! 这样允许所有邮箱！
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
        # 检查同一个email + 同一个角色是否已存在
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE email=? AND role=?",
            (email, role)
        )
        # Now we check BOTH email AND role
        # 现在我们同时检查email和角色
        # Same email + different role = ALLOWED!
        # 同一email + 不同角色 = 允许！
        # Same email + same role = NOT allowed!
        # 同一email + 同一角色 = 不允许！

        if cursor.fetchone():
            error = f"This email is already registered as a {role}."
            conn.close()
            return render_template("register.html", error=error)
        conn.close()

        # Save form data in session temporarily
        # 临时把表单数据保存到session
        # We don't create account yet — wait for OTP first!
        # 我们还不创建账户 — 先等OTP验证！
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
        # "pending_user" = 等待验证的用户

        # Generate and send OTP
        # 生成并发送OTP
        otp = generate_otp()
        save_otp(email, otp)

        success = send_otp_email(email, otp)

        if success:
            return redirect("/verify_otp")
            # Go to OTP verification page
            # 跳转到OTP验证页面
        else:
            error = "Failed to send OTP. Please try again."
            return render_template("register.html", error=error)

    return render_template("register.html", error=error)

# ── REGISTER STEP 2: Verify OTP 验证OTP ──────
@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp_page():

    if "pending_user" not in session:
        return redirect("/register")

    error   = None
    success = None
    # success = message to show when something good happens
    # success = 好事发生时显示的消息
    email   = session["pending_user"]["email"]

    if request.method == "POST":
        entered_otp = request.form["otp"].strip()

        if verify_otp(email, entered_otp):
            # ✅ OTP CORRECT! Create account now
            # ✅ OTP正确！现在创建账户
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
            # 把成功消息保存到session
            session["flash"] = "🎉 Account created successfully! Please login."

            return redirect("/login")

        else:
            # ❌ OTP WRONG or expired
            # ❌ OTP错误或已过期
            error = "Wrong or expired OTP. Please try again. "

    return render_template("verify_otp.html",
        email=email,
        error=error,
        success=success
    )

# ── RESEND OTP 重新发送OTP ───────────────────
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
        # 获取这个email的所有账户
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        users_found = cursor.fetchall()
        # fetchall() = get ALL matching rows (not just one)
        # fetchall() = 获取所有匹配的行（不只是一个）
        conn.close()

        if not users_found:
            # No account found 没有找到账户
            error = "Email not registered.。"

        else:
            # Check password using first account found
            # 用找到的第一个账户检查密码
            if not check_password_hash(users_found[0]["password"], password):
                error = "Wrong password."

            elif len(users_found) == 2:
                # This email has BOTH buyer and seller accounts!
                # 这个email同时有买家和卖家账户！
                # Ask user which role to login as
                # 问用户以哪个角色登录
                session["pending_login_email"] = email
                return redirect("/choose_role")
                # We go to a new page to choose role
                # 我们去一个新页面选择角色

            else:
                # Only one account, login directly
                # 只有一个账户，直接登录
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

# ── CHOOSE ROLE PAGE 选择角色页面 ─────────────
# This page shows when user has BOTH buyer and seller accounts
# 当用户同时有买家和卖家账户时显示这个页面
@app.route("/choose_role", methods=["GET", "POST"])
def choose_role():

    if "pending_login_email" not in session:
        return redirect("/login")

    if request.method == "POST":
        chosen_role = request.form["role"]
        # Get the role the user clicked
        # 获取用户点击的角色

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
            # 把选择的角色账户保存到session
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

# ── PROFILE 个人资料 ──────────────────────────
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
# SELLER SYSTEM 卖家系统
# ════════════════════════════════════════════

# ── SELLER DASHBOARD 卖家仪表板 ──────────────
@app.route("/seller_dashboard")
def seller_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "seller":
        return redirect("/buyer_dashboard")

    # Get all products belonging to this seller
    # 获取属于这个卖家的所有商品
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM products
        WHERE seller_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],))
    # WHERE seller_id = ? = only get THIS seller's products
    # 只获取这个卖家的商品
    # ORDER BY created_at DESC = newest first 最新的排在前面
    products = cursor.fetchall()
    conn.close()

    return render_template("seller_dashboard.html",
        first_name = session["first_name"],
        products   = products
    )

# ── ADD PRODUCT 添加商品 ──────────────────────
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

        # Handle image upload 处理图片上传
        image_path = None
        # image_path = where we save the image path
        # image_path = 我们保存图片路径的地方

        if 'image' in request.files:
            # request.files = contains uploaded files
            # request.files = 包含上传的文件
            file = request.files['image']

            if file and file.filename != '':
                # file.filename != '' = user actually selected a file
                # file.filename != '' = 用户确实选择了文件

                if allowed_file(file.filename):
                    # Make filename safe 让文件名安全
                    filename = secure_filename(file.filename)

                    # Add unique number to avoid same filename conflicts
                    # 加上唯一数字避免同名文件冲突
                    import time
                    filename = str(int(time.time())) + "_" + filename
                    # time.time() = current timestamp e.g. 1714900000
                    # 当前时间戳，例如 1714900000
                    # Result: "1714900000_nike_shoes.jpg"
                    # 结果："1714900000_nike_shoes.jpg"

                    # Save file to uploads folder
                    # 保存文件到uploads文件夹
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    # os.path.join = combines folder + filename
                    # os.path.join = 合并文件夹和文件名
                    # Result: "static/uploads/1714900000_nike_shoes.jpg"

                    image_path = 'uploads/' + filename
                    # We save relative path (without 'static/')
                    # 我们保存相对路径（没有'static/'）
                    # Because Flask's url_for('static') already adds it
                    # 因为Flask的url_for('static')已经会加上它
                else:
                    error = "Only images allowed (PNG, JPG, GIF, WEBP). 只允许图片文件。"
                    return render_template("add_product.html", error=error, success=success)

        # Validation 验证
        if not name or not price or not stock:
            error = "Please fill all required fields. 请填写所有必填项。"
        else:
            try:
                price = float(price)
                stock = int(stock)

                if price <= 0:
                    error = "Price must be more than 0. 价格必须大于0。"
                elif stock < 0:
                    error = "Stock cannot be negative. 库存不能为负数。"
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
                        # 把图片路径保存到数据库
                    ))
                    conn.commit()
                    conn.close()
                    success = f"✅ Product '{name}' added successfully! 商品添加成功！"

            except ValueError:
                error = "Price and stock must be numbers. 价格和库存必须是数字。"

    return render_template("add_product.html",
        error=error, success=success)

# ── LOGOUT 登出 ──────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ── EDIT PRODUCT 编辑商品 ─────────────────────
@app.route("/seller/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    # <int:product_id> = gets ID number from URL
    # <int:product_id> = 从URL获取ID数字
    # Example: /seller/edit_product/3 → product_id = 3
    # 例如：/seller/edit_product/3 → product_id = 3

    if "user_id" not in session or session["role"] != "seller":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Get this product — only if it belongs to THIS seller
    # 获取这个商品 — 只有属于这个卖家的才能编辑
    cursor.execute("""
        SELECT * FROM products
        WHERE id = ? AND seller_id = ?
    """, (product_id, session["user_id"]))
    # AND seller_id = ? = security check!
    # Sellers can ONLY edit their OWN products!
    # 卖家只能编辑自己的商品！安全检查！
    product = cursor.fetchone()
    conn.close()

    if not product:
        # Product not found or doesn't belong to this seller
        # 商品不存在或不属于这个卖家
        return redirect("/seller_dashboard")

    error   = None
    success = None

    if request.method == "POST":
        name        = request.form["name"].strip()
        description = request.form["description"].strip()
        price       = request.form["price"]
        stock       = request.form["stock"]
        category    = request.form["category"].strip()

        # Handle new image upload 处理新图片上传
        image_path = product["image_url"]
        # Keep old image by default
        # 默认保留旧图片

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    import time
                    filename = str(int(time.time())) + "_" + secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_path = 'uploads/' + filename
                    # New image uploaded! Replace old path
                    # 新图片上传了！替换旧路径
                else:
                    error = "Only images allowed. 只允许图片文件。"
                    return render_template("edit_product.html",
                        product=product, error=error, success=success)

        if not name or not price or not stock:
            error = "Please fill all required fields. 请填写所有必填项。"
        else:
            try:
                price = float(price)
                stock = int(stock)

                if price <= 0:
                    error = "Price must be more than 0. 价格必须大于0。"
                elif stock < 0:
                    error = "Stock cannot be negative. 库存不能为负数。"
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
                    # UPDATE = 修改数据库里已有的数据
                    # SET = which columns to change 要修改哪些列
                    # WHERE = which row to change 修改哪一行
                    conn.commit()
                    conn.close()
                    success = "✅ Product updated successfully! 商品更新成功！"

                    # Refresh product data to show updated values
                    # 刷新商品数据显示更新后的值
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
                    product = cursor.fetchone()
                    conn.close()

            except ValueError:
                error = "Price and stock must be numbers. 价格和库存必须是数字。"

    return render_template("edit_product.html",
        product = product,
        error   = error,
        success = success
    )


# ── DELETE PRODUCT 删除商品 ───────────────────
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
    # DELETE = remove a row from database 从数据库删除一行
    # WHERE id=? AND seller_id=? = security check!
    # Only delete if product belongs to THIS seller
    # 只删除属于这个卖家的商品
    conn.commit()
    conn.close()

    return redirect("/seller_dashboard")

# ════════════════════════════════════════════
# SHOPPING CART 购物车系统
# ════════════════════════════════════════════

# ── BUYER HOME — Show all products 买家主页显示所有商品 ──
@app.route("/buyer_dashboard")
def buyer_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    # Get ALL products from ALL sellers
    # 获取所有卖家的所有商品
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
    # JOIN = 合并products表和users表
    # users.username as seller_name = get seller's name
    # users.username as seller_name = 获取卖家的名字
    # WHERE stock > 0 = only show products with stock
    # WHERE stock > 0 = 只显示有库存的商品
    products = cursor.fetchall()

    # Get cart count for this buyer
    # 获取这个买家的购物车数量
    cursor.execute("""
        SELECT SUM(quantity) FROM cart WHERE buyer_id = ?
    """, (session["user_id"],))
    # SUM(quantity) = add up all quantities
    # SUM(quantity) = 把所有数量加起来
    result = cursor.fetchone()
    cart_count = result[0] if result[0] else 0
    # if result[0] is None (empty cart), use 0
    # 如果result[0]是None（空购物车），用0
    conn.close()

    return render_template("buyer_dashboard.html",
        first_name = session["first_name"],
        products   = products,
        cart_count = cart_count
    )

# ── ADD TO CART 加入购物车 ────────────────────
@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    # Only buyers can add to cart
    # 只有买家可以加入购物车
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    quantity = int(request.form.get("quantity", 1))
    # request.form.get("quantity", 1) = get quantity, default 1
    # 获取数量，默认是1

    conn = get_db()
    cursor = conn.cursor()

    # Check if product exists and has enough stock
    # 检查商品是否存在且有足够库存
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        return redirect("/buyer_dashboard")

    if product["stock"] < quantity:
        # Not enough stock! 库存不足！
        conn.close()
        return redirect("/buyer_dashboard")

    # Check if this product already in buyer's cart
    # 检查这个商品是否已经在买家的购物车里
    cursor.execute("""
        SELECT * FROM cart
        WHERE buyer_id=? AND product_id=?
    """, (session["user_id"], product_id))
    existing = cursor.fetchone()

    if existing:
        # Already in cart! Just increase quantity
        # 已经在购物车里！只需增加数量
        cursor.execute("""
            UPDATE cart
            SET quantity = quantity + ?
            WHERE buyer_id=? AND product_id=?
        """, (quantity, session["user_id"], product_id))
        # quantity + ? = add to existing quantity
        # quantity + ? = 加到已有的数量上
    else:
        # Not in cart yet, add new item
        # 还没在购物车里，添加新商品
        cursor.execute("""
            INSERT INTO cart (buyer_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (session["user_id"], product_id, quantity))

    conn.commit()
    conn.close()

    return redirect("/cart")
    # After adding, go to cart page
    # 添加后跳转到购物车页面

# ── VIEW CART 查看购物车 ──────────────────────
@app.route("/cart")
def view_cart():
    if "user_id" not in session:
        return redirect("/login")
    if session["role"] != "buyer":
        return redirect("/seller_dashboard")

    conn = get_db()
    cursor = conn.cursor()

    # Get all cart items with product details
    # 获取所有购物车商品及其详情
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
    # = 价格 × 数量 = 每件商品小计
    items = cursor.fetchall()

    # Calculate total price 计算总价
    total = sum(item["subtotal"] for item in items)
    # sum() = adds up all subtotals
    # sum() = 把所有小计加起来

    conn.close()

    return render_template("cart.html",
        items      = items,
        total      = total,
        first_name = session["first_name"]
    )

# ── UPDATE CART QUANTITY 更新购物车数量 ─────────
@app.route("/cart/update/<int:cart_id>", methods=["POST"])
def update_cart(cart_id):
    if "user_id" not in session:
        return redirect("/login")

    quantity = int(request.form.get("quantity", 1))

    if quantity < 1:
        # If quantity less than 1, remove item
        # 如果数量小于1，删除商品
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

# ── REMOVE FROM CART 从购物车删除 ─────────────
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
    # 只删除属于这个买家的（安全！）
    conn.commit()
    conn.close()

    return redirect("/cart")

# ── RUN 运行 ─────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)