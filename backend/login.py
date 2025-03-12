import jwt
import requests
import datetime
from flask import Flask, redirect, request, jsonify, make_response, render_template
from pymongo import MongoClient

app = Flask(__name__)

# Flask JWT 설정
JWT_SECRET = "aldasfih254nsSIJSAfensDSEFS2151kSDAKIJF124sdklafe"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRY_DAYS = 30
REFRESH_TOKEN_EXPIRY_DAYS = 150

# Slack OAuth
SLACK_CLIENT_ID = "8599876682577.8592594742836"
SLACK_CLIENT_SECRET = "f1a7e812ae7f95efe8e4b2795a326851"
MAIN_URL = "https://7293-1-238-129-195.ngrok-free.app"
SLACK_REDIRECT_URI = f"{MAIN_URL}/oauth/callback"

# MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client.db_jungle
users_collection = db.users
tokens_collection = db.tokens

@app.route('/users/login')
def user_login():
    return render_template('login.html')

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
    response = make_response(redirect(MAIN_URL))
    response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite="Lax", max_age=ACCESS_TOKEN_EXPIRY_DAYS * 86400)  

    return response

def generate_token(user, token_expiry_days):
    payload = {
        "user_id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "exp": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=token_expiry_days)).timestamp(),
    }

    return jwt.encode(payload=payload, key=JWT_SECRET, algorithm=JWT_ALGORITHM)

app.run(host = '0.0.0.0', port = 5001, debug = 'True')