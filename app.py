from flask import Flask, render_template, request, redirect, flash
from routes.main import main

app = Flask(__name__)
app.secret_key = '6f2883g%32@sw1'
app.register_blueprint(main)


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
# PRODUCT DATA  
# ============================================================

PRODUCTS = {

    1: Product(
        name        = "13-inch MacBook Neo",
        price       = "RM1,999.00",
        image       = "macbookneo.jpg",
        description = "Powerful laptop for work,and study."
    ),

    2: Product(
        name        = "iPhone 17e",
        price       = "RM2,949.00",
        image       = "iphone17.png",
        description = "Latest Apple smartphone with advanced camera system."
    ),

}

PRICE_ALERTS = []

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def home():
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

    return render_template(
        'homepage.html',
        products=PRODUCTS.items()
    )


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

@app.route('/homepage')
def homepage():
    
    return render_template(
    'homepage.html' ,
    products=PRODUCTS.items()
    )

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

    total_products = len(PRODUCTS)

    pending_orders = 3

    orders_today = 12

    revenue = 18240

    return render_template(
        "Admin/dashboard.html",
        total_products=total_products,
        pending_orders=pending_orders,
        orders_today=orders_today,
        revenue=revenue
    )

@app.route('/helpcentre')
def helpcentre():
    return render_template('helpcentre.html')


# ============================================================
# RUN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True)