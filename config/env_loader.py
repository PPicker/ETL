import os
from dotenv import load_dotenv

def load_db_config(env_file: str = ".env"):
    """
    지정된 .env 파일을 로드하고, DB 설정 딕셔너리 반환
    """
    load_dotenv(dotenv_path=env_file)

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        # "password": os.getenv("DB_PASSWORD")
    }




def load_aws_config(env_file: str = ".env"):
    """
    지정된 .env 파일을 로드하고, DB 설정 딕셔너리 반환
    """
    load_dotenv(dotenv_path=env_file)

    return {
        "AWS_S3_BUCKET_NAME": os.getenv("AWS_S3_BUCKET_NAME"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "AWS_DEFAULT_REGION": os.getenv("AWS_DEFAULT_REGION"),
    }