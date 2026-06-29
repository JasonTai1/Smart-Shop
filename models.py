from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 🟢 Product Table
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    seller_id = db.Column(db.Integer)

    name = db.Column(db.String(100), nullable=False)

    description = db.Column(db.Text)

    price = db.Column(db.Float)

    stock = db.Column(db.Integer, default=0)

    category = db.Column(db.String(100))

    image_url = db.Column(db.String(300))

# 🟢 Forum Post
class ForumPost(db.Model):
    __tablename__ = "forum_post"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    content = db.Column(db.Text)

    author = db.Column(db.String(100))

    likes = db.Column(db.Integer, default=0)

    views = db.Column(db.Integer, default=0)

    image_url = db.Column(db.String(300), nullable=True)

# 🟢 Comment System
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    content = db.Column(db.Text, nullable=False)
    
    author = db.Column(db.String(100), nullable=False) # 存名字展示（如 session["username"]）
    
    user_id = db.Column(db.Integer, nullable=False)    # 🔥 核心：必须存是谁发的 ID
    
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)

    image_url = db.Column(db.String(300), nullable=True)