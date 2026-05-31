from flask import Flask,render_template,request
from models import db,Product

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
db.init_app(app)

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)

    return render_template(
        'product.html',
        product=product,
    )

@app.route('/search')
def search():

    query = request.args.get('q')

    products = Product.query.filter(
        Product.name.ilike(f"%{query}%")
    ).all()

    return render_template(
        'search.html',
        products=products,
        query=query
    )

@app.route('/category/<category>')
def category(category):

    products = Product.query.filter_by(
        category=category
    ).all()

    return render_template(
        'search.html',
        products=products,
        query=category
    )

@app.route('/forum')
def forum():
    
    posts = ForumPost.query.all()

    return render_template(
        'forum.html',
        posts=posts
    )

if __name__ == '__main__':
    app.run(debug=True)