from flask import Flask, render_template, jsonify, request, redirect, make_response
import requests
from pymongo import MongoClient
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from TokenHandler import decode_token
import jwt
from bson import ObjectId

app = Flask(__name__)

# Flask JWT 설정
JWT_SECRET = "aldasfih254nsSIJSAfensDSEFS2151kSDAKIJF124sdklafe"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRY_DAYS = 30
REFRESH_TOKEN_EXPIRY_DAYS = 150

# Slack OAuth
SLACK_CLIENT_ID = "8599876682577.8592594742836"
SLACK_CLIENT_SECRET = "f1a7e812ae7f95efe8e4b2795a326851"
MAIN_URL = "https://91e5-1-238-129-195.ngrok-free.app"
SLACK_REDIRECT_URI = f"{MAIN_URL}/oauth/callback"


client = MongoClient('localhost', 27017)
db = client.boards
users_collection = db.users
tokens_collection = db.tokens


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index.html', methods=['GET'])
def getMainPage():
    return render_template('index.html')

@app.route('/create-product.html', methods=['GET'])
def getCreateProduct():
    return render_template('create-product.html')

@app.route('/login.html')
def user_login():
    return render_template('login.html')


@app.route('/product-detail/<id>', methods=['GET'])
def product_detail(id):
    print('here', id)
    product = db.boards.find_one({"_id": ObjectId(id)})
    if product:
        return render_template('product-detail.html', product=product)
    else:
        return jsonify({"result": "fail", "message": "상품을 찾을 수 없습니다."}), 404

@app.route('/find_product/<id>', methods=["GET"])
def find_product(id):
        product_id = ObjectId(id)  # 유효한 ObjectId로 변환
        product = db.boards.find_one({"_id": product_id})

        product["_id"] = str(product["_id"])  # _id를 문자열로 변환하여 반환
        return jsonify({"result": "success", "product": product})


''' 모든 상품 게시글 조회'''
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



'''상품 게시글 생성'''
@app.route('/api/product', methods=['POST'])
def createProduct():
    #userId = decode_token()
    #if not userId:
    #    return jsonify({'error': 'Invalid or missing token'}), 401


    board = request.form['title']
    name = request.form['item_name']
    link = request.form['item_url']
    price = request.form['item_price']
    deadline = request.form['deadline'] # 2025-03-03, YYYY-MM-DD
    shipping = request.form['delivery_fee']
    condition = request.form['free_delivery_cond']
    message = request.form['confirmation_msg']
    category = request.form['category']
    quantity = request.form['item_count']
    #ownerId = userId

    product = { 'board': board, 'name':name, 'link':link, 'price':price, 
                'deadline':deadline, 'shipping':shipping, 'condition':condition, 
                'message':message, 'category':category, 'quantity':quantity, 
                'ownerId' : "test" , 'participants': [], "expired": False}
    
    db.boards.insert_one(product)
    return jsonify({'result': 'success'})


'''마감일이 지난 상품 검색 -> 해당 메서드는 APScheduler를 통해 실행'''
def check_expired_products():
    """ 공동구매 마감된 게시글 찾고 상태 업데이트 """
    now = datetime.datetime.now()
    
    # 마감 기한이 지난 게시글 조회
    expired_products = db.boards.find({
    "deadline": {"$lt": datetime.strptime(now, "%Y-%m-%d")},
    "expired": {"$ne": True}})
    
    for product in expired_products:
        send_messageToparticipants(product)
        send_messageToOwner(product)
        db.boards.update_one(
            {"_id": product["_id"]},
            {"$set": {"expired": True}}
        )

''' 구매 희망 유저들에게 슬랙 디엠 전송 기능 '''
def send_messageToparticipants(product):
    slack_token = "추후 입력 예정"
    message = product['message']
    participants = product['participants']

    for userId in participants:
        data = {
            'token' : slack_token,
            'channel' : userId,
            'as_user' : True,
            'text' : message
        }
        requests.post(
            url='https://slack.com/api/chat.postMessage',
            data=data)

''' 상품 게시글 게시자에게 슬랙 디엠 전송 기능 '''
def send_messageToOwner(product):
    slack_token = "추후 입력 예정"
    total_quantity = product['quantity']
    total_price = int(product['price']) * int(product['quantity'])
    ownerId = product['ownerId']

    data = {
            'token' : slack_token,
            'channel' : ownerId,
            'as_user' : True,
            'text' : f"총 구매 금액은 {total_price}, 총 수량은 {total_quantity}"
    }
    
    requests.post(
            url='https://slack.com/api/chat.postMessage',
            data=data)


@app.route('/oauth')
def oauth():
    slack_auth_url = (
        "https://slack.com/oauth/v2/authorize?"
        f"client_id={SLACK_CLIENT_ID}"
        "&scope=&user_scope=email,openid,profile"
        f"&redirect_uri={SLACK_REDIRECT_URI}"
    )
    return redirect(slack_auth_url)


@app.route('/oauth/callback')
def oauth_callback(provider="slack"):
    # 유저가 전달한 authorization_code 수신
    code = request.args.get("code")
    if not code:
        return "Authorization failed", 400

    # Slack OAuth 서버에 Access Token 요청
    token_response = requests.post(
        "https://slack.com/api/oauth.v2.access",
        data = {
            "client_id": SLACK_CLIENT_ID,
            "client_secret": SLACK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": SLACK_REDIRECT_URI,
        }
    )

    token_data = token_response.json()
    if not token_data.get("ok"):
        return "OAuth 실패", 400
    
    access_token = token_data["authed_user"]["access_token"]

    # Access Token을 통해 유저 정보 가져오기
    user_info_response = requests.get(
        "https://slack.com/api/openid.connect.userInfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user_info = user_info_response.json()
    if not user_info.get("ok"):
        return "알 수 없는 유저입니다.", 400

    user = {"id": user_info.get("sub"),
            "name": user_info.get("name"), 
            "email": user_info.get("email")}
    
    # JWT token 발급
    access_token = generate_token(user, ACCESS_TOKEN_EXPIRY_DAYS)
    refresh_token = generate_token(user, REFRESH_TOKEN_EXPIRY_DAYS)

    # DB에 사용자 저장 
    users_collection.update_one(
        user,
        {"$set": {"token": refresh_token}},
        upsert=True
    )

    # 쿠키에 Access Token 저장 후 메인 페이지로 리디렉트
    response = make_response(redirect(MAIN_URL+"/index.html"))
    response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite="Lax", max_age=ACCESS_TOKEN_EXPIRY_DAYS * 86400)  

    return response # 기본 엔그록 url + index.html

def generate_token(user, token_expiry_days):
    payload = {
        "user_id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "exp": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=token_expiry_days)).timestamp(),
    }

    return jwt.encode(payload=payload, key=JWT_SECRET, algorithm=JWT_ALGORITHM)



if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_expired_products, 'cron', hour=0, minute=1)
    scheduler.start()
    app.run('0.0.0.0', port=5001, debug=True)
    

