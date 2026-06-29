# services/screener.py
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import text
from services.market_cap import get_market_cap_ranking

def run_screener_service(filters: list, db: Session, codes: list = None) -> list:
    # 수신된 필터 조건 목록 및 코드 풀 목록이 둘 다 비어있으면 즉시 빈 결과를 반환합니다.
    if not filters and not codes:
        return []
        
    filter_results = {}
    
    # 1단계: 시가총액 랭킹 조건(RANK_MARKET_CAP_...)이 존재하는지 먼저 확인하고 코드를 추출합니다.
    market_cap_filter = next((f for f in filters if f.startswith("RANK_MARKET_CAP_")), None)
    
    # 기본 코드 풀은 전달받은 codes 리스트로 1차 조율합니다.
    base_code_pool = list(codes) if codes else None
    
    if market_cap_filter:
        try:
            # 키값에서 숫자 부분 추출 (예: RANK_MARKET_CAP_100_KR -> 100)
            limit_val = int(market_cap_filter.split("RANK_MARKET_CAP_")[1].split("_")[0])
        except Exception:
            limit_val = 100
        
        # 시총 상위 랭킹 종목 코드 리스트 조회
        ranked_codes = get_market_cap_ranking(limit_val, db)
        
        if base_code_pool is not None:
            # 전달받은 ETF 코드군과 시총 랭킹 결과의 교집합을 구하여 탐색 풀을 압축합니다.
            ranked_set = set(ranked_codes)
            base_code_pool = [c for c in base_code_pool if c in ranked_set]
        else:
            base_code_pool = ranked_codes

    # 2단계: 일반 조건식이 전혀 없고 코드 풀만 획득된 경우 (ETF 단독 검색 시)
    normal_filters = [f for f in filters if not f.startswith("RANK_MARKET_CAP_")]
    
    if not normal_filters and not market_cap_filter and base_code_pool is not None:
        if not base_code_pool:
            return []
            
        detail_query = text("""
            SELECT
                c.code,
                c.name,
                p.open,
                p.high,
                p.low,
                p.close,
                p.volume,
                (COALESCE(c.listed_stock_count, 0) * p.close) AS market_cap
            FROM company_info_kr c
            JOIN (
                SELECT *
                FROM daily_price_kr
                WHERE date = (SELECT MAX(date) FROM daily_price_kr)
            ) p ON c.code = p.code
            WHERE c.code IN :code_list
            ORDER BY market_cap DESC
        """)
        cursor = db.execute(detail_query, {"code_list": tuple(base_code_pool)})
        keys = cursor.keys()
        results = []
        for row in cursor.fetchall():
            row_dict = dict(zip(keys, row))
            code_val = row_dict.get("code") or ""
            if not code_val:
                continue
            results.append({
                "code": code_val,
                "name": row_dict.get("name") or "",
                "currentPrice": float(row_dict.get("close", 0.0) if row_dict.get("close") is not None else 0.0),
                "high": float(row_dict.get("high", 0.0) if row_dict.get("high") is not None else 0.0),
                "low": float(row_dict.get("low", 0.0) if row_dict.get("low") is not None else 0.0),
                "close": float(row_dict.get("close", 0.0) if row_dict.get("close") is not None else 0.0),
                "marketCap": int(row_dict.get("market_cap", 0) if row_dict.get("market_cap") is not None else 0)
            })
        return results

    try:
        # 일반 조건식이 있지만, 이미 조율된 탐색용 코드 풀이 비어있다면 결과가 있을 수 없으므로 즉시 리턴
        if normal_filters and base_code_pool is not None and not base_code_pool:
            return []

        for action_key in normal_filters:
            current_filter_data = {}
            
            # 일반 조건식 쿼리 조립: 시총이나 ETF 등으로 1차 조율된 base_code_pool이 있으면 IN 조건으로 대폭 스캔 대상을 압축합니다.
            query_str = """
                SELECT 
                    sd.code, 
                    sd.name, 
                    dp.open, 
                    dp.high, 
                    dp.low, 
                    dp.close, 
                    dp.volume,
                    (COALESCE(c.listed_stock_count, 0) * dp.close) AS market_cap
                FROM strategy_detail sd
                JOIN daily_price_kr dp ON sd.code = dp.code AND dp.date = sd.signal_date
                LEFT JOIN company_info_kr c ON sd.code = c.code
                WHERE sd.action LIKE :action_key
                  AND sd.signal_date = (
                      SELECT MAX(signal_date) 
                      FROM strategy_detail 
                      WHERE action LIKE :action_key
                  )
            """
            
            if base_code_pool is not None:
                query_str += " AND sd.code IN :code_list"
                
            detail_query = text(query_str)
            params = {"action_key": action_key}
            if base_code_pool is not None:
                params["code_list"] = tuple(base_code_pool) if base_code_pool else ("",)
                
            cursor = db.execute(detail_query, params)
            keys = cursor.keys()
            
            for row in cursor.fetchall():
                row_dict = dict(zip(keys, row))
                code_val = row_dict.get("code") or ""
                if not code_val:
                    continue
                    
                name_val = row_dict.get("name") or ""
                current_price = float(row_dict.get("close", 0.0) if row_dict.get("close") is not None else 0.0)
                high_val = float(row_dict.get("high", 0.0) if row_dict.get("high") is not None else 0.0)
                low_val = float(row_dict.get("low", 0.0) if row_dict.get("low") is not None else 0.0)
                close_val = float(row_dict.get("close", 0.0) if row_dict.get("close") is not None else 0.0)
                market_cap = int(row_dict.get("market_cap", 0) if row_dict.get("market_cap") is not None else 0)

                current_filter_data[code_val] = {
                    "code": code_val,
                    "name": name_val,
                    "currentPrice": current_price,
                    "high": high_val,
                    "low": low_val,
                    "close": close_val,
                    "marketCap": market_cap
                }
                
            if not current_filter_data:
                return []
                
            filter_results[action_key] = current_filter_data

        # 일반 조건식 없이 시총 조건만 선택한 경우
        if not normal_filters and market_cap_filter and base_code_pool:
            current_filter_data = {}
            detail_query = text("""
                SELECT
                    c.code,
                    c.name,
                    p.open,
                    p.high,
                    p.low,
                    p.close,
                    p.volume,
                    (COALESCE(c.listed_stock_count, 0) * p.close) AS market_cap
                FROM company_info_kr c
                JOIN (
                    SELECT *
                    FROM daily_price_kr
                    WHERE date = (SELECT MAX(date) FROM daily_price_kr)
                ) p ON c.code = p.code
                WHERE c.code IN :code_list
                ORDER BY market_cap DESC
            """)
            cursor = db.execute(detail_query, {"code_list": tuple(base_code_pool)})
            keys = cursor.keys()
            
            for row in cursor.fetchall():
                row_dict = dict(zip(keys, row))
                code_val = row_dict.get("code") or ""
                if not code_val:
                    continue
                
                name_val = row_dict.get("name") or ""
                current_price = float(row_dict.get("close", 0.0) if row_dict.get("close") is not None else 0.0)
                high_val = float(row_dict.get("high", 0.0) if row_dict.get("high") is not None else 0.0)
                low_val = float(row_dict.get("low", 0.0) if row_dict.get("low") is not None else 0.0)
                close_val = float(row_dict.get("close", 0.0) if row_dict.get("close") is not None else 0.0)
                market_cap = int(row_dict.get("market_cap", 0) if row_dict.get("market_cap") is not None else 0)

                current_filter_data[code_val] = {
                    "code": code_val,
                    "name": name_val,
                    "currentPrice": current_price,
                    "high": high_val,
                    "low": low_val,
                    "close": close_val,
                    "marketCap": market_cap
                }
            filter_results[market_cap_filter] = current_filter_data

        if not filter_results:
            return []
            
        # 모든 필터의 종목 코드 세트(Set) 목록을 추출합니다.
        code_sets = [set(res.keys()) for res in filter_results.values()]
        
        # 첫 번째 필터의 종목 코드 목록을 기준으로 다른 필터들과의 교집합(Intersection)을 연산합니다.
        common_codes = code_sets[0]
        for s in code_sets[1:]:
            common_codes = common_codes.intersection(s)
            
        # 교집합에 해당하는 종목의 상세 정보 데이터만 최종 결과에 담아 반환합니다.
        first_filter_key = list(filter_results.keys())[0]
        first_filter_data = filter_results[first_filter_key]
        
        results = [first_filter_data[code] for code in common_codes]
        
        # 화면에 시가총액이 가장 높은 순으로 내림차순 정렬을 수행합니다.
        results.sort(key=lambda x: x.get("marketCap", 0), reverse=True)
        
        return results
        
    except Exception as e:
        # 비즈니스 로직 및 쿼리 과정에서 에러 발생 시 예외를 호출자(라우터)로 전달합니다.
        print("Screener Service Error:", str(e))
        raise e
