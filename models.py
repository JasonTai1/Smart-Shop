from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(300))
    
    # Relationship to get all listings/prices for this product
    listings = db.relationship('ProductListing', backref='product', lazy=True)

    # Helper function to find the lowest price
    def get_best_price(self):
        if not self.listings:
            return None
        return min(listing.price for listing in self.listings)

class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    website_url = db.Column(db.String(200))

class ProductListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    url_to_buy = db.Column(db.String(500)) # Link directly to the seller's product page
    
    # Connect back to the seller name easily
    seller = db.relationship('Seller', backref='listings')