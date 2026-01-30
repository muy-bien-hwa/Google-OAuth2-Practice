"""
데이터베이스 설정 및 User 모델 정의
구글로 로그인한 사용자 정보를 저장하는 테이블을 만듭니다.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 데이터베이스 파일 경로
# 👉 실제 프로덕션에서는 PostgreSQL, MySQL 등을 사용
DATABASE_URL = os.getenv("DATABASE_URL")

# 데이터베이스 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 만들기 (DB와 통신하는 창구)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모델의 기본 클래스
Base = declarative_base()


# 👤 User 테이블 정의
class User(Base):
    """
    구글 로그인 사용자 정보를 저장하는 테이블
    """
    __tablename__ = "users"

    # 기본 키 (자동 증가)
    id = Column(Integer, primary_key=True, index=True)
    
    # 구글 고유 ID (sub 필드)
    # 👉 같은 사람이 다시 로그인해도 이걸로 구분
    google_id = Column(String, unique=True, index=True, nullable=False)
    
    # 이메일 주소
    email = Column(String, unique=True, index=True, nullable=False)
    
    # 사용자 이름
    name = Column(String, nullable=True)
    
    # 프로필 사진 URL
    picture = Column(String, nullable=True)


def init_db():
    """
    데이터베이스 테이블 생성
    앱 시작할 때 한 번 실행
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    데이터베이스 세션을 가져오는 함수
    FastAPI의 Depends에서 사용
    
    사용 후 자동으로 닫아줌 (finally 블록)
    """
    db = SessionLocal()
    try:
        yield db  # 👈 이 부분에서 DB 세션을 전달
    finally:

        db.close()  # 👈 작업 끝나면 자동으로 닫기

