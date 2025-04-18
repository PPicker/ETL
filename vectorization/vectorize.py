import os
import boto3
import psycopg2
import faiss
import numpy as np
from io import BytesIO
from PIL import Image
from embedder import Embedding_Model
from config.env_loader import load_db_config
from utils.aws import get_s3_client


class Vectorizer:
    """
    S3에서 이미지 로드 → 임베딩 생성 → FAISS 인덱스 갱신/검색 → PostgreSQL 메타 정보 조회
    """
    def __init__(self, faiss_index_path: str):
        # DB & S3 설정
        
        self.db_config = load_db_config()
        self.s3_bucket = os.getenv('AWS_S3_BUCKET_NAME')
        self.faiss_index_path = faiss_index_path
        # AWS S3 클라이언트 생성
        self.s3_client = get_s3_client()
        # Embedding 모델 로드
        self.embedder = Embedding_Model()

    def fetch_image(self, key: str) -> Image.Image:
        """
        S3 객체 키(key)로부터 이미지를 가져와 PIL.Image로 반환
        """
        resp = self.s3_client.get_object(Bucket=self.s3_bucket, Key=key)
        body = resp["Body"].read()
        return Image.open(BytesIO(body)).convert("RGB")

    def embed_and_update(self):
        """
        products 테이블에서 is_embedded=False인 항목을 벡터화하여
        FAISS 인덱스에 추가하고, DB의 is_embedded 플래그를 True로 업데이트
        """
        # DB 연결
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        cur.execute("SELECT id, thumbnail_url FROM products WHERE is_embedded = FALSE;")
        rows = cur.fetchall()
        if not rows:
            print("✅ 벡터화할 신규 상품이 없습니다.")
            conn.close()
            return

        ids, embs = [], []
        for prod_id, key in rows:
            try:
                img = self.fetch_image(key)
                vec = self.embedder.embed_image(img)  # embed_image 메서드 사용
                vec = vec.cpu().numpy().astype("float32")
                embs.append(vec)
                ids.append(prod_id)
            except Exception as e:
                print(f"❌ ID {prod_id} 처리 실패: {e}")

        if embs:
            batch = np.vstack(embs)
            faiss.normalize_L2(batch)
            index = faiss.read_index(self.faiss_index_path)
            index.add_with_ids(batch, np.array(ids, dtype='int64'))
            faiss.write_index(index, self.faiss_index_path)
            print(f"✅ FAISS에 {len(ids)}개 벡터 추가 완료")

            # DB 업데이트
            cur.execute(
                "UPDATE products SET is_embedded = TRUE WHERE id = ANY(%s);",
                (ids,)
            )
            conn.commit()

        conn.close()
    
