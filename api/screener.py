# api/screener.py
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from database.connection import get_db
from services.screener import run_screener_service
from services.screener_us import run_screener_us_service

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
        # 필터 목록 중에서 _US 접미사를 가진 해외 주식용 조건이 포함되어 있는지 판별합니다.
        is_us = any(f.endswith("_US") for f in filters)
        
        # 해외 주식용 조건이 있다면 미국 주식 스크리너 서비스를 호출하고, 그렇지 않다면 국내용을 호출합니다.
        if is_us:
            results = run_screener_us_service(filters, db, codes)
        else:
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
