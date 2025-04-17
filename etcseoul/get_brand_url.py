import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import csv

def main():
    base_url = "https://www.etcseoul.com"
    url = base_url + "/brand.html"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/95.0.4638.69 Safari/537.36")
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print("페이지 요청 중 오류 발생:", e)
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    item_boxes = soup.select(".item_box")
    brand_dict = {}

    for box in item_boxes:
        try:
            item = box.select_one(".item")
            if not item:
                continue
            a_tag = item.find("a")
            if not a_tag:
                continue
            href = urljoin(url, a_tag.get("href"))
            p_tags = item.find_all("p")
            if len(p_tags) >= 2:
                brand_name = p_tags[1].get_text(strip=True)
                brand_dict[brand_name] = href
        except Exception as e:
            print("아이템 추출 중 에러 발생:", e)

    # CSV 저장
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, 'brand_urls.csv')

    try:
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["brand_name", "url"])
            for name, url in brand_dict.items():
                writer.writerow([name, url])
        print("✅ CSV 파일 저장 완료:", csv_file_path)
    except Exception as e:
        print("❌ CSV 저장 중 오류 발생:", e)


def load_brand_dict_from_csv(csv_path):
    brand_dict = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand_dict[row["brand_name"]] = row["url"]
    except Exception as e:
        print("❌ CSV 로딩 중 오류:", e)
    return brand_dict



if __name__ == '__main__':
    main()

    # 테스트 로딩 (필요시 주석 해제)
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # csv_path = os.path.join(current_dir, 'brand_urls.csv')
    # brand_dict = load_brand_dict_from_csv(csv_path)
    # print(brand_dict)
