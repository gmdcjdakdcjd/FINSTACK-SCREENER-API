# database/connection.py
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker

import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# 현재 connection.py 파일의 상위 디렉토리(프로젝트 루트) 경로를 구합니다.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 실행 시점의 APP_ENV 환경변수를 파악하여 설정 파일을 구분합니다.
# 기본 설정은 개발 환경인 'dev'로 지정됩니다.
APP_ENV = os.getenv("APP_ENV", "dev")

# 개발 환경('dev')인 경우에만 로컬의 .env.dev 파일을 읽어와 환경변수를 설정합니다.
# 운영 환경('real') 등에서는 Docker 컨테이너 구동 시 주입한 시스템 환경변수를 직접 활용합니다.
if APP_ENV == "dev":
    ENV_PATH = os.path.join(BASE_DIR, ".env.dev")
    if os.path.exists(ENV_PATH):
        load_dotenv(dotenv_path=ENV_PATH)


# 환경설정 파일 혹은 시스템 환경변수에서 DB 접속 정보를 읽어옵니다.
# 기존의 로컬 정보는 .env.dev 파일로 위임되었으므로 하드코딩된 기본값은 제거하였습니다.
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

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
