from flask import Flask, render_template, url_for, flash, redirect, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from decimal import Decimal
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user
import os
import random
from flask_migrate import Migrate

app = Flask(__name__)

app.config["SECRET_KEY"] = "your_secret_key_here"

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Set the login view

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"User('{self.first_name}', '{self.last_name}', '{self.email}')"

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Product('{self.name}', '{self.category}', {self.price})"
    
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # Relationships
    order = db.relationship('Order', backref='order_items')
    product = db.relationship('Product', backref='order_items')

    def __repr__(self):
        return f"OrderItem('{self.order_id}', '{self.product_id}', '{self.quantity}')"

# Cart Item Model
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    product = db.relationship('Product', backref='cart_items')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Pending')

    # Relationships
    user = db.relationship('User', backref='orders')

    def __repr__(self):
        return f"Order('{self.id}', '{self.total_amount}', '{self.status}')"

# Load User for LoginManager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context Processor for current_user
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Context processor for cart count
@app.context_processor
def utility_processor():
    def get_cart_count():
        if 'cart' not in session:
            return 0
        return sum(session['cart'].values())
    return dict(get_cart_count=get_cart_count)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form['first_name']
        current_user.last_name = request.form['last_name']
        current_user.email = request.form['email']
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', user=current_user, orders=orders)

# Function to get category description
def get_category_description(category):
    descriptions = {
        'electronics': 'Discover the latest in technology with our premium electronic devices and accessories.',
        'fashion': 'Express yourself with our trendy collection of fashion items and accessories.',
        'home-living': 'Transform your living space with our elegant home décor and furniture collection.',
        'beauty': 'Enhance your natural beauty with our premium beauty and skincare products.',
        'sports-outdoors': 'Get active with our high-quality sports equipment and outdoor gear.'
    }
    return descriptions.get(category, 'Explore our amazing products')

# Function to get products
def get_products(category=None):
    if category:
        return Product.query.filter_by(category=category).all()
    return Product.query.all()

# Routes
@app.route('/')
def home():
    categories = ['electronics', 'fashion', 'home-living', 'beauty', 'sports-outdoors']
    random_category = random.choice(categories)
    products = get_products(random_category)
    return render_template('index.html', products=products[:15], category=random_category)

@app.route('/category/<category>')
def category_page(category):
    products = get_products(category)
    category_desc = get_category_description(category)
    return render_template('category.html', 
                         category=category, 
                         products=products[:15],
                         category_description=category_desc)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Log out the user
    session.pop('cart', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now login', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/cart')
@login_required
def cart():
    if 'cart' not in session:
        session['cart'] = {}
    
    cart_items = []
    total = Decimal('0.0')
    
    for product_id, quantity in session['cart'].items():
        product = Product.query.get(int(product_id))
        if product:
            item_total = Decimal(str(product.price)) * Decimal(str(quantity))
            total += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'item_total': float(item_total)
            })
    
    return render_template('cart.html', cart_items=cart_items, total=float(total))

