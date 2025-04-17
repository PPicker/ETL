import os
import psycopg2
import psycopg2.extras
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime
from config.env_loader import load_db_config

# 환경 변수 로드
load_dotenv()
db_config = load_db_config()
# Notion API 클라이언트 설정
notion = Client(auth=os.environ.get("NOTION_API_TOKEN"))

# Notion 데이터베이스 ID
NOTION_BRAND_DB_ID = os.environ.get("NOTION_BRAND_DB_ID")

# PostgreSQL 연결 설정
conn = psycopg2.connect(
    **db_config
)
cursor = conn.cursor()

# ✅ 1. Notion 속성(schema) 불러오기
db_info = notion.databases.retrieve(database_id=NOTION_BRAND_DB_ID)
notion_schema = db_info["properties"]

# ✅ 2. PostgreSQL 테이블 데이터 불러오기
cursor.execute("SELECT * FROM brands;")
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

# ✅ 3. Notion 형식에 맞게 자동 매핑
def to_rich_text(val):
    return [{"type": "text", "text": {"content": str(val)}}] if val else []

def to_date(val):
    return {"start": val.isoformat()} if val else None

def to_properties(row_dict):
    props = {}

    # title 필드 자동 매핑
    title_col = next((k for k, v in notion_schema.items() if v["type"] == "title"), None)
    
    for key, val in row_dict.items():
        if key not in notion_schema:
            continue

        prop_type = notion_schema[key]["type"]

        if key == "name" and title_col:
            props[title_col] = {"title": to_rich_text(val)}
        elif prop_type == "rich_text":
            props[key] = {"rich_text": to_rich_text(val)}
        elif prop_type == "number":
            props[key] = {"number": val}
        elif prop_type == "date":
            props[key] = {"date": to_date(val)}
        elif prop_type == "checkbox":
            props[key] = {"checkbox": bool(val)}
        elif prop_type == "url":
            props[key] = {"url": str(val) if val else None}
        else:
            print(f"⚠️ '{key}' → 타입 '{prop_type}'은 아직 미지원 → 무시")

    return props

# ✅ 4. Notion에 데이터 삽입
print("📤 Notion에 row 삽입 시작...")
for row in rows:
    row_dict = dict(zip(columns, row))
    props = to_properties(row_dict)

    notion.pages.create(
        parent={"database_id": NOTION_BRAND_DB_ID},
        properties=props
    )

print("✅ 데이터 삽입 완료!")