from flask import Flask, render_template, jsonify, request
import requests
from pymongo import MongoClient

app = Flask(__name__)


client = MongoClient('localhost', 27017)
db = client.boards


@app.route('/')
def home():
    return render_template('index의류1  .html')

@app.route('/index.html', methods=['GET'])
def getMainPage():
    return render_template('index.html')

@app.route('/create-product.html', methods=['GET'])
def getCreateProduct():
    return render_template('create-product.html')

@app.route('/api/products', methods=['GET'])
def getAllProducts():
    result = list(db.boards.find({}, {'_id': 0}))
    
    formatted_products = [
        {
            "title": product["name"],  # 'name' 필드를 'title'로 변경
            "price": f"{product['price']}원",  # 가격에 "원" 추가
            "deadline": product["deadline"],  # 날짜 형식 그대로 사용
            "category": product["category"],
            "shipping": product["shipping"]
        }
        for pro