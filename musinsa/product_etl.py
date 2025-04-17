from base.product_etl import BaseProductETL
import requests
import os
from typing import List
import numpy as np
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from . import headers,base_url
from .platform_utils.product_parser import parse_product_list
from .platform_utils.image_extractor import load_image_from_url, upload_pil_image_to_s3,get_normalized_image_format_from_url
from config.brand_whitelist_loader import load_whitelisted_brands
from config.env_loader import load_db_config
from .get_brand_url import load_brand_dict_from_csv
from utils.fashion_detector import FashionDetector
from utils.name_rule import normalize_product_name,normalize_brand_name,get_image_name
import uuid

class Musinsa_ProductETL(BaseProductETL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # 부모 클래스 초기화
        self.fashion_detector = FashionDetector()  # 추가 속성 초기화
        
    def extract(self,brand_name,brand_url) -> List[dict]:
        product_base_url = "https://api.musinsa.com/api2/dp/v1/plp/goods"
        params = {
            "brand": f"{brand_name}",  # 원하는 브랜드
            "sortCode": "POPULAR",
            "page": 1,           # 시작 페이지 번호
            "size": 30,          # 한 페이지당 제품 수
            "caller": "FLAGSHIP",
            'gf' : "M", #성별 남자 , 여성은 F, 전체는 A임
            'category' : '001' #001 : 상의, 002 : 아우터, 003 : 하의
        }

        category_dicts = {'001':'TOP', '002' : 'OUTER', '003' : 'BOTTOM' }
        try:
            products_data = []
            products = []
            for key, value in category_dicts.items():
                params["page"] = 1 #초기화해줌
                params['category'] = key
                print(f'{key} 카테고리를 추출합니다')
                while True:
                    # API 요청 보내기
                    response = requests.get(product_base_url, params=params, headers=headers)
                    json_data = response.json()
                    # 제품 데이터는 data.list 에 있음
                    tmp_products = json_data.get("data", {}).get("list", [])
                    tmp_products = [{**product, 'category': value} for product in tmp_products] #category 추가
                    
                    products.extend(tmp_products) #일단 10개로 고정
                    pagination = json_data.get("data", {}).get("pagination", {})
                    has_next = pagination.get("hasNext", False)
                    has_next = False #일단 페이지 넘기지 마
                    print(f"페이지 {params['page']}에서 {len(tmp_products)}개의 제품 수집")
                    
                    # 다음 페이지가 없으면 종료
                    if not has_next:
                        print("더 이상 페이지가 없습니다. 종료합니다.")
                        break
                    params["page"] += 1
        except Exception as e:
            print(f"{brand_name} 페이지 요청 중 오류 발생: {e}")
        
        return parse_product_list(products)

    def _transform_single_product(self, product: dict) -> dict:
        image_urls = product['image_urls']

        product['product_name_normalized'] = normalize_product_name(product['name'])
        product['brand_normalized'] = normalize_brand_name(product["brand"])
        s3_image_path_base = get_image_name(
            platform=self.platform,
            brand=product['brand_normalized'],
            product_name=product['product_name_normalized']
        )

        images = [load_image_from_url(image_url) for image_url in image_urls]

        detector = FashionDetector()
        is_only_fashion_list = detector.detect_person_in_images(images, batch_size=4)

        image_entries = []
        thumbnail_flag = False
        index = 0
        thumbnail_index = 0 #업데이트가 진짜 만약없으면 0번으로 넣어

        for image_url, is_only_fashion, image in zip(image_urls, is_only_fashion_list, images):
            
            if is_only_fashion:
                result = detector.detect_fashion(image)
                if not result["is_fashion"]:
                    continue  # 옷만 있는 이미지인데 옷이 아님 → 제거

                entry = {
                    "clothing_only": True,
                    "is_thumbnail": False,
                    "order_index": index,
                }

                if not thumbnail_flag and not result.get("is_multi_category", False):
                    entry["is_thumbnail"] = True
                    product["category"] = result.get("category")
                    thumbnail_index = index #thumbnail용 엔트리의 인덱스 저장
                    thumbnail_flag = True

            else:
                entry = {
                    "clothing_only": False,
                    "is_thumbnail": False,
                    "order_index": index,
                }

            image_format = get_normalized_image_format_from_url(image_url)
            s3_image_path = s3_image_path_base + f"{uuid.uuid4()}"
            if (s3_url := upload_pil_image_to_s3(image, s3_image_path, 'ppicker', self.s3_client, format=image_format)):
                entry['url'] = s3_url
                image_entries.append(entry)

            index += 1
        product['thumbnail_url'] = image_entries[thumbnail_index]['url'] #thumbnail index의 url을 넣어
        product['image_entries'] = image_entries
        return product

    def transform(self, products):
        return [self._transform_single_product(product) for product in products]

    def transform_one(self, product):
        return self._transform_single_product(product)



if __name__ == '__main__':
    whitelist = load_whitelisted_brands()
    my_brands = whitelist["musinsa"]
    base_url = 'https://www.musinsa.com'
    brand_dict = {brand: f'{base_url}/brand/{brand}' for brand in my_brands}

    etc_product_etl = Musinsa_ProductETL(brand_dict = brand_dict, platform='musinsa',db_config=load_db_config())
    etc_product_etl.run()