from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# def parse_product_detail(soup):
#     # soup = BeautifulSoup(response.text, 'html.parser')
#     wrap = soup.find("div", class_="xans-element- xans-product xans-product-detail detail_wrap")
#     if wrap:
#         return [div.get_text(separator="\n", strip=True)
#                 for div in wrap.find_all("div", style="text-align: center;")]
#     return None


    

def parse_product_detail(soup):
    html = response.text
    detail_wrap_div = soup.find("div", class_="xans-element- xans-product xans-product-detail detail_wrap")
    if detail_wrap_div:
        # detail_wrap_div 내부에서 style="text-align: center;" 속성을 가진 모든 <div>를 찾음
        detail_divs = detail_wrap_div.find_all("div", style="text-align: center;")
        # for div in detail_divs:
        #     print(div.get_text(separator="\n", strip=True))
        #     return 
        return [div.get_text(separator="\n", strip=True) for div in detail_divs]
    else:
        print("PC용 detail 영역을 찾지 못했습니다.")
        return None 
def parse_prouct_detail(url):

    driver.get(url)
    wait = WebDriverWait(driver, 30)
    button = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button.gtm-click-button[data-button-id='prd_detail_open']")
    ))
    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    driver.execute_script("arguments[0].click();", button)
    
    # 3. 컨텐츠 로드 대기: 클래스가 "text-xs font-normal text-black font-pretendard"인 모든 요소
    containers = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, ".text-xs.font-normal.text-black.font-pretendard")
    ))
    
    # 필요한 경우, 마지막 요소 대신 모든 요소를 순회할 수도 있음
    container = containers[-1]
    if (text_content:= container.text) :
        description = text_content
        return description
    
    else:
        '''
        text가 없는 경우에만 image를 뽑도록 로직 조정
        '''
        print('Text 형태로 저장되어있지 않습니다')
        description ='' #일단 공백 보내
        # (c) <img> 태그의 src에서 .jpg 또는 .svg 파일 URL 추출
        imgs = container.find_elements(By.TAG_NAME, "img")
        image_urls = []
        for img in imgs:
            src = img.get_attribute("src")
            #if src and ('.jpg' in src.lower() or '.svg' in src.lower()): #아직 svg처리못함
            if src and ('.jpg' in src.lower()):
                image_urls.append(src)
                