@app.route('/add-to-cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}
    
    product = Product.query.get_or_404(product_id)
    
    if str(product_id) in session['cart']:
        current_quantity = session['cart'][str(product_id)]
        if current_quantity + 1 <= product.stock:
            session['cart'][str(product_id)] += 1
            session.modified = True
            flash('Product quantity updated in cart!', 'success')
        else:
            flash(f'Sorry, only {product.stock} item(s) available in stock!', 'warning')
    else:
        if product.stock > 0:
            session['cart'][str(product_id)] = 1
            session.modified = True
            flash('Product added to cart!', 'success')
        else:
            flash('Sorry, this product is out of stock!', 'warning')
    
    return redirect(request.referrer or url_for('home'))

@app.route('/update-cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    if 'cart' not in session:
        return redirect(url_for('cart'))
    
    quantity = int(request.form.get('quantity', 0))
    product = Product.query.get_or_404(product_id)
    
    if quantity <= 0:
        session['cart'].pop(str(product_id), None)
        flash('Product removed from cart!', 'success')
    elif quantity <= product.stock:
        session['cart'][str(product_id)] = quantity
        session.modified = True
        flash('Cart updated successfully!', 'success')
    else:
        session['cart'][str(product_id)] = product.stock
        session.modified = True
        flash(f'Quantity adjusted to available stock ({product.stock})!', 'warning')
    
    return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'].pop(str(product_id), None)
        session.modified = True
        flash('Product removed from cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/about')
def about():
    return render_template('aboutus.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if name and email and message:
            # Here you would typically handle the contact form submission
            # (e.g., send email, save to database, etc.)
            flash('Message sent successfully!', 'success')
        else:
            flash('Please fill in all fields.', 'error')

        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')

        # Validate email uniqueness (if changed)
        if email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already exists. Please use a different email.', 'danger')
                return redirect(url_for('profile'))

        # Update user information
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/shipping', methods=['GET', 'POST'])
@login_required
def shipping():
    if request.method == 'POST':
        # Get shipping details from the form
        shipping_details = {
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'zip_code': request.form.get('zip_code'),
            'country': request.form.get('country')
        }
        session['shipping_details'] = shipping_details
        return redirect(url_for('checkout'))
    
    return render_template('shipping.html')

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))

    if 'shipping_details' not in session:
        return redirect(url_for('shipping'))

    if request.method == 'POST':
        # Calculate the total amount
        total = Decimal('0.0')
        for product_id, quantity in session['cart'].items():
            product = Product.query.get(int(product_id))
            if product:
                total += Decimal(str(product.price)) * Decimal(str(quantity))

        # Create a new order
        new_order = Order(
            user_id=current_user.id,
            total_amount=float(total),
            status='Pending'
        )
        db.session.add(new_order)
        db.session.flush()  # Assign an ID to the new order

        # Create OrderItem records for each product in the cart
        for product_id, quantity in session['cart'].items():
            product = Product.query.get(int(product_id))
            if product:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=quantity
                )
                db.session.add(order_item)

                # Update stock levels
                product.stock -= quantity
                db.session.add(product)
        
        try:
            db.session.commit()
            session.pop('cart', None)
            session.pop('shipping_details', None)
            flash('Order placed successfully! Thank you for your purchase.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing your order. Please try again.', 'error')
        
        return redirect(url_for('home'))

    shipping_details = session.get('shipping_details', {})
    cart_items = [(Product.query.get(int(product_id)), quantity) for product_id, quantity in session['cart'].items()]
    total = sum(product.price * quantity for product, quantity in cart_items)
    return render_template('checkout.html', shipping_details=shipping_details, cart_items=cart_items, total=total)

@app.route('/search')
def search():
    query = request.args.get('query', '')
    if query:
        products = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
    else:
        products = []
    return render_template('search_results.html', query=query, products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

# Sample Products Insertion
def insert_sample_products():
    sample_products = [
        # Electronics Category
        Product(name="Smart LED TV", image_url="smart_tv.jpg", price=39999.99, stock=15, category="electronics"),
        Product(name="Gaming Laptop", image_url="gaming_laptop.jpg", price=85999.99, stock=5, category="electronics"),
        Product(name="Wireless Earbuds", image_url="earbuds.jpg", price=1999.99, stock=50, category="electronics"),
        Product(name="Smartphone", image_url="smartphone.jpg", price=29999.99, stock=25, category="electronics"),
        
        # Fashion Category
        Product(name="Denim Jeans", image_url="jeans.jpg", price=1999.99, stock=100, category="fashion"),
        Product(name="Cotton T-Shirt", image_url="tshirt.jpg", price=699.99, stock=200, category="fashion"),
        Product(name="Running Shoes", image_url="shoes.jpg", price=2499.99, stock=50, category="fashion"),
        Product(name="Leather Wallet", image_url="wallet.jpg", price=999.99, stock=75, category="fashion"),
        
        # Home & Living Category
        Product(name="Coffee Maker", image_url="coffee_maker.jpg", price=4999.99, stock=30, category="home-living"),
        Product(name="Bedsheet Set", image_url="bedsheet.jpg", price=1499.99, stock=80, category="home-living"),
        Product(name="Floor Lamp", image_url="lamp.jpg", price=2999.99, stock=40, category="home-living"),
        Product(name="Cushion Set", image_url="cushions.jpg", price=799.99, stock=100, category="home-living"),
        
        # Beauty Category
        Product(name="Face Cream", image_url="face_cream.jpg", price=499.99, stock=150, category="beauty"),
        Product(name="Shampoo", image_url="shampoo.jpg", price=299.99, stock=200, category="beauty"),
        Product(name="Perfume", image_url="perfume.jpg", price=1999.99, stock=60, category="beauty"),
        Product(name="Makeup Kit", image_url="makeup_kit.jpg", price=2499.99, stock=45, category="beauty"),
        
        # Sports & Outdoors Category
        Product(name="Yoga Mat", image_url="yoga_mat.jpg", price=799.99, stock=100, category="sports-outdoors"),
        Product(name="Dumbbells Set", image_url="dumbbells.jpg", price=1999.99, stock=40, category="sports-outdoors"),
        Product(name="Tennis Racket", image_url="tennis_racket.jpg", price=2999.99, stock=30, category="sports-outdoors"),
        Product(name="Camping Tent", image_url="tent.jpg", price=4999.99, stock=20, category="sports-outdoors")
    ]
    
    db.session.bulk_save_objects(sample_products)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Uncomment the next line to insert sample products
        # insert_sample_products()
    app.run(debug=True)