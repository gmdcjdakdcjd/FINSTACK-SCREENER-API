# database/connection.py
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker

import os

# 1. MariaDB 접속 및 커넥션 풀 설정
# 환경변수로부터 DB 접속 정보를 읽어오며, 값이 없을 경우 로컬 개발용 DB를 기본값으로 사용합니다.
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "0806")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "managingtest")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)

# 데이터베이스 세션을 생성하는 세션 팩토리입니다.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    # FastAPI 의존성 주입(Depends)을 위해 세션을 생명주기에 맞게 생성하고 반납하는 헬퍼 함수입니다.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
