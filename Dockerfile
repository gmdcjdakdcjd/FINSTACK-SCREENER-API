# 베이스 이미지로 가벼운 파이썬 3.10-slim 이미지 사용
FROM python:3.10-slim

# 가동 중 파이썬 로그가 버퍼링 없이 즉시 출력되도록 설정
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 라이브러리 업데이트 및 빌드에 필요한 최소 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 전체 복사
COPY . .

# FastAPI 서버가 리슨하는 8000번 포트 노출
EXPOSE 8000

# 도커 환경에서 동작할 수 있도록 host를 0.0.0.0으로 지정하여 uvicorn 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
