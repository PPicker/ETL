from selenium.webdriver.chrome.options import Options
import os 
headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/95.0.4638.69 Safari/537.36")
}

base_url =  "https://www.etcseoul.com"

chrome_options = Options()
chrome_options.add_argument("--headless")  # headless 모드 사용
chrome_options.add_argument("--window-size=1920,1080")  # 화면 크기 설정
