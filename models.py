from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 🟢 Product Table
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    category = db.Column(db.String(100))

    description = db.Column(db.Text)

    image_url = db.Column(db.String(300))

    seller = db.Column(db.String(100))

    price = db.Column(db.Float)

# 🟢 Forum Post
class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    content = db.Column(db.Text)

# 🟢 Comment System
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'))

    content = db.Column(db.Text)