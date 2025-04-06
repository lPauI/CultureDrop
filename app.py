from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify

from dotenv import load_dotenv

from flask_wtf import CSRFProtect, FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email
from sqlalchemy.sql.expression import func
from flask_cors import CORS

from bcrypt import hashpw, gensalt, checkpw

import os

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app and configure database connection
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
csrf = CSRFProtect(app)

mysql_user = os.getenv('MYSQL_USER')
mysql_password = os.getenv('MYSQL_PASSWORD')
mysql_host = os.getenv('MYSQL_HOST')
mysql_database = os.getenv('MYSQL_DATABASE')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_database}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Clothes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)


class Songs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    cover_path = db.Column(db.String(200), nullable=False)
    song_path = db.Column(db.String(200), nullable=False)
    lyrics = db.Column(db.Text, nullable=False)


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    clothes_id = db.Column(db.Integer, db.ForeignKey('clothes.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    clothes = db.relationship('Clothes', backref='cart_items')


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())


@app.route('/')
def home():
    is_logged = 'user_id' in session
    
    clothes = Clothes.query.order_by(func.random()).all()
    songs = Songs.query.order_by(func.random()).limit(8).all()
    
    return render_template('index.html', clothes=clothes, songs=songs)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        flash('You are already logged. Log out for a new account.', 'info')
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        hashed_password = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
        
        new_user = Users(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        flash('You are already logged in.', 'info')
        return redirect(url_for('home'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        # Find user by email
        user = Users.query.filter_by(email=email).first()
        
        # Check if user exists and password is correct
        if user and checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            # Set up session
            session['user_id'] = user.id
            session['email'] = user.email
            
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    flash('You logged out successfully!', 'success')
    return redirect(url_for('home'))


@app.route("/checkout")
def checkout():
    if 'user_id' not in session:
        flash('You must be logged in to access the checkout page.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    total_price = sum(item.quantity * item.clothes.price for item in cart_items)
    
    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash('You need to login for this action.', 'warning')
        return redirect(url_for('login'))
        
    product_id = request.form.get('product_id')
    if not product_id:
        flash('The product was not found.', 'warning')
        return redirect(url_for('home'))
    
    user_id = session['user_id']
    
    # Check if product is already in cart
    cart_item = Cart.query.filter_by(user_id=user_id, clothes_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        new_item = Cart(user_id=user_id, clothes_id=product_id, quantity=1)
        db.session.add(new_item)
    
    db.session.commit()
    flash('The product was added to the cart!', 'success')
    return redirect(url_for('home'))


@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    if 'user_id' not in session:
        flash('You need to login for this action.', 'warning')
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    cart_item = Cart.query.filter_by(id=cart_item_id, user_id=user_id).first()
    
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('The product was removed from the cart!', 'success')
    else:
        flash('The product was not found.', 'warning')
        
    return redirect(url_for('checkout'))


@app.route('/create_order', methods=['POST'])
def create_order():
    if 'user_id' not in session:
        flash('You need to login for this action.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('checkout'))
    
    total_price = sum(item.quantity * item.clothes.price for item in cart_items)
    
    new_order = Order(user_id=user_id, total_price=total_price)
    db.session.add(new_order)
    
    for item in cart_items:
        db.session.delete(item)
    
    db.session.commit()
    flash('The order was created successfully!', 'success')
    return redirect(url_for('home'))


@app.route('/song/<int:song_id>')
def song(song_id):
    song = Songs.query.get_or_404(song_id)
    return render_template('song.html', song=song)


@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        flash('You need to be logged in to view favorites.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    favorites_list = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.created_at.desc()).all()
    favorites_details = []

    for fav in favorites_list:
        details = {
            'id': fav.id,
            'created_at': fav.created_at
        }

        if fav.item_type == 'cloth':
            cloth = Clothes.query.get(fav.item_id)
            if cloth:
                details['title'] = cloth.name
                details['cover'] = cloth.image_path
        
        elif fav.item_type == 'song':
            song = Songs.query.get(fav.item_id)
            if song:
                details['title'] = song.title
                details['cover'] = song.cover_path
        
        favorites_details.append(details)

    return render_template('favorites.html', favorites=favorites_details)


@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    if 'user_id' not in session:
        flash('You need to be logged in to perform this action.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    item_id = request.form.get('item_id')
    item_type = request.form.get('item_type')
    
    if not item_id or not item_type:
        flash('Invalid item selection.', 'warning')
        return redirect(url_for('home'))
    
    # Prevent duplicate favorites
    existing_favorite = Favorite.query.filter_by(user_id=user_id, item_id=item_id, item_type=item_type).first()
    if existing_favorite:
        flash('Item already in favorites.', 'info')
    else:
        new_favorite = Favorite(user_id=user_id, item_id=item_id, item_type=item_type)
        db.session.add(new_favorite)
        db.session.commit()
        flash('Item added to favorites!', 'success')
    
    return redirect(url_for('home'))


@app.route('/remove_favorite/<int:favorite_id>', methods=['POST'])
def remove_favorite(favorite_id):
    if 'user_id' not in session:
        flash('You need to be logged in to perform this action.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    fav = Favorite.query.filter_by(id=favorite_id, user_id=user_id).first()
    
    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash('Item removed from favorites!', 'success')
    else:
        flash('Favorite not found.', 'warning')
    
    return redirect(url_for('favorites'))


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
