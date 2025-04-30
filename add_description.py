from config.env_loader import load_environment,load_db_config
from utils.gemini_analyzer import Analyzer
from utils.aws import get_s3_client
import psycopg2
import os
from io import BytesIO
from PIL import Image
import json

if __name__ == "__main__":
    load_environment()
    analyzer = Analyzer()
    s3_client= get_s3_client()
    db_config = load_db_config()
    conn = psycopg2.connect(
        **db_config
    )
    conn.autocommit = True
    s3 = get_s3_client()
    bucket = os.getenv("AWS_S3_BUCKET_NAME")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                p.id,
                p.name,
                p.description_semantic_raw
            FROM products AS p
            where p.description is NULL
            """
        )
        cols = [c.name for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    for row in rows:
        id = row["id"]
        name = row["name"]
        print(name)
        description_semantic_raw = row["description_semantic_raw"]
        with conn.cursor() as cur :
            cur.execute(
            """
            SELECT key
              FROM product_images
             WHERE product_id = %s
             ORDER BY order_index
            """,
            (id,),
            )
            img_keys = [row[0] for row in cur.fetchall()]
        
        images = []
        for img_key in img_keys:
            resp = s3.get_object(Bucket=bucket, Key=img_key)
            body = resp['Body'].read()
            
            # BytesIO를 통해 PIL로 열고 RGB로 변환
            images.append(Image.open(BytesIO(body)).convert("RGB"))
        response_json = analyzer.analyze(images = images, description=name + "\n" + description_semantic_raw)
        subcategory = response_json["세부 카테고리"]
        with conn.cursor() as cur:
            # 3) JSONB 컬럼(raw_data)에 새 JSON 통째로 덮어쓰기
            #    TEXT 컬럼(subcategory)에는 분리된 값 삽입
            cur.execute("""
                UPDATE products
                SET
                description    = %s::jsonb,
                subcategory = %s
                WHERE id = %s
            """, [
                json.dumps(response_json, ensure_ascii=False), 
                subcategory,
                id
            ])
            conn.commit()
    conn.close()