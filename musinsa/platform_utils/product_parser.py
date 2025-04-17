from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
from .image_extractor import extract_images
from .detail_parser import parse_product_detail
from .. import headers,base_url,chrome_options




# def parse_product_list(response, brand=None):
#     soup = BeautifulSoup(response.text, 'html.parser')
#     products = []

#     for item in soup.select('li.item.xans-record-'):
#         a_tag = item.select_one('a.name')
#         if not a_tag:
#             continue

#         product_name = a_tag.get_text(strip=True)
#         product_href = urljoin(base_url, a_tag.get('href'))

#         price_info_block = item.select_one("ul.xans-product-listitem")
#         if price_info_block:
#             price_text = price_info_block.get_text(" ", strip=True)
#             if "원" not in price_text:
#                 continue

#             original_price,discounted_price = extract_price(price_text)
#             if not original_price:
#                 continue
#         try:
#             detail_response = requests.get(product_href, headers=headers)
#             soup = BeautifulSoup(detail_response.text, 'html.parser')

#             product_detail = parse_product_detail(soup)
#             image_urls = extract_editor_images(soup)
#             products.append({
#                 "name": product_name,
#                 "brand": brand,
#                 "category": None,  # 필요 시 분류
#                 "url": product_href,
#                 "description_detail": "",
#                 "description_semantic" : "",
#                 "description_semantic_raw": "\n".join(product_detail) if product_detail else "",
#                 "original_price": int(original_price.replace(",", "").replace("원", "")), #아직 할인 옵션 추가 X
#                 "discounted_price": int(discounted_price.replace(",", "").replace("원", "")) if discounted_price else None, #아직 할인 옵션 추가 X
#                 "sold_out": False,
#                 "image_urls": image_urls,
#             })

#         except Exception as e:
#             print(f"❌ 상세 페이지 처리 실패: {product_href}, 오류: {e}")
#             continue

#     return products


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



def parse_product_list(product_jsons):
    driver = webdriver.Chrome(options=chrome_options)
    for product_json in product_jsons:
        product = json2dict(product_json)
        product['image_urls'] =extract_images(product['url'])
        print(product)
        

        exit()
    return products_data




                # wait = WebDriverWait(driver, 30)
                
                # # 2. 버튼 클릭하기: 버튼이 클릭 가능한 상태를 기다립니다.
                # button = wait.until(EC.element_to_be_clickable(
                #     (By.CSS_SELECTOR, "button.gtm-click-button[data-button-id='prd_detail_open']")
                # ))
                # driver.execute_script("arguments[0].scrollIntoView(true);", button)
                # driver.execute_script("arguments[0].click();", button)
                
                # # 3. 컨텐츠 로드 대기: 클래스가 "text-xs font-normal text-black font-pretendard"인 모든 요소
                # containers = wait.until(EC.presence_of_all_elements_located(
                #     (By.CSS_SELECTOR, ".text-xs.font-normal.text-black.font-pretendard")
                # ))
                
                # # 필요한 경우, 마지막 요소 대신 모든 요소를 순회할 수도 있음
                # container = containers[-1]
                # text_content = container.text
                # if text_content:
                #     descriptions.append(text_content)
                # else:
                #     '''
                #     text가 없는 경우에만 image를 뽑도록 로직 조정
                #     '''
                #     print('Text 형태로 저장되어있지 않습니다')
                #     descriptions.append('') #일단 공백 보내
                    # # (c) <img> 태그의 src에서 .jpg 또는 .svg 파일 URL 추출
                    # imgs = container.find_elements(By.TAG_NAME, "img")
                    # image_urls = []
                    # for img in imgs:
                    #     src = img.get_attribute("src")
                    #     if src and ('.jpg' in src.lower() or '.svg' in src.lower()):
                    #         image_urls.append(src)
                    
                    # print("Image URLs:", image_urls)


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