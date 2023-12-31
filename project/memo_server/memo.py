from http import HTTPStatus
import random
import requests
import json
import urllib
import logging
import os

from redis import StrictRedis
from flask import abort, Flask, make_response, render_template, Response, redirect, request, jsonify

app = Flask(__name__)

with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

naver_client_id = config_data.get('naver_client_id')
naver_client_secret = config_data.get('naver_client_secret')
naver_redirect_uri = config_data.get('naver_redirect_uri')
redis_ip_address = config_data.get('redis_ip_address')
redis_port = config_data.get('redis_port')

redis_client = StrictRedis(host=redis_ip_address, port=redis_port, db=0)
'''
  본인 app 의 것으로 교체할 것.
  여기 지정된 url 이 http://localhost:8000/auth 처럼 /auth 인 경우
  아래 onOAuthAuthorizationCodeRedirected() 에 @app.route('/auth') 태깅한 것처럼 해야 함
'''

@app.route('/')
def home():
    # 쿠기를 통해 이전에 로그인 한 적이 있는지를 확인한다.
    # 이 부분이 동작하기 위해서는 OAuth 에서 access token 을 얻어낸 뒤
    # user profile REST api 를 통해 유저 정보를 얻어낸 뒤 'userId' 라는 cookie 를 지정해야 된다.
    # (참고: 아래 onOAuthAuthorizationCodeRedirected() 마지막 부분 response.set_cookie('userId', user_id) 참고)
    userId = request.cookies.get('userId', default=None)

    ####################################################
    # TODO: 아래 부분을 채워 넣으시오.
    # userId 로부터 DB 에서 사용자 이름을 얻어오는 코드를 여기에 작성해야 함
    name = None
    if(userId):
        name_value = redis_client.get(userId)
            if name_value: 
                name = name_value.decode('utf8')
    ####################################################

    # 이제 클라에게 전송해 줄 index.html 을 생성한다.
    # template 로부터 받아와서 name 변수 값만 교체해준다.
    return render_template('index.html', name=name)


# 로그인 버튼을 누른 경우 이 API 를 호출한다.
# OAuth flow 상 브라우저에서 해당 URL 을 바로 호출할 수도 있으나,
# 브라우저가 CORS (Cross-origin Resource Sharing) 제약 때문에 HTML 을 받아온 서버가 아닌 곳에
# HTTP request 를 보낼 수 없는 경우가 있다. (예: 크롬 브라우저)
# 이를 우회하기 위해서 브라우저가 호출할 URL 을 HTML 에 하드코딩하지 않고,
# 아래처럼 서버가 주는 URL 로 redirect 하는 것으로 처리한다.
#
# 주의! 아래 API 는 잘 동작하기 때문에 손대지 말 것

@app.route('/login')
def onLogin():
    params = {
            'response_type': 'code',
            'client_id': naver_client_id,
            'redirect_uri': naver_redirect_uri,
            'state': random.randint(0, 10000)
        }
    urlencoded = urllib.parse.urlencode(params)
    url = f'https://nid.naver.com/oauth2.0/authorize?{urlencoded}'
    return redirect(url)


# 아래는 Redirect URI 로 등록된 경우 호출된다.
# 만일 본인의 Redirect URI 가 http://localhost:8000/auth 의 경우처럼 /auth 대신 다른 것을
# 사용한다면 아래 @app.route('/auth') 의 내용을 그 URL 로 바꿀 것
@app.route('/memo/auth')
def onOAuthAuthorizationCodeRedirected():
    # TODO: 아래 1 ~ 4 를 채워 넣으시오.

    # 1. redirect uri 를 호출한 request 로부터 authorization code 와 state 정보를 얻어낸다.
    authorization_code = request.args.get('code')
    state = request.args.get('state')

    print(f"authorization_code: {authorization_code}")
    print(f"state: {state}")

    # 2. authorization code 로부터 access token 을 얻어내는 네이버 API 를 호출한다.
    token_uri = "https://nid.naver.com/oauth2.0/token"
    token_params = {
        'grant_type' : 'authorization_code',
        'client_id' : naver_client_id,
        'client_secret' : naver_client_secret,
        'code' : authorization_code,
        'state' : state,
    }

    token_response = requests.post(token_uri, data = token_params)

    print(f"token_response: {token_response}")

    token_data = token_response.json()
    access_token = token_data.get('access_token')


    # 3. 얻어낸 access token 을 이용해서 프로필 정보를 반환하는 API 를 호출하고,
    #    유저의 고유 식별 번호를 얻어낸다.
    profile_url = "https://openapi.naver.com/v1/nid/me"
    headers = {
        'Authorization' : f'Bearer {access_token}',
    }
    profile_response = requests.get(profile_url, headers = headers)

    print(f"profile_response: {profile_response}")

    profile_data = profile_response.json()
    user_id = profile_data.get('response', {}).get('id')

    # 4. 얻어낸 user id 와 name 을 DB 에 저장한다.
    redis_client.set(user_id, profile_data.get('response', {}).get('name'))

    # 5. 첫 페이지로 redirect 하는데 로그인 쿠키를 설정하고 보내준다.
    response = redirect('/')
    response.set_cookie('userId', user_id)
    return response


@app.route('/memo', methods=['GET'])
def get_memos():
    # 로그인이 안되어 있다면 로그인 하도록 첫 페이지로 redirect 해준다.
    userId = request.cookies.get('userId', default=None)

    print(f"userId: {userId}")

    if not userId:
        return redirect('/')

    # TODO: DB 에서 해당 userId 의 메모들을 읽어오도록 아래를 수정한다.
    user_memos_key = f'user:{userId}:memos'
    memos = redis_client.lrange(user_memos_key, 0, -1)
    memos = [memo.decode('utf8') for memo in memos]

    print(f"memos: {memos}")

    # memos라는 키 값으로 메모 목록 보내주기
    return jsonify({'memos': memos or []})


@app.route('/memo', methods=['POST'])
def post_new_memo():
    # 로그인이 안되어 있다면 로그인 하도록 첫 페이지로 redirect 해준다.
    userId = request.cookies.get('userId', default=None)
    if not userId:
        return redirect('/')

    # 클라이언트로부터 JSON 을 받았어야 한다.
    if not request.is_json:
        abort(HTTPStatus.BAD_REQUEST)

    # TODO: 클라이언트로부터 받은 JSON 에서 메모 내용을 추출한 후 DB에 userId 의 메모로 추가한다.
    memo_content = request.json.get('text')

    print(f"memo_content: {memo_content}")

    user_memos_key = f'user:{userId}:memos'
    redis_client.rpush(user_memos_key, memo_content)

    return '', HTTPStatus.OK

if __name__ == '__main__':
    app.run('0.0.0.0', port=8000, debug=True)