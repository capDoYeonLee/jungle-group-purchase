from flask import Flask, render_template, jsonify, request
import requests, datetime
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.boards

@app.route('/')
def home():
    return render_template('index.html')  # 수정됨

@app.route('/product-detail/<id>', methods=['GET'])
def product_detail(id):
    product = db.boards.find_one({"_id": ObjectId(id)})
    if product:
        return render_template('product-detail.html', product=product)
    else:
        return jsonify({"result": "fail", "message": "상품을 찾을 수 없습니다."}), 404



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
            "title": product["name"],
            "price": f"{product['price']}원",
            "deadline": product["deadline"],
            "category": product["category"],
            "shipping": product["shipping"]
        }
        for product in result
    ]

    return jsonify({'result': 'success', 'products': formatted_products})

@app.route('/api/product', methods=['POST'])
def createProduct():
    product = {
        "board": request.form['title'],
        "name": request.form['item_name'],
        "link": request.form['item_url'],
        "price": request.form['item_price'],
        "deadline": request.form['deadline'],
        "shipping": request.form['delivery_fee'],
        "condition": request.form['free_delivery_cond'],
        "message": request.form['confirmation_msg'],
        "category": request.form['category'],
        "quantity": request.form['item_count'],
        "comments" : []
    }
    
    db.boards.insert_one(product)
    return jsonify({'result': 'success'})


@app.route('/find_product/<id>', methods=["GET"])
def find_product(id):
        product_id = ObjectId(id)  # 유효한 ObjectId로 변환
        product = db.boards.find_one({"_id": product_id})

        product["_id"] = str(product["_id"])  # _id를 문자열로 변환하여 반환
        return jsonify({"result": "success", "product": product})
   
   
@app.route('/new_comment', methods=['POST']) #id는 자동생성되는 친구 쓰는거로~
def New_comment():
    post_id = ObjectId(request.form['post_id'])  # 댓글을 추가할 게시글 ID
    #comment_author = 댓글 작성장의 슬렉 계정정
    text = request.form['text']

    comment = {
        "_id" : str(datetime.datetime.now(datetime.timezone.utc).timestamp()*1000),
        #'comment_author_id": comment_author,
        "text": text,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "updated_at": 0,
        "status" : 'valid',
        "replies": [],  # 대댓글 
        
    }

    # 게시글 컬렉션에 저장
    result = db.boards.update_one(
        {"_id": post_id},
        {"$push": {"comments": comment}}
    )

    if result.modified_count > 0:
        return jsonify({"result": "success", "message": "댓글이 추가되었습니다."})
    else:
        return jsonify({"result": "fail", "message": "게시글을 찾을 수 없습니다."})
    
@app.route('/read_comment/<id>', methods=["GET"])
def read_comment(id):
        product_id = ObjectId(id)  # 유효한 ObjectId로 변환
        products = db.boards.find_one({"_id": product_id})
        comments = products["comments"]
        for i in range(len(products["comments"])):
            comments[i]["_id"] = str(comments[i]["_id"])  # _id를 문자열로 변환하여 반환
        return jsonify({"result": "success", "response": comments})

@app.route('/Update_comment', methods=['POST']) 
def Update_comment():
    comment_id = request.form['comment_id']  
    text = request.form['update_text']

    result = db.boards.update_one(
        {"comments._id": comment_id},
        {"$set": {"comments.$.text": text, "comments.$.updated_at": datetime.datetime.now(datetime.timezone.utc)}}
    )



    if result.modified_count > 0:
        return jsonify({"result": "success", "message": "댓글이 수정되었습니다."})

@app.route('/delete_comment', methods=['POST']) 
def delete_comment():
    comment_id = request.form['comment_id']  
    result = db.boards.update_one(
        {"comments._id": comment_id },
        {"$set": {"comments.$.status": "deleted" }}
    )

    if result.modified_count > 0:
        return jsonify({"result": "success", "message": "댓글이 삭제되었습니다."})

@app.route('/New_reply', methods=['POST'])
def New_reply():
    post_id = ObjectId(request.form['post_id'])  # 게시글 ID
    comment_id = request.form['comment_id']  # 부모 댓글 ID
    # reply_author = 슬렉 계정 사용자
    text = request.form['text']

    new_reply = {
        "_id" : str(datetime.datetime.now(datetime.timezone.utc).timestamp()*1000),
        #"author_id": reply_author,
        "text": text,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "updated_at" : 0,
        "status" : 'valid'
    }

    result = db.boards.update_one(
        {"_id": post_id, "comments._id": comment_id},
        {"$push": { "comments.$.replies" : new_reply}}
    )

    if result.modified_count > 0:
        return jsonify({"result": "success", "message": "대댓글이 추가되었습니다."})
    else:
        return jsonify({"result": "fail", "message": "댓글을 찾을 수 없습니다."})
    
@app.route('/read_replies/<id>', methods=["GET"])
def read_replies(id):
        product_id = ObjectId(id)  # 유효한 ObjectId로 변환
        comment_id = request.form['comment_id']  # 부모 댓글 ID
        comments = db.boards.find_one({"_id" : product_id, "comments._id": comment_id})
        replies = comments["replies"]
        for i in range(len(replies)):
            replies[i]["_id"] = str(replies[i]["_id"])  # _id를 문자열로 변환하여 반환
        return jsonify({"result": "success", "response": replies})

@app.route('/Update_reply', methods=['POST'])
def Update_reply():
    post_id = ObjectId(request.form['post_id'])  # 게시글 ID
    comment_id = request.form['comment_id']  # 부모 댓글 ID
    reply_id = request.form['reply_id'] #대댓글 ID
    # reply_author = 슬렉 계정 사용자
    text = request.form['text'] # 수정된 대댓글글

    result = db.boards.update_one(
        {"_id" : post_id, "comments._id": comment_id, "comments.replies._id" : reply_id},
        {"$set": {
            "comments.$.replies.$[elem].text": text,
            "comments.$.replies.$[elem].updated_at": datetime.datetime.now(datetime.timezone.utc)
        }},
        array_filters=[{"elem._id": reply_id}]  
    )

    if result.modified_count > 0:
        return jsonify({"result": "success", "message": "대댓글이 수정정되었습니다."})
    
@app.route('/delete_reply', methods=['POST'])
def delete_reply():
    post_id = ObjectId(request.form['post_id'])
    comment_id = request.form['comment_id']
    reply_id = request.form['reply_id']

    result = db.boards.update_one(
        {"_id": post_id, "comments._id": comment_id, "comments.replies._id": reply_id},
        {"$set": {"comments.$.replies.$[elem].status": "deleted"}},
        array_filters=[{"elem._id": reply_id}]
    )

    if result.modified_count > 0:
        return jsonify({"result": "success", "message": "대댓글이 삭제되었습니다."})
    else:
        return jsonify({"result": "fail", "message": "대댓글을 찾을 수 없습니다."})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
