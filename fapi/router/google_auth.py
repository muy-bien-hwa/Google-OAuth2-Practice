"""
Google OAuth 라우터 - Render 배포 대응 버전
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
import secrets
import urllib.parse
import requests
from dotenv import load_dotenv

from model.database import get_db, User
from auth_utils import create_access_token, verify_token

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

# ========================================
# 🔥 환경 변수로 URL 관리 (개발/배포 자동 전환)
# ========================================

# 구글 OAuth 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# 백엔드 URL (Render에서 자동으로 설정됨)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# 프론트엔드 URL
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# 구글 리다이렉트 URI (백엔드 URL 기반)
# 🔥 개발: http://localhost:8000/auth/google/callback
# 🔥 배포: https://your-app.onrender.com/auth/google/callback
GOOGLE_REDIRECT_URI = f"{BACKEND_URL}/auth/google/callback"

# 구글 OAuth URL
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# 시작 시 URL 확인 로그
print("=" * 60)
print("🔧 OAuth 설정 정보")
print("=" * 60)
print(f"백엔드 URL: {BACKEND_URL}")
print(f"프론트엔드 URL: {FRONTEND_URL}")
print(f"구글 리다이렉트 URI: {GOOGLE_REDIRECT_URI}")
print("=" * 60)


@router.get("/google/login")
def google_login(request: Request):
    """구글 로그인 페이지로 리다이렉트"""
    
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": GOOGLE_REDIRECT_URI,  # 🔥 환경에 따라 자동 변경
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    
    query_string = urllib.parse.urlencode(params)
    google_oauth_url = GOOGLE_AUTH_URL + "?" + query_string
    
    print(f"🔗 구글로 리다이렉트: {google_oauth_url}")
    
    return RedirectResponse(google_oauth_url)


@router.get("/google/callback")
def google_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """구글 콜백 처리"""
    
    print(f"📨 구글 콜백 받음!")
    
    # State 검증
    saved_state = request.session.get("oauth_state")
    if state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # 토큰 교환
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI,  # 🔥 환경에 따라 자동 변경
    }
    
    try:
        token_response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Token error: {str(e)}")
    
    access_token = token_json.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")
    
    # 사용자 정보 조회
    try:
        userinfo_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Userinfo error: {str(e)}")
    
    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name")
    picture = userinfo.get("picture")
    
    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Missing user info")
    
    # DB 저장/업데이트
    user = db.query(User).filter(User.google_id == google_id).first()
    
    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            picture=picture
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.email = email
        user.name = name
        user.picture = picture
        db.commit()
    
    # JWT 생성
    jwt_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "name": user.name
        }
    )
    
    # 프론트엔드로 리다이렉트
    response = RedirectResponse(f"{FRONTEND_URL}/login/success")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=True,  # 🔥 배포에서는 True (HTTPS)
        samesite="none",  # 🔥 배포에서는 "none" (다른 도메인 쿠키)
        max_age=3600
    )
    
    request.session.pop("oauth_state", None)
    
    print(f"✅ 로그인 완료! 사용자 ID: {user.id}")
    
    return response


@router.get("/me")
def get_current_user(request: Request):
    """현재 사용자 정보 조회"""
    
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = verify_token(access_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name")
    }


@router.post("/logout")
def logout():
    """로그아웃"""
    
    response = RedirectResponse(f"{FRONTEND_URL}/login")
    response.delete_cookie("access_token")
    
    return response