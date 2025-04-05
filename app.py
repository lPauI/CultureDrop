from flask import Flask, render_template

from dotenv import load_dotenv

from flask_sqlalchemy import SQLAlchemy

import os

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app and configure database connection
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

mysql_user = os.getenv('MYSQL_USER')
mysql_password = os.getenv('MYSQL_PASSWORD')
mysql_host = os.getenv('MYSQL_HOST')
mysql_database = os.getenv('MYSQL_DATABASE')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_database}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Clothes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)


@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
