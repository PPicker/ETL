import requests
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO
from .. import base_url,headers
import os
import re
import json
def get_normalized_image_format_from_url(url):
    """
    이미지 URL에서 확장자를 추출하고, Pillow 및 Content-Type에서 사용 가능한 형식으로 정규화한다.
    """
    path = urlparse(url).path
    ext = os.path.splitext(path)[-1].lower().strip('.')

    format_map = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'webp': 'WEBP',
        'gif': 'GIF',
        'bmp': 'BMP',
        'tiff': 'TIFF'
    }

    return format_map.get(ext, 'JPEG')  # 확장자가 없거나 예상 못 하면 기본 'JPEG'


# def extract_editor_images(soup):
#     imgs = soup.find_all('img', src=lambda s: s and '/web/upload/NNEditor/' in s)
#     return list(dict.fromkeys([urljoin(base_url, img['src']) for img in imgs]))


def extract_images(url):
    """
    지정한 URL의 HTML에서 src 속성에 '/web/upload/NNEditor/'가 포함된 <img> 태그의 절대 URL을 리스트로 반환합니다.
    """

    # url = "https://www.musinsa.com/products/4869537"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    pattern = r'window\.__MSS__\.product\.state\s*=\s*(\{.*?\});'
    match = re.search(pattern, response.text, re.DOTALL)

    if match:
        product_json = match.group(1)
        product_data = json.loads(product_json)

        image_urls = [
            "https://image.msscdn.net" + img["imageUrl"]
            for img in product_data.get("goodsImages", [])
        ]





def load_image_from_url(url):
        """
        URL에서 이미지를 다운로드하여 PIL Image로 변환
        
        Args:
            url: 이미지 URL
            
        Returns:
            PIL Image 객체
        """
        try:
            response = requests.get(url,headers = headers,timeout=10)
            response.raise_for_status()  # HTTP 오류 확인
            return Image.open(BytesIO(response.content)).convert("RGB")
        except Exception as e:
            raise ValueError(f"이미지 URL을 로드하는 중 오류가 발생했습니다: {url}, 오류: {str(e)}")
    



def upload_pil_image_to_s3(pil_image, filename, bucket, s3_client, format='JPEG'):
    try:
        img_buffer = BytesIO()
        pil_image.save(img_buffer, format=format)
        img_buffer.seek(0)
        s3_client.put_object(
            Bucket=bucket,
            Key=filename,
            Body=img_buffer,
            ContentType=f'image/{format.lower()}'
        )

        s3_url = f"https://{bucket}.s3.amazonaws.com/{filename}"
        return s3_url
    except Exception as e:
        print(f"❌ S3 업로드 실패: {filename}, 오류: {e}")
        return None