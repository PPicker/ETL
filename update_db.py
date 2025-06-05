"""
ppicker_category_setup.py
-------------------------------------------------
PostgreSQL + psycopg2 기반 3-단 카테고리 구축 스크립트
1) category / subcategory_synonym 테이블·인덱스 생성
2) C_MAP(3-단 트리)·syn_map(동의어) UPSERT
3) products.subcategory 정규화 + category FK/path 매핑
-------------------------------------------------
실행 방법:  python ppicker_category_setup.py
DB 접속 정보는 환경 변수 POSTGRES_* 로 주거나
conn_params 딕셔너리에 직접 기입하세요.
"""

import os
import psycopg2
from psycopg2 import sql
from config.env_loader import load_environment, load_db_config


# ── 3-단 카테고리 트리 (Root → Mid → Leaf, 모두 slug) ─────────────
C_MAP = {
    "top": {
        "tshirt":      ["short_sleeve_tshirt", "long_sleeve_tshirt",
                        "sleeveless_tshirt", "ringer_tshirt"],
        "shirt":       ["short_sleeve_shirt", "denim_shirt",
                        "chambray_shirt", "polo_shirt"],
        "knit":        ["knit", "henley_knit", "sweatshirt"],
        "cardigan":    ["cardigan"],
        "hoodie":      ["hoodie"],
        "vest":        ["vest"],
    },
    "bottom": {
        "pants":         ["pants", "slacks", "wide_pants"],
        "chino_pants":   ["chino_pants"],
        "denim_pants":   ["denim_pants"],
        "cargo_pants":   ["cargo_pants"],
        "fatigue_pants": ["fatigue_pants"],
        "shorts":        ["shorts", "cargo_shorts", "denim_shorts"],
    },
    "outer": {
        "jacket":   ["jacket", "souvenir_jacket", "liner_jacket",
                     "trucker_jacket", "harrington_jacket",
                     "hooded_jacket", "field_jacket", "zip_up_jacket"],
        "blouson":  ["blouson"],
        "blazer":   ["blazer"],
    },
    "accessory": {
        "belt":      ["belt"],
        "hat":       ["ball_cap"],
        "neckwear":  ["necktie"],
        "bag":       ["tote_bag", "shopper_bag"],
    },
}

# ── 동의어 사전: (왼쪽 = 원본 한글 alias, 오른쪽 = 영문 canonical Leaf) ──
syn_map = {
    # TOP ─────────────────────────────────────
    "티셔츠":               "tshirt",
    "베스트":               "vest",
    "후드티" :              "hoodie",
    "링거티":               "ringer_tshirt",
    "링거 티셔츠":           "ringer_tshirt",
    "긴팔 티셔츠":           "long_sleeve_tshirt",
    "롱 슬리브 티셔츠":       "long_sleeve_tshirt",
    "긴팔 브이넥 티셔츠":      "long_sleeve_tshirt",
    "하프 슬리브 티셔츠":      "short_sleeve_tshirt",
    "반팔 티셔츠":           "short_sleeve_tshirt",
    "스웻 셔츠" :           "sweatshirt",
    "스웻셔츠":              "sweatshirt",
    "니트 스웨터" :           "sweatshirt",
    "슬리브리스 티셔츠":      "sleeveless_tshirt",
    "민소매 티셔츠":          "sleeveless_tshirt",
    "슬리브리스" :             "sleeveless_tshirt",
    "tank top":             "sleeveless_tshirt",

    "셔츠" :               "shirt",
    "반팔 셔츠":             "short_sleeve_shirt",
    "반소매 셔츠":           "short_sleeve_shirt",
    "하프 슬리브 셔츠":       "short_sleeve_shirt",
    "숏 슬리브 셔츠":         "short_sleeve_shirt",
    "남성 반팔 셔츠":         "short_sleeve_shirt",
    "하프 셔츠":             "short_sleeve_tshirt",   # 티셔츠 계열


    "데님 셔츠":             "denim_shirt",
    "샴브레이 셔츠":          "chambray_shirt",
    "폴로 셔츠":             "polo_shirt",
    "폴로셔츠":             "polo_shirt",
    "니트 폴로 셔츠":          "polo_shirt",

    "니트웨어":              "knit",
    "스웨터":                "knit",
    "헨리넥 스웨터":           "henley_knit",

    "가디건" :             "cardigan",
    "니트 가디건":            "cardigan",

    "스웨트 셔츠":            "sweatshirt",
    "맨투맨 스웻셔츠":         "sweatshirt",
    "맨투맨/스웻셔츠":         "sweatshirt",
    "맨투맨/스웨트 셔츠":      "sweatshirt",

    # OUTER ──────────────────────────────────
    "자켓":                "jacket",
    "재킷":                 "jacket",
    "수베니어 자켓":          "souvenir_jacket",
    "라이너 자켓":            "liner_jacket",
    "트러커 재킷":            "trucker_jacket",
    "해링턴 자켓":            "harrington_jacket",
    "후드 재킷":              "hooded_jacket",
    "필드 재킷":              "field_jacket",
    "집업 자켓":              "zip_up_jacket",
    "블루종":                "blouson",
    "블루종/점퍼":            "blouson",
    "블레이저":              "blazer",

    # BOTTOM ─────────────────────────────────
    "팬츠":                 "pants",
    "청바지":              "denim_pants",
    "슬랙스":                "slacks",
    "트라우저":              "pants",
    "와이드 팬츠":            "wide_pants",
    "캐주얼 팬츠":            "pants",

    "치노 팬츠":              "chino_pants",
    "카고 팬츠":              "cargo_pants",
    "퍼티그 팬츠":            "fatigue_pants",
    "데님 팬츠":              "denim_pants",

    "반바지":                "shorts",
    "카고 쇼츠":              "cargo_shorts",
    "카고 반바지":            "cargo_shorts",
    "데님 쇼츠":              "denim_shorts",
    "쇼츠" :                "shorts",
    # ACCESSORY ─────────────────────────────
    "타이" :                "necktie",
    "넥타이":                "necktie",
    "토트백":                "tote_bag",
    "쇼퍼백":                "shopper_bag",
    "벨트":                 "belt",
    "볼캡":                 "ball_cap",
    "모자":                 "ball_cap",
}
# ── 3. 스키마 생성 SQL ──────────────────────────────
CREATE_SQL = """
CREATE EXTENSION IF NOT EXISTS ltree;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  

CREATE TABLE IF NOT EXISTS category (
    id        SERIAL PRIMARY KEY,
    name      TEXT UNIQUE NOT NULL,
    parent_id INT REFERENCES category(id) ON DELETE CASCADE,
    path      LTREE NOT NULL                    -- Python 에서 계산
);

CREATE INDEX IF NOT EXISTS cat_path_gist
    ON category USING GIST (path);

CREATE TABLE IF NOT EXISTS subcategory_synonym (
    alias        TEXT PRIMARY KEY,
    category_id  INT NOT NULL REFERENCES category(id)
);

CREATE INDEX IF NOT EXISTS syn_trgm
    ON subcategory_synonym USING GIN (alias gin_trgm_ops);

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS category_id   INT,
    ADD COLUMN IF NOT EXISTS category_path LTREE;

CREATE INDEX IF NOT EXISTS prod_cat_path_gist
    ON products USING GIST (category_path);
"""

