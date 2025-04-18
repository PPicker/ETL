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

class ETC_ProductETL(BaseProductETL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # 부모 클래스 초기화
        self.fashion_detector = FashionDetector()  # 추가 속성 초기화
        
    def extract(self,brand_name,brand_url) -> List[dict]:
        try:
            response = requests.get(brand_url, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        except Exception as e:
            print(f"{brand_name} 페이지 요청 중 오류 발생: {e}")
        #brand description부터 추출
        return parse_product_list(response,brand_name)

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
        is_only_fashion_list =  self.fashion_detector.batch_detect_person(images, batch_size=4)
        
        image_entries = []
        thumbnail_flag = False
        index = 0
        thumbnail_index = 0 #업데이트가 진짜 만약없으면 0번으로 넣어

        for image_url, is_only_fashion, image in zip(image_urls, is_only_fashion_list, images):
            if is_only_fashion:
                result = self.fashion_detector.detect_fashion(image)
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


if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'brand_urls.csv')
    all_urls = load_brand_dict_from_csv(csv_path)
    whitelist = load_whitelisted_brands()
    my_brands = whitelist["etcseoul"]
    brand_dict = {name: url for name, url in all_urls.items() if name in my_brands}
    # for name in brand_dict:
    #     print(name)
    etc_product_etl = ETC_ProductETL(brand_dict = brand_dict, platform='ETCSeoul',db_config=load_db_config())
    etc_product_etl.run()