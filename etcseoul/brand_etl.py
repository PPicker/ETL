from base.brand_etl import BaseBrandETL
from .platform_utils.brand_parser import get_brand_description
from .get_brand_url import load_brand_dict_from_csv
from config.env_loader import load_db_config
from config.brand_whitelist_loader import load_whitelisted_brands
import requests
import os 
from utils.name_rule import normalize_brand_name

headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/95.0.4638.69 Safari/537.36")
}

class ETC_BrandETL(BaseBrandETL):
    def extract(self, brand_name: str, brand_url: str) -> dict:
        try:
            response = requests.get(brand_url, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        except Exception as e:
            print(f"{brand_name} 페이지 요청 중 오류 발생: {e}")

        #brand description부터 추출
        description = get_brand_description(response, brand_name) 
        brand_data = {'name':brand_name,'url':brand_url,'description':description}
        return brand_data


if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'brand_urls.csv')
    all_urls = load_brand_dict_from_csv(csv_path)

    whitelist = load_whitelisted_brands()
    my_brands = whitelist["etcseoul"]
    brand_dict = {name: url for name, url in all_urls.items() if name in my_brands}
    etc_etl = ETC_BrandETL(brand_dict = brand_dict, platform='ETCSeoul',db_config=load_db_config())
    etc_etl.run()