# ── 4. 카테고리·동의어 UPSERT 함수 ─────────────────

def insert_category(cur, name: str, parent_id: int | None, parent_path: str | None):
    """카테고리 삽입(있으면 조회) → (id, path) 반환"""
    path_val = f"{parent_path}.{name}" if parent_path else name
    cur.execute(
        """
        INSERT INTO category (name, parent_id, path)
        VALUES (%s, %s, %s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id, path
        """,
        (name, parent_id, path_val),
    )
    if cur.rowcount:
        return cur.fetchone()  # 새로 삽입
    cur.execute("SELECT id, path FROM category WHERE name=%s", (name,))
    return cur.fetchone()

def upsert_categories(cur, cmap):
    for root, mids in cmap.items():
        root_id, root_path = insert_category(cur, root, None, None)
        for mid, leafs in mids.items():
            mid_id, mid_path = insert_category(cur, mid, root_id, root_path)
            for leaf in leafs:
                insert_category(cur, leaf, mid_id, mid_path)

def upsert_synonyms(cur, mapping):
    for alias, canon in mapping.items():
        cur.execute("SELECT id FROM category WHERE name=%s", (canon,))
        res = cur.fetchone()
        if not res:
            raise ValueError(f"canonical '{canon}' not in category table")
        cat_id = res[0]
        cur.execute(
            """
            INSERT INTO subcategory_synonym(alias, category_id)
            VALUES (%s, %s)
            ON CONFLICT(alias) DO UPDATE SET category_id = EXCLUDED.category_id
            """,
            (alias, cat_id),
        )

# ── 5. 정규화·매핑 쿼리 ────────────────────────────
NORMALIZE_SQL = """
UPDATE products p
SET    subcategory = c.name
FROM   subcategory_synonym s
JOIN   category c ON c.id = s.category_id
WHERE  p.subcategory = s.alias
  AND  p.subcategory <> c.name;
"""

MAP_SQL = """
UPDATE products p
SET    category_id   = c.id,
       category_path = c.path
FROM   category c
WHERE  p.subcategory = c.name
  AND  (p.category_id IS NULL OR p.category_id <> c.id);
"""

# ── 6. main 흐름 ───────────────────────────────────
def main():
    with psycopg2.connect(**load_db_config()) as conn:
        with conn.cursor() as cur:
            print("▶ 스키마 생성/업데이트")
            cur.execute(CREATE_SQL)

            print("▶ category 트리 UPSERT")
            upsert_categories(cur, C_MAP)

            print("▶ synonym UPSERT")
            upsert_synonyms(cur, syn_map)

            print("▶ products.subcategory 정규화")
            cur.execute(NORMALIZE_SQL)

            print("▶ products.category_id / path 매핑")
            cur.execute(MAP_SQL)

        conn.commit()
    print("✅ 완료!")


if __name__ == "__main__":
    load_environment()
    main()