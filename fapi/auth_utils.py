"""
JWT 토큰 생성 및 검증 유틸리티
구글 로그인 성공 후, 우리 서비스의 JWT 토큰을 만듭니다.
"""

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()

# .env 파일에서 설정 가져오기
SECRET_KEY = os.getenv("SECRET_KEY")  # JWT 암호화 키
ALGORITHM = "HS256"  # 암호화 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 토큰 유효 시간 (1시간)


def create_access_token(data: dict):
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 담을 정보 (예: user_id, email 등)
        
    Returns:
        JWT 토큰 문자열
        
    예시:
        token = create_access_token({"sub": "123", "email": "user@example.com"})
    """
    # 토큰에 담을 데이터를 복사 (원본 변경 방지)
    to_encode = data.copy()
    
    # 만료 시간 계산 (현재 시간 + 1시간)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 만료 시간을 데이터에 추가
    to_encode.update({"exp": expire})
    
    # JWT 토큰 생성 (암호화)
    # 👉 SECRET_KEY로 암호화하므로, 같은 키가 없으면 해독 불가
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str):
    """
    JWT 토큰 검증 및 정보 추출
    
    Args:
        token: 검증할 JWT 토큰
        
    Returns:
        토큰에 담긴 정보 (dict)
        
    Raises:
        JWTError: 토큰이 유효하지 않은 경우
    """
    try:
        # 토큰 해독 (SECRET_KEY로 검증)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # JWT 만료 여부는 jwt.decode() 가 자동으로 검사함.
        return payload
    except JWTError as e:
        # 토큰이 만료되었거나, 변조되었거나, 잘못된 경우
        raise Exception(f"Invalid token: {str(e)}")
