from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)  # Enhanced security
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)  # Static folder path

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    address = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Forms
class SignupForm(FlaskForm):
    name = StringField('নাম', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('ইমেইল', validators=[DataRequired(), Email()])
    password = PasswordField('পাসওয়ার্ড', validators=[DataRequired(), Length(min=8)])

class SigninForm(FlaskForm):
    email = StringField('ইমেইল', validators=[DataRequired(), Email()])
    password = PasswordField('পাসওয়ার্ড', validators=[DataRequired()])

class CheckoutForm(FlaskForm):
    address = TextAreaField('ঠিকানা', validators=[DataRequired()])
    email = StringField('ইমেইল', validators=[DataRequired(), Email()])
    phone = StringField('ফোন নম্বর', validators=[DataRequired(), Length(min=10, max=15)])

# Initialize Database with Static Image Paths
with app.app_context():
    db.create_all()
    if not Product.query.first():
        products = [
            Product(name='ওয়্যারলেস হেডফোন', description='উচ্চ মানের সাউন্ড, নয়েজ ক্যান্সেলেশন, ২০ ঘণ্টা ব্যাটারি লাইফ।', price=4500, image='headphones.png'),
            Product(name='ক্যাজুয়াল টি-শার্ট', description='আরামদায়ক তুলার টি-শার্ট, সব মাপে পাওয়া যায়।', price=1500, image='tshirt.png'),
            Product(name='স্মার্ট ঘড়ি', description='ফিটনেস ট্র্যাকার, হার্ট রেট মনিটর, ওয়াটারপ্রুফ।', price=8500, image='smartwatch.png'),
            Product(name='কিচেন ব্লেন্ডার', description='৫০০ ওয়াট পাওয়ার, মাল্টি-স্পিড, টেকসই ব্লেড।', price=3500, image='blender.png'),
        ]
        db.session.bulk_save_objects(products)
        db.session.commit()

# Routes
@app.route('/')
def index():
    products = Product.query.all()
    print(f"Products fetched: {products}")  # Debug output
    if not products:
        return "No products found. Please check the database.", 500
    return render_template('index.html', products=products)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('ইমেইল ইতিমধ্যে নিবন্ধিত!', 'danger')
            return redirect(url_for('signup'))
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('নিবন্ধন সফল! এখন সাইন ইন করুন।', 'success')
        return redirect(url_for('signin'))
    return render_template('signup.html', form=form)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            flash('সাইন ইন সফল!', 'success')
            return redirect(url_for('index'))
        flash('ভুল ইমেইল বা পাসওয়ার্ড!', 'danger')
    return render_template('signin.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('আপনি সাইন আউট করেছেন।', 'success')
    return redirect(url_for('index'))

@app.route('/product/<int:id>')
def product_details(id):
    product = Product.query.get_or_404(id)
    return render_template('product_details.html', product=product)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('কার্টে যোগ করতে সাইন ইন করুন!', 'danger')
        return redirect(url_for('signin'))
    quantity = int(request.form.get('quantity', 1))
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append({'product_id': product_id, 'quantity': quantity})
    session.modified = True
    flash('পণ্য কার্টে যোগ করা হয়েছে!', 'success')
    return redirect(url_for('cart'))

@app.route('/buy_now/<int:product_id>', methods=['POST'])
def buy_now(product_id):
    if 'user_id' not in session:
        flash('কিনতে সাইন ইন করুন!', 'danger')
        return redirect(url_for('signin'))
    quantity = int(request.form.get('quantity', 1))
    session['cart'] = [{'product_id': product_id, 'quantity': quantity}]
    session.modified = True
    return redirect(url_for('checkout'))

@app.route('/cart')
def cart():
    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', cart_items=[])
    cart_items = []
    total = 0
    for item in session['cart']:
        product = Product.query.get(item['product_id'])
        if product:
            cart_items.append({'product': product, 'quantity': item['quantity']})
            total += product.price * item['quantity']
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('চেকআউট করতে সাইন ইন করুন!', 'danger')
        return redirect(url_for('signin'))
    if 'cart' not in session or not session['cart']:
        flash('আপনার কার্ট খালি!', 'danger')
        return redirect(url_for('index'))
    form = CheckoutForm()
    if form.validate_on_submit():
        user_id = session['user_id']
        for item in session['cart']:
            order = Order(
                user_id=user_id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                address=form.address.data,
                email=form.email.data,
                phone=form.phone.data
            )
            db.session.add(order)
        db.session.commit()
        session['cart'] = []
        session.modified = True
        flash('অর্ডার সফলভাবে সম্পন্ন হয়েছে!', 'success')
        return redirect(url_for('index'))
    return render_template('checkout.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)