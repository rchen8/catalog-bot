from dotenv import load_dotenv
from flask import abort, Flask, render_template, request, jsonify
from flask_heroku import Heroku
from flask_sqlalchemy import SQLAlchemy
import sys

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if '--dev' in sys.argv:
  app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/<database>'
else:
  heroku = Heroku(app)
db = SQLAlchemy(app)

from . import routes as Routes
