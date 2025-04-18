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

def update_product_images_urls_to_keys():
    # PostgreSQL 연결 정보 - 실제 정보로 수정 필요
    db_config = load_db_config()
    
    # 연결 생성
    conn = None
    try:
        # 데이터베이스 연결
        print("PostgreSQL 데이터베이스에 연결 중...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 1. 새로운 key 컬럼 추가 (아직 존재하지 않는 경우)
        print("key 컬럼 확인/추가 중...")
        check_column_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'product_images' AND column_name = 'key'
        """
        cursor.execute(check_column_query)
        column_exists = cursor.fetchone()
        
        if not column_exists:
            add_column_query = """
                ALTER TABLE product_images 
                ADD COLUMN "key" VARCHAR(255)
            """
            cursor.execute(add_column_query)
            print("key 컬럼이 추가되었습니다.")
        else:
            print("key 컬럼이 이미 존재합니다.")
        
        # 2. S3 URL이 저장된 레코드 조회
        print("S3 URL이 있는 레코드 조회 중...")
        select_query = """
            SELECT id, url 
            FROM product_images 
            WHERE url LIKE 'https://ppicker.s3.amazonaws.com/%'
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
                    # 레코드 업데이트 - key 컬럼에 key 저장
                    update_query = """
                        UPDATE product_images 
                        SET "key" = %s
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
        
        print(f"\n업데이트 작업 완료:")
        print(f"✅ 성공: {updated_count}개 레코드")
        print(f"❌ 실패: {failed_count}개 레코드")
        
        # 변환 작업이 완료된 후 url 컬럼 확인 및 삭제
        print("\nurl 컬럼 삭제 전 검증 중...")
        
        # key 컬럼이 비어있는 레코드 확인
        check_empty_keys_query = """
            SELECT COUNT(*) 
            FROM product_images 
            WHERE "key" IS NULL OR "key" = ''
        """
        cursor.execute(check_empty_keys_query)
        empty_keys_count = cursor.fetchone()[0]
        
        if empty_keys_count > 0:
            print(f"⚠️ 주의: {empty_keys_count}개 레코드에 key 값이 없습니다.")
            print("모든 URL이 key로 변환되었는지 확인 후 url 컬럼을 삭제하세요.")
        else:
            print("✅ 모든 레코드가 key 값을 가지고 있습니다.")
            
            # 사용자 확인 요청
            confirm = input("url 컬럼을 삭제하시겠습니까? (yes/no): ").strip().lower()
            
            if confirm == 'yes':
                # url 컬럼 삭제
                drop_column_query = """
                    ALTER TABLE product_images 
                    DROP COLUMN url
                """
                cursor.execute(drop_column_query)
                conn.commit()
                print("✅ url 컬럼이 삭제되었습니다.")
            else:
                print("url 컬럼 삭제가 취소되었습니다.")
        
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

if __name__ == "__main__":
    # 데이터베이스 업데이트 실행
    update_product_images_urls_to_keys()