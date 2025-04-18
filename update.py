import urllib.parse
import psycopg2
from psycopg2 import sql
from config.env_loader import load_db_config


# URL에서 S3 key 추출 함수
def extract_key_from_s3_url(s3_url):
    if not s3_url:
        return None
    
    try:
        parsed_url = urllib.parse.urlparse(s3_url)
        # URL 경로에서 첫 번째 '/'를 제거하여 key 추출
        key = parsed_url.path.lstrip('/')
        return key
    except Exception as e:
        print(f"❌ URL 파싱 실패: {s3_url}, 오류: {e}")
        return None

def update_thumbnail_urls_to_keys():
    # PostgreSQL 연결 정보 - 실제 정보로 수정 필요
    db_config =load_db_config()
    
    # 연결 생성
    conn = None
    try:
        # 데이터베이스 연결
        print("PostgreSQL 데이터베이스에 연결 중...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 1. 새로운 컬럼 추가 (아직 존재하지 않는 경우)
        print("thumbnail_key 컬럼 확인/추가 중...")
        check_column_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'products' AND column_name = 'thumbnail_key'
        """
        cursor.execute(check_column_query)
        column_exists = cursor.fetchone()
        
        if not column_exists:
            add_column_query = """
                ALTER TABLE products 
                ADD COLUMN thumbnail_key VARCHAR(255)
            """
            cursor.execute(add_column_query)
            print("thumbnail_key 컬럼이 추가되었습니다.")
        else:
            print("thumbnail_key 컬럼이 이미 존재합니다.")
        
        # 2. S3 URL이 저장된 레코드 조회
        print("S3 URL이 있는 레코드 조회 중...")
        select_query = """
            SELECT id, thumbnail_url 
            FROM products 
            WHERE thumbnail_url LIKE 'https://ppicker.s3.amazonaws.com/%'
        """
        cursor.execute(select_query)
        results = cursor.fetchall()
        total_records = len(results)
        print(f"총 {total_records}개의 레코드를 처리합니다.")
        
        # 3. 각 레코드의 URL을 key로 변환하여 업데이트
        updated_count = 0
        failed_count = 0
        
        for record in results:
            record_id = record[0]
            s3_url = record[1]
            
            # URL에서 key 추출
            s3_key = extract_key_from_s3_url(s3_url)
            
            if s3_key:
                try:
                    # 레코드 업데이트 - thumbnail_key 컬럼에 key 저장
                    update_query = """
                        UPDATE products 
                        SET thumbnail_key = %s
                        WHERE id = %s
                    """
                    cursor.execute(update_query, (s3_key, record_id))
                    updated_count += 1
                    
                    # 100개마다 진행상황 출력 및 커밋
                    if updated_count % 100 == 0:
                        conn.commit()
                        print(f"{updated_count}/{total_records} 레코드 업데이트 완료")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"❌ 레코드 업데이트 실패 ID: {record_id}, 오류: {e}")
            else:
                failed_count += 1
                print(f"⚠️ Key 추출 실패 ID: {record_id}, URL: {s3_url}")
        
        # 변경사항 커밋
        conn.commit()
        
        print(f"\n작업 완료:")
        print(f"✅ 성공: {updated_count}개 레코드")
        print(f"❌ 실패: {failed_count}개 레코드")
        
    except Exception as e:
        print(f"❌ 데이터베이스 작업 중 오류 발생: {e}")
        if conn:
            conn.rollback()
    finally:
        # 연결 종료
        if conn:
            cursor.close()
            conn.close()
            print("데이터베이스 연결이 종료되었습니다.")

# AWS S3 클라이언트를 사용하여 키가 실제로 존재하는지 확인하는 함수 (선택 사항)
def verify_s3_keys():
    import boto3
    
    # AWS 및 PostgreSQL 연결 정보 - 실제 정보로 수정 필요
    db_config = {
        'host': 'localhost',
        'database': 'your_db_name',
        'user': 'your_username',
        'password': 'your_password',
        'port': 5432
    }
    
    bucket_name = 'ppicker'  # URL에서 확인된 버킷 이름
    
    # S3 클라이언트 생성
    s3_client = boto3.client('s3')
    
    conn = None
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 저장된 key 목록 조회
        select_query = """
            SELECT id, thumbnail_key 
            FROM products 
            WHERE thumbnail_key IS NOT NULL
        """
        cursor.execute(select_query)
        results = cursor.fetchall()
        total_keys = len(results)
        
        print(f"총 {total_keys}개의 S3 키를 검증합니다...")
        
        valid_keys = 0
        invalid_keys = 0
        
        for record in results:
            record_id = record[0]
            key = record[1]
            
            try:
                # S3에서 해당 키가 존재하는지 확인
                s3_client.head_object(Bucket=bucket_name, Key=key)
                valid_keys += 1
                
                # 100개마다 진행상황 출력
                if valid_keys % 100 == 0:
                    print(f"{valid_keys + invalid_keys}/{total_keys} 키 검증 완료")
            except Exception as e:
                print(f"❌ 존재하지 않는 S3 키: ID={record_id}, Key={key}")
                invalid_keys += 1
        
        print(f"\nS3 키 검증 결과:")
        print(f"✅ 유효한 키: {valid_keys}개")
        print(f"❌ 유효하지 않은 키: {invalid_keys}개")
        
    except Exception as e:
        print(f"❌ 검증 중 오류 발생: {e}")
    finally:
        # 연결 종료
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    # 데이터베이스 업데이트 실행
    update_thumbnail_urls_to_keys()
    