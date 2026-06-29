# services/market_cap.py
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import text

def get_market_cap_ranking(limit_val: int, db: Session) -> list:
    """
    실시간으로 한국 주식 시장(KR)의 시가총액을 계산하고 
    상위 순위(limit_val)에 해당하는 종목 코드(code) 리스트만 추출하여 반환합니다.
    (시총 연산 및 랭킹 정렬 필터링 책임만 담당합니다.)
    """
    detail_query = text(f"""
        SELECT
            c.code
        FROM company_info_kr c
        JOIN (
            SELECT *
            FROM daily_price_kr
            WHERE date = (SELECT MAX(date) FROM daily_price_kr)
        ) p ON c.code = p.code
        ORDER BY (COALESCE(c.listed_stock_count, 0) * p.close) DESC
        LIMIT {limit_val}
    """)
    
    cursor = db.execute(detail_query)
    # 종목 코드 문자열 배열만 추출하여 반환합니다.
    return [row[0] for row in cursor.fetchall()]
