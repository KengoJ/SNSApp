from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('main.config')
app.config['SECRET_KEY'] = 'secret'
#app.config['UPLOAD_FOLDER'] = './static/upload_img'


db = SQLAlchemy(app)
import main.views

