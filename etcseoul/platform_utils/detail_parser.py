from typing import Optional
import re

# def parse_product_detail(soup):
#     # detail_wrap 요소 찾기
#     wrap = soup.find("div", class_="detail_wrap")
#     if not wrap:
#         return None

#     # text-align:center인 div 모두 찾기
#     center_divs = wrap.find_all(
#         "div",
#         style=re.compile(r"text-align\s*:\s*center")
#     )
#     if not center_divs:
#         return None

#     # 모든 텍스트+<br>을 순회하며 chunks에 모으기
#     chunks = []
#     for div in center_divs:
#         for node in div.descendants:
#             if node.name == "br":
#                 chunks.append("\n")
#             elif isinstance(node, str):
#                 text = node.strip()
#                 if text:
#                     chunks.append(text)
#         # div 사이 구분용 공백 줄 추가
#         chunks.append("\n\n")

#     full_text = "".join(chunks).strip()
#     return full_text or None  # 혹시 strip 후 빈 문자열이 되면 None




def parse_product_detail(soup: str) -> Optional[str]:
    wrap = soup.find("div", class_="detail_wrap")
    if not wrap:
        return None

    # 1) 태그 이름을 None 으로 두면, 모든 태그에서 style 속성만 보고 찾습니다.
    center_tags = wrap.find_all(
        None,
        style=re.compile(r"text-align\s*:\s*center")
    )
    # -- 또는 --
    # 2) 명시적으로 div,p 둘 다 허용
    # center_tags = wrap.find_all(
    #     ["div", "p"],
    #     style=re.compile(r"text-align\s*:\s*center")
    # )

    if not center_tags:
        return None

    chunks = []
    for tag in center_tags:
        for node in tag.descendants:
            if node.name == "br":
                chunks.append("\n")
            elif isinstance(node, str):
                txt = node.strip()
                if txt:
                    chunks.append(txt)
        chunks.append("\n\n")

    full_text = "".join(chunks).strip()
    return full_text or None