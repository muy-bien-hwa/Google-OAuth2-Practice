"""
Google OAuth 라우터 - Part 1: 구글로 보내기
사용자를 구글 로그인 페이지로 리다이렉트합니다.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
import os
import secrets
import requests
from sqlalchemy.orm import Session
import urllib.parse
from dotenv import load_dotenv
from model.database import get_db, User
from auth_utils import create_access_token, verify_token

load_dotenv()

# 라우터 생성 (URL 앞에 /auth가 자동으로 붙음)
router = APIRouter(
    prefix="/auth", 
    tags=["auth"]
)

# 환경 변수에서 구글 설정 가져오기
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# 구글이 로그인 후 돌아올 주소 (우리 백엔드)
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"

# 구글 OAuth 인증 URL
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get("/google/login")
def google_login(request: Request):
    """
    1️⃣ 사용자를 구글 로그인 페이지로 보내는 엔드포인트
    
    흐름:
    1. CSRF 공격 방지를 위한 state 생성
    2. state를 세션에 저장
    3. 구글 OAuth URL 생성
    4. 구글로 리다이렉트 (302)
    
    사용자가 보는 것:
    - 구글 로그인 페이지로 이동
    - "이 앱이 당신의 이메일, 프로필에 접근하려고 해요" 화면
    """
    
    # ========================================
    # 1. CSRF 방어: state 토큰 생성
    # ========================================
    # 👉 state는 랜덤 문자열로, 나중에 구글이 돌려줄 때
    #    "진짜 우리가 보낸 요청인지" 확인하는 용도
    state = secrets.token_urlsafe(16)  # 예: "xJ4k2_Lm9pQ3rT8v"
    
    # 세션에 state 저장 (나중에 비교할 예정)
    # 👉 SessionMiddleware가 필요한 이유!
    request.session["oauth_state"] = state
    
    
    # ========================================
    # 2. 구글 OAuth URL 파라미터 설정
    # ========================================
    params = {
        # 구글 클라이언트 ID (누가 요청하는지)
        "client_id": GOOGLE_CLIENT_ID,
        
        # 응답 타입: authorization code 방식
        # 👉 구글이 code를 주면, 우리가 그걸로 토큰을 받아옴
        "response_type": "code",
        
        # 요청할 권한 범위
        # openid: 구글 로그인 기본
        # email: 이메일 주소
        # profile: 이름, 프로필 사진
        "scope": "openid email profile",
        
        # 구글이 로그인 후 돌아올 주소 (우리 백엔드)
        # ⚠️ 반드시 Google Cloud Console에 등록된 주소와 정확히 일치!
        "redirect_uri": GOOGLE_REDIRECT_URI,
        
        # CSRF 방어용 state
        "state": state,
        
        # access_type: offline
        # 👉 refresh token도 받을 수 있음 (선택사항)
        "access_type": "offline",
        
        # prompt: consent
        # 👉 매번 권한 동의 화면 표시 (선택사항)
        "prompt": "consent",
    }
    
    
    # ========================================
    # 3. URL 생성 및 리다이렉트
    # ========================================
    # URL 인코딩: 특수문자를 URL에 사용 가능한 형태로 변환
    # 예: "openid email profile" → "openid+email+profile"
    query_string = urllib.parse.urlencode(params)
    
    # 최종 URL 조합
    # 예: https://accounts.google.com/o/oauth2/v2/auth?client_id=...&response_type=code&...
    google_oauth_url = GOOGLE_AUTH_URL + "?" + query_string
    
    print(f"🔗 구글로 리다이렉트: {google_oauth_url}")
    print(f"🔑 생성된 state: {state}")
    
    # 구글 로그인 페이지로 리다이렉트 (HTTP 302)
    return RedirectResponse(google_oauth_url)


# ========================================
# 💡 흐름 정리
# ========================================
# 
# 사용자 브라우저에서 일어나는 일:
# 
# 1. 프론트엔드에서 "구글 로그인" 버튼 클릭
#    👇
# 2. http://localhost:8000/auth/google/login 접속
#    👇
# 3. 이 함수 실행 → 구글 URL로 리다이렉트
#    👇
# 4. 구글 로그인 페이지 표시
#    - "Google로 계속하기"
#    - "이 앱이 다음 권한을 요청합니다: 이메일, 프로필"
#    👇
# 5. 사용자가 "허용" 버튼 클릭
#    👇
# 6. 구글이 우리 백엔드로 돌려보냄 (다음 단계)
#    http://localhost:8000/auth/google/callback?code=xxx&state=xxx




@router.get("/google/callback")
def google_callback(
    code: str,          # 구글이 준 authorization code
    state: str,         # 구글이 돌려준 state (우리가 보냈던 것)
    request: Request,   # FastAPI Request 객체 (세션 접근용)
    db: Session = Depends(get_db)  # DB 세션
):
    """
    2️⃣ 구글에서 돌아온 콜백을 처리하는 엔드포인트
    
    구글이 보내주는 것:
    - code: authorization code (일회용 코드)
    - state: 우리가 보냈던 state
    
    해야 할 일:
    1. state 검증 (CSRF 방어)
    2. code → access_token 교환
    3. access_token으로 사용자 정보 조회
    4. DB에 저장 또는 업데이트
    5. 우리 서비스의 JWT 발급
    6. 프론트엔드로 리다이렉트 (쿠키에 JWT 담아서)
    """
    
    print(f"📨 구글 콜백 받음!")
    print(f"   - code: {code[:20]}... (일부만 표시)")
    print(f"   - state: {state}")
    
    
    # ========================================
    # 1️⃣ state 검증 (CSRF 공격 방어)
    # ========================================
    # 세션에 저장했던 state와 구글이 돌려준 state가 같은지 확인
    saved_state = request.session.get("oauth_state")
    
    if state != saved_state:
        print(f"❌ State 불일치! 저장: {saved_state}, 받음: {state}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid state parameter - CSRF 공격 가능성"
        )
    
    print(f"✅ State 검증 성공!")
    
    
    # ========================================
    # 2️⃣ code → access_token 교환
    # ========================================
    # 👉 이 단계는 반드시 백엔드에서만 해야 함!
    #    왜? client_secret이 필요하기 때문
    
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,  # 🔥 절대 프론트에 노출 금지!
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }
    
    print(f"🔄 구글에 토큰 요청 중...")
    
    try:
        # 구글 토큰 엔드포인트에 POST 요청
        token_response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
        token_response.raise_for_status()  # 에러 발생 시 예외 던지기
        token_json = token_response.json()
        
        print(f"✅ 토큰 받음!")
        
    except requests.RequestException as e:
        print(f"❌ 토큰 요청 실패: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to get access token: {str(e)}"
        )
    
    # access_token 추출
    access_token = token_json.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=400, 
            detail="No access token in response"
        )
    
    
    # ========================================
    # 3️⃣ access_token으로 사용자 정보 조회
    # ========================================
    print(f"🔄 사용자 정보 요청 중...")
    
    try:
        # 구글 UserInfo API 호출
        userinfo_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()
        
        print(f"✅ 사용자 정보 받음!")
        print(f"   - 이름: {userinfo.get('name')}")
        print(f"   - 이메일: {userinfo.get('email')}")
        
    except requests.RequestException as e:
        print(f"❌ 사용자 정보 요청 실패: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to get user info: {str(e)}"
        )
    
    # 필수 정보 추출
    google_id = userinfo.get("sub")        # 구글 고유 ID
    email = userinfo.get("email")          # 이메일
    name = userinfo.get("name")            # 이름
    picture = userinfo.get("picture")      # 프로필 사진 URL
    
    # 필수 정보 확인
    if not google_id or not email:
        raise HTTPException(
            status_code=400, 
            detail="Missing required user information from Google"
        )
    
    
    # ========================================
    # 4️⃣ DB에서 사용자 조회 또는 생성
    # ========================================
    print(f"🔄 DB에서 사용자 찾는 중... (google_id: {google_id})")
    
    # google_id로 기존 사용자 찾기
    user = db.query(User).filter(User.google_id == google_id).first()
    
    if not user:
        # 새 사용자 생성
        print(f"🆕 새 사용자 생성!")
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            picture=picture
        )
        db.add(user)
        db.commit()
        db.refresh(user)  # DB에서 ID 등 업데이트된 정보 가져오기
        
    else:
        # 기존 사용자 정보 업데이트
        print(f"✅ 기존 사용자 찾음! (ID: {user.id})")
        print(f"   정보 업데이트 중...")
        user.email = email
        user.name = name
        user.picture = picture
        db.commit()
    
    
    # ========================================
    # 5️⃣ 우리 서비스의 JWT 토큰 발급
    # ========================================
    print(f"🔄 JWT 토큰 생성 중...")
    
    jwt_token = create_access_token(
        data={
            "sub": str(user.id),      # 사용자 ID (subject)
            "email": user.email,       # 이메일
            "name": user.name          # 이름
        }
    )
    
    print(f"✅ JWT 토큰 생성 완료!")
    
    
    # ========================================
    # 6️⃣ 프론트엔드로 리다이렉트 (쿠키에 JWT 담기)
    # ========================================
    print(f"🔄 프론트엔드로 리다이렉트 중... ({FRONTEND_URL}/login/success)")
    
    # 프론트엔드의 성공 페이지로 리다이렉트
    response = RedirectResponse(f"{FRONTEND_URL}/login/success")
    
    # 쿠키에 JWT 토큰 설정
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,   # 🔒 JavaScript에서 접근 불가 (XSS 방어)
        secure=False,    # 🔒 개발: False, 프로덕션: True (HTTPS 필수)
        samesite="lax",  # 🔒 CSRF 방어
        max_age=3600     # 1시간 (초 단위)
    )
    
    # 세션에서 state 제거 (더 이상 필요 없음)
    request.session.pop("oauth_state", None)
    
    print(f"✅ 로그인 완료! 사용자 ID: {user.id}")
    
    return response


# ========================================
# 💡 전체 흐름 정리
# ========================================
# 
# 1. 사용자가 구글에서 로그인 & 권한 허용
#    👇
# 2. 구글이 /auth/google/callback?code=xxx&state=xxx 로 리다이렉트
#    👇
# 3. 이 함수 실행:
#    ① state 검증 (CSRF 방어)
#    ② code로 access_token 받기
#    ③ access_token으로 사용자 정보 받기
#    ④ DB에 저장/업데이트
#    ⑤ JWT 토큰 생성
#    👇
# 4. 프론트엔드 /login/success로 리다이렉트 (쿠키에 JWT 담아서)
#    👇
# 5. 프론트엔드에서 로그인 완료 처리




@router.get("/me")
def get_current_user(request: Request):
    """
    현재 로그인한 사용자 정보 조회
    
    흐름:
    1. 쿠키에서 access_token 추출
    2. JWT 토큰 검증
    3. 토큰에 담긴 사용자 정보 반환
    
    프론트엔드에서 호출:
    axios.get('/auth/me', { withCredentials: true })
    👉 withCredentials: true가 있어야 쿠키가 전송됨!
    """
    
    print(f"📨 /auth/me 요청 받음")
    
    # ========================================
    # 1. 쿠키에서 JWT 토큰 추출
    # ========================================
    # 쿠키는 request.cookies에 저장되어 있음
    access_token = request.cookies.get("access_token")
    
    print(f"   쿠키에서 토큰 추출: {'있음' if access_token else '없음'}")
    
    if not access_token:
        # 토큰이 없으면 인증되지 않은 사용자
        print(f"❌ 토큰 없음 - 인증 실패")
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated - No token found"
        )
    
    
    # ========================================
    # 2. JWT 토큰 검증
    # ========================================
    try:
        # auth_utils.py의 verify_token 함수 사용
        payload = verify_token(access_token)
        
        print(f"✅ 토큰 검증 성공!")
        print(f"   - 사용자 ID: {payload.get('sub')}")
        print(f"   - 이메일: {payload.get('email')}")
        
    except Exception as e:
        # 토큰이 만료되었거나 변조된 경우
        print(f"❌ 토큰 검증 실패: {e}")
        raise HTTPException(
            status_code=401, 
            detail=f"Invalid token: {str(e)}"
        )
    
    
    # ========================================
    # 3. 사용자 정보 반환
    # ========================================
    user_info = {
        "id": payload.get("sub"),      # 사용자 ID
        "email": payload.get("email"),  # 이메일
        "name": payload.get("name")     # 이름
    }
    
    return user_info





@router.post("/logout")
def logout():
    """
    로그아웃
    
    흐름:
    1. access_token 쿠키 삭제
    2. 프론트엔드 로그인 페이지로 리다이렉트
    
    프론트엔드에서 호출:
    axios.post('/auth/logout', {}, { withCredentials: true })
    """
    
    print(f"📨 로그아웃 요청 받음")
    
    # 프론트엔드 로그인 페이지로 리다이렉트
    response = RedirectResponse(f"{FRONTEND_URL}/login")
    
    # 쿠키 삭제
    # 👉 max_age=0으로 설정하면 즉시 삭제됨
    response.delete_cookie("access_token")
    
    print(f"✅ 쿠키 삭제 완료 - 로그아웃 성공")
    
    return response


# ========================================
# 💡 전체 흐름 정리
# ========================================
#
# /auth/me 엔드포인트:
# 1. 프론트엔드가 axios로 요청 (withCredentials: true)
#    👇
# 2. 브라우저가 자동으로 쿠키 포함해서 전송
#    👇
# 3. 백엔드가 쿠키에서 JWT 추출
#    👇
# 4. JWT 검증 (만료, 변조 확인)
#    👇
# 5. 사용자 정보 반환
#
# /auth/logout 엔드포인트:
# 1. 프론트엔드가 axios로 요청
#    👇
# 2. 백엔드가 쿠키 삭제
#    👇
# 3. 로그인 페이지로 리다이렉트