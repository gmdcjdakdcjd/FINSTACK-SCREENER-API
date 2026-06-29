# api/screener.py
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from database.connection import get_db
from services.screener import run_screener_service

# APIRouter 인스턴스를 생성합니다. (prefix와 tags를 통해 분류 관리)
router = APIRouter(
    prefix="/api/screener",
    tags=["screener"]
)

# 스크리너 필터 데이터를 수신하여 DB에서 교집합 결과를 조회하는 엔드포인트입니다.
@router.post("/run")
def run_screener(payload: dict, db: Session = Depends(get_db)):
    # React로부터 수신된 필터 키 리스트 및 선택 사항인 종목 코드 풀 리스트
    filters = payload.get("filters", [])
    codes = payload.get("codes", [])
    print("FastAPI 라우터 수신 필터 데이터:", filters)
    print("FastAPI 라우터 수신 종목 코드 풀:", len(codes), "개")
    
    try:
        # 서비스 레이어에 비즈니스 로직을 위임하여 교집합 결과를 획득합니다.
        results = run_screener_service(filters, db, codes)
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"데이터베이스 조회 및 스크리닝 연산 오류: {str(e)}"
        }
