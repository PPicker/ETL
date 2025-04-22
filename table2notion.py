import psycopg2
from config.env_loader import load_db_config
from notion_client import Client
from dotenv import load_dotenv
import os

# ✅ .env 파일 로드
load_dotenv()
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

db_config = load_db_config()

# ✅ PostgreSQL 연결 설정
conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

# ✅ Notion 클라이언트 초기화
notion = Client(auth=NOTION_API_TOKEN)


# ✅ 헬퍼 함수: rich_text object
def text_cell(content: str):
    return [{"type": "text", "text": {"content": content}}]


# ✅ 1. 기존 페이지 블록 전체 삭제
def clear_all_blocks(page_id):
    children = notion.blocks.children.list(page_id).get("results", [])
    for block in children:
        block_id = block["id"]
        try:
            notion.blocks.delete(block_id)
        except Exception as e:
            print(f"⚠️ 블록 삭제 실패: {block_id} - {e}")


print("🧹 기존 블록 삭제 중...")
clear_all_blocks(NOTION_PAGE_ID)

# ✅ 2. public 스키마 테이블 목록 가져오기
cursor.execute(
    """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public';
"""
)
tables = cursor.fetchall()

# ✅ 3. 테이블 별로 Notion에 추가
for (table_name,) in tables:
    cursor.execute(
        f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = '{table_name}';
    """
    )
    columns = cursor.fetchall()

    # 📌 Heading 블록 추가
    notion.blocks.children.append(
        block_id=NOTION_PAGE_ID,
        children=[
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"📦 {table_name}"}}
                    ]
                },
            }
        ],
    )

    # 📌 Table 블록 구성
    table_block = {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": 2,
            "has_column_header": True,
            "has_row_header": False,
            "children": [],
        },
    }

    # 🔹 헤더 추가
    table_block["table"]["children"].append(
        {
            "object": "block",
            "type": "table_row",
            "table_row": {"cells": [text_cell("column_name"), text_cell("data_type")]},
        }
    )

    # 🔹 컬럼 정보 추가
    for col_name, data_type in columns:
        table_block["table"]["children"].append(
            {
                "object": "block",
                "type": "table_row",
                "table_row": {"cells": [text_cell(col_name), text_cell(data_type)]},
            }
        )

    # 📌 Notion에 테이블 추가
    notion.blocks.children.append(block_id=NOTION_PAGE_ID, children=[table_block])

print("✅ 테이블 구조 전체 재구성 완료!")
