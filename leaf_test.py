"""
ppicker_backoff_search.py
----------------------------------------------------
카테고리 깊이에 따라 단계별(Leaf → Mid → Root)로
검색 범위를 넓혀 가며 최소 K개의 상품을 반환하는 모듈.

• slugify_cat()      : 세부 카테고리 문자열 → canonical slug
• get_category()     : slug → (path text, depth)
• fetch_with_backoff(): 백오프 로직으로 결과 조회

의존: psycopg2 (RealDictCursor), syn_map 사전, category/products 테이블
----------------------------------------------------
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from config.env_loader import load_environment, load_db_config


# --------- ② 유틸 함수들 --------------------------------
def slugify_cat(raw: str, mapping: dict) -> str:
    """alias → canonical slug (못 찾으면 그대로)"""
    return mapping.get(raw, raw).lower()

def get_category(cur, slug: str):
    """
    slug 로 category 레코드 찾기.
    Return (path_text, depth_int)  depth = 1(root)|2(mid)|3(leaf)
    """
    cur.execute(
        "SELECT path::text AS path, nlevel(path) AS depth "
        "FROM   category WHERE name = %s",
        (slug,)
    )
    rec = cur.fetchone()
    if not rec:
        raise ValueError(f"category '{slug}' not found in DB")
    return rec["path"], rec["depth"]

def fetch_with_backoff(cur, path_txt: str, depth: int, k_min: int = 40):
    """
    카테고리 경로만 이용해 Leaf→Mid→Root 단계별로 최소 k_min개까지 수집.
    """
    results = []
    parts   = path_txt.split(".")

    for d in range(depth, 0, -1):          # 3 → 2 → 1
        target_path = ".".join(parts[:d])
        op = "=" if d == 3 else "<@"       # leaf =, 상위는 <@

        sql = (
            "SELECT id, name, original_price, category_path "
            "FROM   products "
            f"WHERE  category_path {op} %s::ltree "
            "ORDER  BY created_at DESC "     # 정렬 기준은 원하는 필드로
            "LIMIT  %s"
        )
        params = [target_path, k_min]

        cur.execute(sql, params)
        fetched = cur.fetchall()

        # 중복 제거
        seen = {row["id"] for row in results}
        results.extend([r for r in fetched if r["id"] not in seen])

        if len(results) >= k_min:
            break

    return results[:k_min]


# --------- ③ 데모용 main ---------------------------------
if __name__ == "__main__":
    # (1) DB 접속 정보
    load_environment()  # 환경 변수 로드
    conn_info = load_db_config()

    # (2) 예시 사용자 쿼리
    user_query = {
        "category" : "top",
        "subcategory": "knit",      # 입력 세부 카테고리 (한글)
        "genre"    : "미니멀리즘",
        "silhouette": "오버사이즈",
        "k_min"    : 40
    }

    # (3) 실행
    with psycopg2.connect(**conn_info) as conn, \
         conn.cursor(cursor_factory=RealDictCursor) as cur:

        # 3-1. canonical slug 얻기
        # leaf_slug = user_query["subcategory"]

        # 3-2. path와 depth 조회
        path_text, depth = get_category(cur, "trucker_jacket")
        print(path_text,depth)
        # 3-3. 백오프 검색
        items = fetch_with_backoff(
            cur,
            path_text,
            depth,
            k_min=3
        )

        print(f"Returned {len(items)} items")
        for itm in items[:5]:
            print(itm)