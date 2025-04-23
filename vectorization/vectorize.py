import os
import numpy as np
import psycopg2
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from .embedder import Embedding_Model  # 사용자 정의 임베딩 클래스
from utils.aws import get_s3_client
from config.env_loader import load_db_config,load_environment
from pgvector.psycopg2 import register_vector


class Vectorizer:
    """
    S3에서 이미지 로드 → 임베딩 생성 → PostgreSQL에 벡터 저장 (embedding 컬럼 기반)
    """

    def __init__(self):
        
        self.db_config = load_db_config()
        self.s3_client = get_s3_client()
        self.embedder = Embedding_Model()
        self.s3_bucket = os.getenv("AWS_S3_BUCKET_NAME")


    def fetch_image(self, key: str) -> Image.Image:
        """
        S3 객체 키(key)로부터 이미지를 가져와 PIL.Image로 반환
        """
        resp = self.s3_client.get_object(Bucket=self.s3_bucket, Key=key)
        body = resp["Body"].read()
        return Image.open(BytesIO(body)).convert("RGB")

    def embed_and_update(self):
        """
        products 테이블에서 embedding IS NULL인 항목을 벡터화하여
        PostgreSQL의 embedding 컬럼에 저장
        """
        conn = psycopg2.connect(**self.db_config)
        register_vector(conn)
        cur = conn.cursor()
        #cur.execute("SELECT id, thumbnail_key FROM products WHERE embedding IS NULL;")
        cur.execute("SELECT id, thumbnail_key FROM products;")
        rows = cur.fetchall()
        if not rows:
            print("✅ 벡터화할 신규 상품이 없습니다.")
            conn.close()
            return

        for prod_id, key in rows:
            try:
                img = self.fetch_image(key)
                vec = self.embedder.embed_image(img)
                vec = vec.cpu().numpy().astype("float32")
                
                # pgvector 형식에 맞게 수정: 벡터를 psycopg2.extras.Json으로 변환하지 않고 직접 사용
                cur.execute(
                    "UPDATE products SET embedding = %s WHERE id = %s;",
                    (vec, prod_id)
                )
                conn.commit()  # 각 업데이트 후 커밋 추가
                print(f"✅ ID {prod_id} 처리 완료")

            except Exception as e:
                print(f"❌ ID {prod_id} 처리 실패: {e}")

        conn.close()  # 모든 작업 완료 후 연결 종료


if __name__ == "__main__":
    load_environment()
    vectorizer = Vectorizer()
    vectorizer.embed_and_update()