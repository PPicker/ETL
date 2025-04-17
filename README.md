# 🧩 PPicker ETL

쇼핑몰 기반 패션 데이터 수집 및 정제 자동화 파이프라인 구축 프로젝트

---

## 🗂 프로젝트 개요

PPicker ETL은 다양한 패션 커머스 플랫폼(예: 무신사, etcseoul 등)에서

**브랜드 및 상품 정보를 자동으로 수집, 정제, 저장**하는 파이프라인입니다.

- 쇼핑몰 HTML 구조 분석 및 크롤러 구현
- 플랫폼별 구조를 공통화하고, 코드 재사용을 위한 **ETL 추상 클래스 설계**
- PostgreSQL 연동 및 데이터 저장 자동화
- 추후 추천 시스템 및 검색 기능 고도화를 위한 데이터 기반 확보 목적

---

## 🚀 주요 기능

- **추상 베이스 클래스**
    - `base/`의 `BaseBrandETL`, `BaseProductETL`이 core ETL 워크플로우(`extract`, `transform`, `load`, `run`) 정의
- **플랫폼 플러그인**
    - `etcseoul`, `musinsa` 등 각 플랫폼 별 `brand_etl.py`, `product_etl.py` 및 `platform_utils/` 파서 제공
- **설정 기반**
    - `config/env_loader.py`로 환경 변수 및 DB 연결 설정 로드
    - `config/brand_whitelist.json`에서 크롤링할 브랜드 목록 제어
- **유틸리티**
    - 이름 정규화, S3 이미지 업로드, 이미지 기반 카테고리 분류 도구 등 `utils/`에 포함
- **Notion 동기화**
    - `brand2notion.py`, `table2notion.py` 스크립트로 PostgreSQL 데이터와 스키마를 Notion 데이터베이스에 동기화

---

## 📁 디렉토리 구조

```bash
ETL/
├── base/                   # 공통 추상화 클래스 (브랜드/상품 크롤링 공통 로직)
│   ├── base_brand_etl.py
│   ├── base_product_etl.py
│
├── config/
│   └── settings.py         # DB 연결, 크롤링 설정 등 공통 환경 변수
│
├── etcseoul/               # etcseoul 대상 크롤링 로직
│   ├── brand_etl.py
│   ├── product_etl.py
│   ├── get_brand_url.py
│   └── platform_utils/
│       └── parser.py
│
├── musinsa/                # musinsa 대상 크롤링 로직
│   ├── brand_etl.py
│   ├── product_etl.py
│   ├── get_brand_url.py
│   └── platform_utils/
│       └── parser.py
│
├── utils/                  # 공통 유틸 함수
│   ├── db_handler.py       # PostgreSQL 연결 및 쿼리 처리
│   └── request_handler.py  # HTTP 요청 핸들러 및 예외처리
│
├── requirements.txt        # 프로젝트 의존 패키지
└── __init__.py
```

## ⚙️ 주요 기능 및 구현 사항

- **플랫폼 확장성 고려한 구조 설계**
    - 쇼핑몰별 HTML 구조를 파악하고, 각 플랫폼별 전용 크롤링 모듈 개발
    - 크롤링 로직을 추상 클래스 기반으로 구성하여, 신규 쇼핑몰 추가 시 재사용 가능
- **브랜드 → 상품 → 상세정보까지의 계층적 크롤링**
    - 브랜드 URL 수집 → 브랜드 페이지 내 상품 목록 수집 → 각 상품 상세페이지 진입 후 상세정보 저장
- **PostgreSQL 연동 및 정형화된 스키마 저장**
    - 브랜드 및 상품 테이블 분리
    - 이미지 및 URL 정제 처리
    - 추후 검색 및 추천 시스템 연동을 고려한 구조

---

## 🧪 사용 기술 스택

- **Python 3.10**
- **BeautifulSoup4**, `requests`, `re`
- **PostgreSQL**
- 크롤링 안정성을 위한 `User-Agent`, `timeout` 처리 및 예외 핸들링
- 쇼핑몰 확장을 위한 OOP 기반 구조 설계

---

## 💡 향후 계획

- 신규 쇼핑몰(29cm, WConcept 등) 대상 플랫폼 및 편집샵 추가
- 상품 태그 및 카테고리 자동 분류를 위한 NLP 모델 연동
- 유저 로그 기반 개인화 추천 시스템 연결