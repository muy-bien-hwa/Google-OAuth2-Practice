"""
FastAPI 메인 애플리케이션
모든 설정과 라우터를 연결합니다.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv

# 우리가 만든 모듈들
from model.database import init_db
from router import google_auth  # google_auth.py를 routers 폴더에 넣어야 함

load_dotenv()

# FastAPI 앱 생성
app = FastAPI(
    title="Google OAuth2 로그인 API",
    description="FastAPI + React Google OAuth2 통합 예제",
    version="1.0.0"
)


# ========================================
# 🔥 SessionMiddleware 설정 (필수!)
# ========================================
# OAuth state를 저장하기 위해 세션이 필요함
# 이게 없으면 "oauth_state" 저장/조회 불가!
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "your-session-secret-key"),
    # 세션 쿠키 설정
    session_cookie="session",
    max_age=3600,  # 1시간
    same_site="lax",
    https_only=False  # 개발 환경, 프로덕션에서는 True
)


# ========================================
# CORS 설정
# ========================================
# 프론트엔드(localhost:3000)에서 백엔드(localhost:8000) 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_credentials=True,  # 🔥 쿠키 전송 허용 (중요!)
    allow_methods=["*"],     # 모든 HTTP 메서드 허용
    allow_headers=["*"],     # 모든 헤더 허용
)


# ========================================
# 데이터베이스 초기화
# ========================================
# 앱 시작 시 테이블 생성
print("🔄 데이터베이스 초기화 중...")
init_db()
print("✅ 데이터베이스 초기화 완료!")


# ========================================
# 라우터 등록
# ========================================
# google_auth.py의 모든 엔드포인트를 /auth 경로에 등록
app.include_router(google_auth.router)


# ========================================
# 기본 엔드포인트
# ========================================
@app.get("/")
def root():
    """
    API 정보 및 사용 가능한 엔드포인트 목록
    """
    return {
        "message": "Google OAuth2 로그인 API",
        "version": "1.0.0",
        "endpoints": {
            "로그인": {
                "method": "GET",
                "path": "/auth/google/login",
                "description": "구글 로그인 페이지로 리다이렉트"
            },
            "콜백": {
                "method": "GET",
                "path": "/auth/google/callback",
                "description": "구글에서 돌아오는 콜백 (자동 처리)"
            },
            "사용자_정보": {
                "method": "GET",
                "path": "/auth/me",
                "description": "현재 로그인한 사용자 정보 조회"
            },
            "로그아웃": {
                "method": "POST",
                "path": "/auth/logout",
                "description": "로그아웃 (쿠키 삭제)"
            }
        },
        "사용법": {
            "1": "프론트엔드에서 /auth/google/login으로 이동",
            "2": "구글 로그인 완료 후 자동으로 프론트엔드로 리다이렉트",
            "3": "/auth/me로 사용자 정보 조회",
            "4": "/auth/logout으로 로그아웃"
        }
    }


@app.get("/health")
def health_check():
    """
    헬스 체크 엔드포인트
    서버가 정상 작동하는지 확인
    """
    return {"status": "healthy", "message": "서버 정상 작동 중"}


# ========================================
# 앱 실행 (개발 환경)
# ========================================
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 FastAPI 서버 시작!")
    print("=" * 60)
    print(f"📍 서버 주소: http://localhost:8000")
    print(f"📍 API 문서: http://localhost:8000/docs")
    print(f"📍 프론트엔드: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}")
    print("=" * 60)
    print()
    print("💡 사용 방법:")
    print("1. 프론트엔드에서 '구글 로그인' 버튼 클릭")
    print("2. http://localhost:8000/auth/google/login으로 이동")
    print("3. 구글 로그인 완료")
    print("4. 자동으로 프론트엔드 /login/success로 리다이렉트")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 코드 변경 시 자동 재시작
    )


# ========================================
# 💡 전체 흐름 정리
# ========================================
#
# 1. FastAPI 앱 생성
#    👇
# 2. SessionMiddleware 추가 (OAuth state 저장용)
#    👇
# 3. CORS 설정 (프론트엔드 접근 허용)
#    👇
# 4. DB 초기화 (users 테이블 생성)
#    👇
# 5. 라우터 등록 (/auth/google/login, /auth/google/callback, /auth/me, /auth/logout)
#    👇
# 6. 서버 실행 (http://localhost:8000)
#
# 실행 명령어:
# python main.py
# 또는
# uvicorn main:app --reload