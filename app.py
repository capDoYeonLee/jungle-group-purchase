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
        for product in result
    ]

    return jsonify({'result':'success', 'products': formatted_products})




@app.route('/api/product', methods=['POST'])
def createProduct():
    board = request.form['title']
    name = request.form['item_name']
    link = request.form['item_url']
    price = request.form['item_price']
    deadline = request.form['deadline']
    shipping = request.form['delivery_fee']
    condition = request.form['free_delivery_cond']
    message = request.form['confirmation_msg']
    category = request.form['category']
    quantity = request.form['item_count']

    product = { 'board': board, 'name':name, 'link':link, 'price':price, 
                'deadline':deadline, 'shipping':shipping, 'condition':condition, 
                'message':message, 'category':category, 'quantity':quantity }
    
    db.boards.insert_one(product)
    return jsonify({'result': 'success'})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)

