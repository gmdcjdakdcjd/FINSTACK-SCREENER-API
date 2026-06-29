# pyrefly: ignore [missing-import]
from fastapi import FastAPI
from api.screener import router as screener_router

# FastAPI 인스턴스를 생성합니다.
app = FastAPI(
    title="Stock Screener API",
    description="실시간 주식 스크리닝 및 조건 검색 서비스를 제공하는 API 서버입니다.",
    version="1.0.0"
)

# 분리된 API 라우터를 메인 애플리케이션에 등록합니다.
app.include_router(screener_router)

@app.get("/")
def read_root():
    # 서버 작동 여부를 간단히 확인할 수 있는 기본 루트 엔드포인트입니다.
    return {"message": "FastAPI 주식 스크리너 서버가 성공적으로 작동하고 있습니다."}

# python main.py로 직접 실행할 때 서버를 구동하기 위한 엔트리 포인트입니다.
if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    # uvicorn 서버를 실행합니다. 8000번 포트를 사용하며 코드 변경 시 자동 재로딩됩니다.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
