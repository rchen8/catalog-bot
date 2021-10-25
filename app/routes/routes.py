from flask import jsonify, render_template, request
from app import app

@app.route('/', methods=['GET'])
def index():
  return render_template('index.html')
