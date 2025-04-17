from bs4 import BeautifulSoup

def parse_product_detail(soup):
    # soup = BeautifulSoup(response.text, 'html.parser')
    wrap = soup.find("div", class_="xans-element- xans-product xans-product-detail detail_wrap")
    if wrap:
        return [div.get_text(separator="\n", strip=True)
                for div in wrap.find_all("div", style="text-align: center;")]
    return None

