"""
FastAPI 메인 - Render 배포 대응
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv

from model.database import init_db
from router import google_auth

load_dotenv()

app = FastAPI(
    title="Google OAuth2 API",
    description="FastAPI + React OAuth2 Integration",
    version="1.0.0"
)

# ========================================
# 환경 변수
# ========================================
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev-session-secret")
ENV = os.getenv("ENV", "development")

print(f"🌍 환경: {ENV}")
print(f"🔗 프론트엔드 URL: {FRONTEND_URL}")

# ========================================
# SessionMiddleware (필수!)
# ========================================
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    session_cookie="session",
    max_age=3600,
    same_site="none" if ENV == "production" else "lax",  # 🔥 배포 시 "none"
    https_only=True if ENV == "production" else False    # 🔥 배포 시 True
)

# ========================================
# CORS 설정
# ========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",  # 로컬 개발용
    ],
    allow_credentials=True,  # 🔥 쿠키 허용 (필수!)
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# DB 초기화
# ========================================
print("🔄 데이터베이스 초기화...")
init_db()
print("✅ 데이터베이스 초기화 완료!")

# ========================================
# 라우터 등록
# ========================================
app.include_router(google_auth.router)

# ========================================
# 헬스 체크
# ========================================
@app.get("/")
def root():
    return {
        "status": "healthy",
        "message": "Google OAuth2 API",
        "environment": ENV,
        "endpoints": {
            "login": "/auth/google/login",
            "callback": "/auth/google/callback",
            "me": "/auth/me",
            "logout": "/auth/logout"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# ========================================
# 개발 서버 실행
# ========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )