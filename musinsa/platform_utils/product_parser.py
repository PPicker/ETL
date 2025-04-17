from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
from .image_extractor import extract_images
from .detail_parser import parse_product_detail
from .. import headers,base_url,chrome_options
from selenium import webdriver


def json2dict(product_json):
    return {
        "name": product_json.get("goodsName", ""),
        "brand": product_json.get("brand", ""),
        "category": product_json.get("category", None),
        "url": product_json.get("goodsLinkUrl", ""),
        "description_detail": "",
        "description_semantic": "",
        "description_semantic_raw": "",
        "original_price": product_json.get("normalPrice", None),
        "discounted_price": product_json.get("price") if product_json.get("price") != product_json.get("normalPrice") else None,
        "sold_out": product_json.get("isSoldOut", False),
        "thumbnail_url" : product_json.get("thumbnail", "")
        # "image_urls": [product_json.get("thumbnail", "")]
    }



# def parse_product_list(product_jsons):
#     driver = webdriver.Chrome(options=chrome_options)
#     products = []
#     for product_json in product_jsons:
#         product = json2dict(product_json)
#         product['image_urls'] =extract_images(product['url'])
#         print(product)
#         description_txt,description_image_urls = parse_product_detail(product['url'],driver) #꺼내오기만함 아직 가공 안되어있음
#         product['description_txt'] = description_txt
#         product['description_image_urls'] = description_image_urls
#         products.append(product)
#     return products

def parse_product_list(product_jsons):
    products = []
    driver = None
    max_retries = 3  # 최대 재시도 횟수
    
    i = 0
    while i < len(product_jsons):
        product_json = product_jsons[i]
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 드라이버가 없으면 새로 생성
                if driver is None:
                    driver = webdriver.Chrome(options=chrome_options)
                
                product = json2dict(product_json)
                try:
                    product['image_urls'] = extract_images(product['url'])
                except Exception as e:
                    print(f"⚠️ 이미지 추출 실패 - {product.get('name', 'unknown')}: {str(e)}")
                    product['image_urls'] = []
                
                print(f"Processing: {product.get('name', 'unknown')} (시도 {retry_count+1}/{max_retries})")
                
                description_txt, description_image_urls = parse_product_detail(product['url'], driver)
                product['description_txt'] = description_txt
                product['description_image_urls'] = description_image_urls
                
                # 성공적으로 처리되면 제품 추가 및 내부 루프 탈출
                products.append(product)
                break
                
            except Exception as e:
                retry_count += 1
                print(f"❌ 파싱 실패 - {product_json.get('name', 'unknown')} (시도 {retry_count}/{max_retries}): {str(e)}")
                
                # 드라이버 재시작
                try:
                    driver.quit()
                except:
                    pass
                driver = webdriver.Chrome(options=chrome_options)
                
                # 최대 재시도 횟수에 도달하면
                if retry_count >= max_retries:
                    print(f"⚠️ 최대 재시도 횟수 초과 - {product_json.get('name', 'unknown')} 건너뜀")
                    # 빈 정보로 제품 추가 (선택사항)
                    product['description_txt'] = None
                    product['description_image_urls'] = []
                    products.append(product)
        
        # 다음 제품으로 이동
        i += 1
    
    # 마지막에 드라이버 종료
    if driver:
        try:
            driver.quit()
        except:
            pass
            
    return products

if __name__ =='__main__':
    import requests
    import re
    import json

    url = "https://www.musinsa.com/products/4869537"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)

    pattern = r'window\.__MSS__\.product\.state\s*=\s*(\{.*?\});'
    match = re.search(pattern, res.text, re.DOTALL)

    if match:
        product_json = match.group(1)
        product_data = json.loads(product_json)

        image_urls = [
            "https://image.msscdn.net" + img["imageUrl"]
            for img in product_data.get("goodsImages", [])
        ]

        for img_url in image_urls:
            print(img_url)
    else:
        print("❌ JavaScript 내 데이터 못 찾음.")