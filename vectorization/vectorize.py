import os
import boto3
import psycopg2
import faiss
import numpy as np
from io import BytesIO
from PIL import Image
from .embedder import Embedding_Model
from config.env_loader import load_db_config
from utils.aws import get_s3_client
from dotenv import load_dotenv

class Vectorizer:
    """
    S3에서 이미지 로드 → 임베딩 생성 → FAISS 인덱스 갱신/검색 → PostgreSQL 메타 정보 조회
    """
    def __init__(self, faiss_index_path: str):
        # DB & S3 설정
        
        # AWS S3 클라이언트 생성
        load_dotenv()
        self.db_config = load_db_config() #여기서 load_dotenv가 불리는거였네
        self.s3_client = get_s3_client()
        # Embedding 모델 로드
        self.embedder = Embedding_Model()
        
        self.s3_bucket = os.getenv('AWS_S3_BUCKET_NAME')
        self.faiss_index_path = faiss_index_path

        os.makedirs(os.path.dirname(self.faiss_index_path), exist_ok=True)
        if os.path.exists(self.faiss_index_path):
            self.index = faiss.read_index(self.faiss_index_path)
        else:
            # 차원(d)을 알고 있다면 빈 인덱스를 생성
            base_index = faiss.IndexFlatL2(self.embedder.dim)
            #base_index = faiss.IndexFlatIP(self.embedder.dim)  # 코사인 유사도 기반 인덱스
            self.index = faiss.IndexIDMap(base_index)  # ID 매핑 추가
            # (ID를 함께 쓰려면 IndexIDMap 등으로 래핑)


        

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
        cur.execute("SELECT id, thumbnail_key FROM products WHERE is_embedded = FALSE;")
        rows = cur.fetchall()
        if not rows:
            print("✅ 벡터화할 신규 상품이 없습니다.")
            conn.close()
            return

        ids, embs = [], []
        for prod_id, key in rows:
            print(key)
            img = self.fetch_image(key)
            vec = self.embedder.embed_image(img)  # embed_image 메서드 사용
            vec = vec.cpu().numpy().astype("float32")
            embs.append(vec)
            ids.append(prod_id)
            # try:
            #     img = self.fetch_image(key)
            #     vec = self.embedder.embed_image(img)  # embed_image 메서드 사용
            #     vec = vec.cpu().numpy().astype("float32")
            #     embs.append(vec)
            #     ids.append(prod_id)
            # except Exception as e:
            #     print(f"❌ ID {prod_id} 처리 실패: {e}")

        if embs:
            batch = np.vstack(embs) #model에서 normalize는 이미 진행함
            # faiss.normalize_L2(batch)
            self.index.add_with_ids(batch, np.array(ids, dtype='int64'))
            faiss.write_index(self.index, self.faiss_index_path)
            print(f"✅ FAISS에 {len(ids)}개 벡터 추가 완료")

            # DB 업데이트
            cur.execute(
                "UPDATE products SET is_embedded = TRUE WHERE id = ANY(%s);",
                (ids,)
            )
            conn.commit()

        conn.close()
    
if __name__ =='__main__':
    

    # .env 파일 로드
    
    vectorizer = Vectorizer(
            faiss_index_path="./faiss/faiss_index_with_ids.index"
        )

    # 신규 상품 벡터화 및 업데이트
    vectorizer.embed_and_update()