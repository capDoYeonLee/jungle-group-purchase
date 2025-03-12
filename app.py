from flask import Flask, render_template, jsonify, request
import requests
from pymongo import MongoClient
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

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
    result = list(db.boards.find({}))
    
    formatted_products = [
        {   
            "id": str(product["_id"]),
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



#def scheduleComingDeadlineProducts():

#21:41 추가됨 모달창 라우트
@app.route('/buy_product/<id>', methods=['POST'])
def buy_porduct(id):
    post_id = ObjectId(request.form['post_id'])
    amount = int(db.boards.find_one({'_id' : post_id})['quantity'])
    buy_amount = int(request.form['purchase_amount'])
    update_amount = amount + buy_amount

    result = db.boards.update_one({'_id' : post_id},{"$set" : {"quantity" : update_amount}})
    if result.modified_count > 0:
        return jsonify({"result": "success", "message": "구매에 참여했습니다!!!"})
    else:
        return jsonify({"result": "fail", "message": "오류 발생으로 재시도 바랍니다."})
#01:16 추가
@app.route('/update_post', methods=['POST']) 
def Update_post():
    post_id = ObjectId(request.form['post_id']) 
    update_boards = request.form['update_boards']
    update_name = request.form['update_name']
    update_link = request.form['update_link']
    update_price = request.form['update_price']
    update_deadline = request.form['update_deadline']
    update_shipping = request.form['update_shipping']
    update_condition = request.form['update_condition']
    update_category = request.form['update_category']
    result = db.boards.update_one(
        {"_id": post_id},
        {"$set": {
            "board": update_boards,
            "name": update_name,
            "link": update_link,
            "price": update_price ,
            "deadline": update_deadline,
            "shipping": update_shipping,
            "condition": update_condition,
            "category": update_category }}
    )
    if result.modified_count > 0:
        return jsonify({"result": "success", "message": "수정되었습니다다!!!"})
    else:
        return jsonify({"result": "fail", "message": "오류 발생으로 재시도 바랍니다."})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)

