from flask import Flask,render_template,request,redirect,session,url_for
from models import db,Product,ForumPost,Comment

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

@app.route('/forum/add', methods=['GET', 'POST'])
def add_post():

    if request.method == 'POST':

        post = ForumPost(
            title=request.form['title'],
            content=request.form['content']
        )
        db.session.add(post)
        db.session.commit()

        return redirect('/forum')

    return render_template('add_post.html')

@app.route("/delete_post/<int:id>")
def delete_post(id):

    post = ForumPost.query.get_or_404(id)

    db.session.delete(post)

    db.session.commit()

    return redirect("/forum")

@app.route("/post/<int:id>")
def view_post(id):

    post = ForumPost.query.get_or_404(id)

    post.views += 1
    db.session.commit()

    comments = Comment.query.filter_by(
        post_id=id
    ).all()

    return render_template(
        "view_post.html",
        post=post,
        comments=comments
    )

@app.route("/like_post/<int:id>")
def like_post(id):

    post = ForumPost.query.get_or_404(id)

    post.likes += 1

    db.session.commit()

    return redirect(
        url_for("view_post", id=id)
    )

@app.route("/add_comment/<int:id>", methods=["POST"])
def add_comment(id):

    content = request.form["content"]

    comment = Comment(
        author="Guest",
        content=content,
        post_id=id
    )

    db.session.add(comment)
    db.session.commit()

    return redirect(
        url_for("view_post", id=id)
    )

# ── SELLER EARNINGS 卖家收入追踪 ──────────────────
@app.route("/seller/earnings")
def seller_earnings():
    if "user_id" not in session or session["role"] != "seller":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Total earnings from ALL paid orders
    # 所有已付款订单的总收入
    cursor.execute("""
        SELECT
            COALESCE(SUM(order_items.price * order_items.quantity), 0)
            as total_earned
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        JOIN orders   ON order_items.order_id   = orders.id
        WHERE products.seller_id = ?
        AND   orders.status IN ('paid', 'shipped', 'delivered')
    """, (session["user_id"],))
    total_earned = cursor.fetchone()["total_earned"]

    # Pending earnings (payment_pending orders)
    # 待确认收入（付款待确认的订单）
    cursor.execute("""
        SELECT
            COALESCE(SUM(order_items.price * order_items.quantity), 0)
            as pending_earned
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        JOIN orders   ON order_items.order_id   = orders.id
        WHERE products.seller_id = ?
        AND   orders.status = 'payment_pending'
    """, (session["user_id"],))
    pending_earned = cursor.fetchone()["pending_earned"]

    # This week earnings 本周收入
    cursor.execute("""
        SELECT
            COALESCE(SUM(order_items.price * order_items.quantity), 0)
            as week_earned
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        JOIN orders   ON order_items.order_id   = orders.id
        WHERE products.seller_id = ?
        AND   orders.status IN ('paid', 'shipped', 'delivered')
        AND   orders.created_at >= datetime('now', '-7 days')
    """, (session["user_id"],))
    # datetime('now', '-7 days') = 7 days ago
    # 7天前
    week_earned = cursor.fetchone()["week_earned"]

    # Total orders count 总订单数
    cursor.execute("""
        SELECT COUNT(DISTINCT orders.id) as order_count
        FROM orders
        JOIN order_items ON orders.id   = order_items.order_id
        JOIN products    ON order_items.product_id = products.id
        WHERE products.seller_id = ?
        AND   orders.status IN ('paid', 'shipped', 'delivered')
    """, (session["user_id"],))
    order_count = cursor.fetchone()["order_count"]

    # Recent orders 最近的订单
    cursor.execute("""
        SELECT DISTINCT
            orders.id,
            orders.created_at,
            orders.status,
            orders.total_amount,
            orders.full_name,
            users.email as buyer_email,
            COALESCE(SUM(
                order_items.price * order_items.quantity
            ), 0) as seller_amount
        FROM orders
        JOIN order_items ON orders.id = order_items.order_id
        JOIN products    ON order_items.product_id = products.id
        JOIN users       ON orders.buyer_id = users.id
        WHERE products.seller_id = ?
        GROUP BY orders.id
        ORDER BY orders.created_at DESC
        LIMIT 10
    """, (session["user_id"],))
    recent_orders = cursor.fetchall()

    # Payout info 收款信息
    cursor.execute("""
        SELECT * FROM seller_payout WHERE seller_id = ?
    """, (session["user_id"],))
    payout_info = cursor.fetchone()

    conn.close()

    return render_template("seller_earnings.html",
        total_earned   = total_earned,
        pending_earned = pending_earned,
        week_earned    = week_earned,
        order_count    = order_count,
        recent_orders  = recent_orders,
        payout_info    = payout_info,
        first_name     = session["first_name"]
    )

# ── SELLER SALES REPORT 卖家销售报告 ─────────────
@app.route("/seller/report")
def seller_report():
    if "user_id" not in session or session["role"] != "seller":
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Sales by month (last 6 months) 最近6个月按月销售额
    cursor.execute("""
        SELECT
            strftime('%Y-%m', orders.created_at) as month,
            COALESCE(SUM(order_items.price * order_items.quantity), 0) as revenue,
            COUNT(DISTINCT orders.id) as order_count
        FROM orders
        JOIN order_items ON orders.id = order_items.order_id
        JOIN products    ON order_items.product_id = products.id
        WHERE products.seller_id = ?
        AND   orders.status IN ('paid', 'shipped', 'delivered')
        AND   orders.created_at >= datetime('now', '-6 months')
        GROUP BY strftime('%Y-%m', orders.created_at)
        ORDER BY month ASC
    """, (session["user_id"],))
    # strftime('%Y-%m', ...) = formats date as "2026-05"
    # strftime('%Y-%m', ...) = 把日期格式化为 "2026-05"
    monthly_sales = cursor.fetchall()

    # Top 5 best selling products 前5名最畅销商品
    cursor.execute("""
        SELECT
            products.name,
            products.image_url,
            SUM(order_items.quantity) as total_sold,
            SUM(order_items.price * order_items.quantity) as total_revenue
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        JOIN orders   ON order_items.order_id   = orders.id
        WHERE products.seller_id = ?
        AND   orders.status IN ('paid', 'shipped', 'delivered')
        GROUP BY products.id
        ORDER BY total_sold DESC
        LIMIT 5
    """, (session["user_id"],))
    top_products = cursor.fetchall()

    # Overall summary 总体摘要
    cursor.execute("""
        SELECT
            COUNT(DISTINCT orders.id)                                  as total_orders,
            COALESCE(SUM(order_items.quantity), 0)                     as total_items_sold,
            COALESCE(SUM(order_items.price * order_items.quantity), 0) as total_revenue,
            COALESCE(AVG(orders.total_amount), 0)                      as avg_order_value
        FROM orders
        JOIN order_items ON orders.id = order_items.order_id
        JOIN products    ON order_items.product_id = products.id
        WHERE products.seller_id = ?
        AND   orders.status IN ('paid', 'shipped', 'delivered')
    """, (session["user_id"],))
    summary = cursor.fetchone()

    conn.close()

    # Convert to lists for chart
    # 转换成列表给图表用
    months   = [row["month"]   for row in monthly_sales]
    revenues = [row["revenue"] for row in monthly_sales]
    orders_count = [row["order_count"] for row in monthly_sales]

    return render_template("seller_report.html",
        months        = months,
        revenues      = revenues,
        orders_count  = orders_count,
        top_products  = top_products,
        summary       = summary,
        first_name    = session["first_name"]
    )

if __name__ == '__main__':
    app.run(debug=True)