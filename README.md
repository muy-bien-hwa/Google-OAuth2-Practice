# Google-OAuth2-Practice

## Render 서버 배포 중 발생 문제
■ Defalut Python 버전인 3.13 으로 구동되어서 SQLAlchemy 2.0.25 버전과 계속 충돌 일으킴.
- SQLAlchemy 2.0.25는 python 3.13 이상 버전과 호환이 안됨.
- .python-version 파일 생성 후 3.11.9 기입 -> deploy 다시 했는데 계속 defalut 버전으로 구동됨
- https://render.com/docs/python-version 의 1번 방법(환경 변수에 PYTHON_VERSION 직접 추가) 하고 Manual Deploy -> Clear build cache % Deploy 하니 해결됨.

■ PostgreSQL DB 서버가 local로 되어있어서 접근 못함 -> 에러
지금 네 설정 상태 요약

로그에 나온 걸 보면:

🌍 환경: development
백엔드 URL: http://localhost:8000


👉 Render에서 돌아가는데도 development + localhost 설정 그대로 씀
👉 이게 문제의 핵심

해결 방법 (택 1 아님, 순서대로 다 해야 함)
1️⃣ Render 전용 Postgres 써라 (정석)

Render 대시보드에서:

New → PostgreSQL

생성 후 Internal Database URL 복사

Render Web Service → Environment Variables

DATABASE_URL=postgresql://user:password@host:port/dbname


그리고 코드에서 무조건 이걸 쓰게 만들어라:

import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


❌ localhost
❌ 하드코딩
❌ .env만 믿기

2️⃣ init_db()를 앱 import 시점에 실행하지 마라 (중요)

지금 구조:

# main.py
init_db()  # ← 이게 서버 시작도 전에 실행됨


👉 Render에서는 DB 준비 타이밍 문제 + 장애 전파 다 생김

고쳐라
@app.on_event("startup")
def on_startup():
    init_db()


또는 더 안전하게:

try:
    init_db()
except Exception as e:
    print("DB init failed:", e)

3️⃣ 환경 분기 제대로 해라 (안 하면 또 터짐)
ENV = os.getenv("ENV", "development")

if ENV == "development":
    DATABASE_URL = "postgresql://localhost:5432/..."
else:
    DATABASE_URL = os.getenv("DATABASE_URL")


Render에서는:

ENV=production

결론 한 줄

Render에서 로컬 DB(localhost)에 붙이려 해서 앱이 시작도 못 하는 상태다.

이거 고치면:

uvicorn 정상 실행

OAuth고 뭐고 그 다음 단계로 감

원하면
👉 Render + FastAPI + SQLAlchemy 최소 정답 구조 바로 짜줄게.
