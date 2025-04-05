from flask import Flask, render_template, redirect, url_for, flash, session

from dotenv import load_dotenv

from flask_wtf import CSRFProtect, FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email
from sqlalchemy.sql.expression import func

from bcrypt import hashpw, gensalt, checkpw

import os

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app and configure database connection
app = Flask(__name__)
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


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


@app.route('/')
def home():
    is_logged = 'user_id' in session
    
    clothes = Clothes.query.order_by(func.random()).all()
    
    return render_template('index.html', clothes=clothes)


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
    flash('Te-ai deconectat cu succes!', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
