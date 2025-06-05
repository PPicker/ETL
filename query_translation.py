
import base64
import os
import json
from google import genai
from google.genai import types

def parse_fashion_query(text_query: str) -> dict:
    """
    패션 텍스트 쿼리를 구조화된 JSON 형태로 변환하는 함수
    
    Args:
        text_query (str): 사용자의 패션 관련 텍스트 쿼리
        
    Returns:
        dict: 구조화된 패션 정보를 담은 딕셔너리
        
    Raises:
        Exception: API 호출 실패 시 발생
    """
    try:
        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

        model = "gemini-2.5-flash-preview-05-20"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""도쿄의 빈티지 숍에서 찾을 것 같은 워크웨어 자켓"""),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""**Analyzing Query Structure**

I'm currently focused on extracting key elements from the user's text query and structuring them into a JSON format. My primary objective is to accurately map the provided information to the specific JSON fields: material, genre, category, silhouette, color and pattern, sub-category, atmosphere, and direction. Right now, I'm working to identify the specific requirements for each category.


**Mapping User Queries**

I'm now focusing on mapping the user's query into the JSON format, considering the constraints for each field. I've successfully mapped the example query \"도쿄의 빈티지 숍에서 찾을 것 같은 워크웨어 자켓\" to the JSON fields. The genre is identified as \"워크웨어\", the category as \"outer\", and the sub-category as \"자켓\".  Null values are assigned to fields lacking information, like material, silhouette, and color/pattern. The goal is to retain the original query's essence as much as possible.


**Formulating JSON Data**

I'm now structuring user queries into a JSON format, considering each field's specific constraints. I'm focusing on \"도쿄의 빈티지 숍에서 찾을 것 같은 워크웨어 자켓,\" successfully mapping: material (null), genre (\"워크웨어\"), category (\"outer\"), silhouette (null), color/pattern (null), sub-category (\"자켓\"), and atmosphere/direction (\"도쿄 빈티지\"). My focus is to preserve the user's intent.


"""),
                    types.Part.from_text(text="""```json
{
  \"소재\": null,
  \"장르\": \"워크웨어\",
  \"카테고리\": \"outer\",
  \"실루엣\": null,
  \"색상 및 패턴\": null,
  \"세부 카테고리\": \"자켓\",
  \"분위기 및 지향점\": \"도쿄 빈티지 숍 느낌\"
}
```"""),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""미니멀한 디자인의 오버사이즈 니트"""),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""**Identifying Fashion Elements**

I'm currently focused on extracting the core fashion elements from user queries. My aim is to accurately identify and categorize crucial features like material, genre, category, silhouette, and color/pattern, as well as any specific details. I'm exploring various methods to improve the precise identification of these specific features.


**Mapping Query Components**

I've made good progress on parsing \"미니멀한 디자인의 오버사이즈 니트.\"  I successfully pinpointed \"미니멀리즘\" as the genre, \"니트\" as the category (top), and \"오버사이즈\" as the silhouette. I identified the absence of specific material or color/pattern, so these will be marked as null.  Now I'm evaluating the \"Vibe/Direction\" based on \"미니멀한 디자인.\" I'm deciding whether \"미니멀\" is captured by \"미니멀리즘\" or if it is a secondary marker.


**Clarifying Attribute Assignments**

I've refined my approach to attribute assignments. With \"미니멀한 디자인의 오버사이즈 니트,\" I've confirmed that \"미니멀리즘\" accurately represents the genre, \"니트\" the category, and \"오버사이즈\" the silhouette. I've also decided that material and color/pattern are not specified, thus marked as null. After re-evaluating, I am now confident that the vibe/direction is captured by the genre and so is null.


"""),
                    types.Part.from_text(text="""```json
{
  \"소재\": null,
  \"장르\": \"미니멀리즘\",
  \"카테고리\": \"top\",
  \"실루엣\": \"오버사이즈\",
  \"색상 및 패턴\": null,
  \"세부 카테고리\": \"니트\",
  \"분위기 및 지향점\": null
}
```"""),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=text_query),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=[
                types.Part.from_text(text="""너는 패션 전문가로써 사용자의 질문을 구조화해줘
사용자는 자기가 원하는 느낌의 옷을 text query로 제공해줬어 
이걸 구조화하는게 필요해 text query를 json 형식으로 뱉어줘 
이때 json의 항목은 
소재, 장르, 카테고리,  실루엣, 색상 및 패턴, 세부 카테고리,  분위기 및 지향점이야 

카테고리는 top accessory bottom outer 중 하나로 뱉어줘

세부 카테고리는 정말 옷의 세부 카테고리를 분리해서 넣어줘

장르는 다음 중 하나로 뱉어줘 만약에 이중에 해당하지 않으면 null을 내보내고 복수로 해당되면 복수를 ,로 구분해서 저장하는데, 가장 근사한 애의 순서대로 나열해 가령 아메리칸 캐주얼과 아메카지 둘다 해당되는 것 같을땐 그 중 더 확실한애를 앞에 둬
- 캐주얼
- 아메리칸 캐주얼
- 아메카지
- 스트릿
- 댄디
- 미니멀리즘
- 클래식 
- 워크웨어 
- 프레피 
- 락시크
- 아웃도어

만약에 json 항목에 해당하는 내용이 없다면 해당 항목은 null로 뱉어줘 

최대한 사용자의 질문에서 내용을 수정하지 말고 mapping해주는 역할만 수행해
"""),
            ],
        )

        # 스트림 응답을 모두 수집
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text

        # JSON 부분만 추출
        json_start = response_text.find('```json')
        json_end = response_text.find('```', json_start + 7)
        
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start + 7:json_end].strip()
            return json.loads(json_str)
        else:
            # JSON 코드 블록이 없는 경우, 전체 응답에서 JSON 파싱 시도
            try:
                return json.loads(response_text.strip())
            except json.JSONDecodeError:
                raise Exception("응답에서 유효한 JSON을 찾을 수 없습니다.")
            
    except Exception as e:
        raise Exception(f"패션 쿼리 파싱 중 오류 발생: {str(e)}")




# To run this code you need to install the following dependencies:
# pip install google-genai


def query_categorizer(text_query: str):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-preview-05-20"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""도쿄의 빈티지 숍에서 찾을 것 같은 워크웨어 자켓"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""**Considering Fashion Categories**

I'm currently analyzing the query \"워크웨어 자켓\" (workwear jacket). My initial focus is on identifying core keywords within the request. I'm prioritizing the phrase \"workwear jacket\" and considering how to translate that to a fashion category relevant to Tokyo vintage shops. I am moving on to research keywords within my structured fashion category framework.


**Refining Category Selection**

I've honed in on the key category: \"jacket.\" I'm now certain \"jacket\" is the best fit, given the user's description. The translation of \"워크웨어 자켓\" (workwear jacket) is driving my process to identify the garment type, which is undoubtedly a \"jacket.\" My focus is now on confirming the best presentation format for this classification.


"""),
                types.Part.from_text(text="""jacket"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""\"미니멀한 디자인의 오버사이즈 니트\"
"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""**Pinpointing the Knit**

I've identified \"니트\" as the key term and confirmed that it fits under the \"top\" category in my system. Now I'm working on refining the description by integrating \"미니멀한 디자인\" and \"오버사이즈\" attributes. My goal is to craft a precise product description.


**Clarifying Category Matches**

I'm focused on the \"니트\" query and how it aligns with my existing system. I've successfully matched \"니트\" to the \"knit\" category and confirmed it falls under the \"top\" umbrella. Now, I'm analyzing the context and attributes provided to make sure I present a clear and accurate category match.


"""),
                types.Part.from_text(text="""knit"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""미니멀한 디자인의 오버사이즈의 폴로셔츠"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""**Focusing on Item Category**

I'm homing in on the core item, the \"polo shirt,\" as the foundation. The descriptors \"minimal design\" and \"oversized\" will refine the search parameters, but the polo shirt is the crux of the matter.


**Defining the Primary Category**

I've honed in on \"polo_shirt\" as the core category, confirmed by its direct match within the hierarchical structure.  The input's \"minimal\" and \"oversized\" descriptions will be treated as secondary attributes.  The primary category assignment is now robust.


"""),
                types.Part.from_text(text="""polo_shirt"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""프랑스 캐주얼 느낌의 옷"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""**Defining French Casual Style**

I'm currently focused on defining \"French casual style\" for clothing recommendations. I'm structuring the recommendations into \"top,\" \"bottom,\" \"outer,\" and \"accessory\" categories. This framework ensures a comprehensive approach to building a casual French wardrobe.


**Refining Categorization Strategy**

I've revised the approach to handling user queries. Instead of directly mapping keywords to categories, I'm now assessing the overall \"style\" intent.  The initial query lacked category-specific details, leading to an \"undetermined\" result, as instructed. I'm adapting to identify situations requiring a \"None\" response more readily.


"""),
                types.Part.from_text(text="""None"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""편안한 분위기로 입기 좋은 셔츠"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""shirt"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""여름에 입기 좋은 반팔 티셔츠"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""short_sleeve_tshirt"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=text_query),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text="""You are a fashion expert.
Your task is to analyze the user's query and determine whether it contains any specific keywords.
Based on those keywords, you must select the most appropriate category from the following structure:
{
    \"top\": {
        \"tshirt\":      [\"short_sleeve_tshirt\", \"long_sleeve_tshirt\",
                        \"sleeveless_tshirt\", \"ringer_tshirt\"],
        \"shirt\":       [\"short_sleeve_shirt\", \"denim_shirt\",
                        \"chambray_shirt\", \"polo_shirt\"],
        \"knit\":        [\"knit\", \"henley_knit\", \"sweatshirt\"],
        \"cardigan\":    [\"cardigan\"],
        \"hoodie\":      [\"hoodie\"],
        \"vest\":        [\"vest\"],
    },
    \"bottom\": {
        \"pants\":         [\"pants\", \"slacks\", \"wide_pants\"],
        \"chino_pants\":   [\"chino_pants\"],
        \"denim_pants\":   [\"denim_pants\"],
        \"cargo_pants\":   [\"cargo_pants\"],
        \"fatigue_pants\": [\"fatigue_pants\"],
        \"shorts\":        [\"shorts\", \"cargo_shorts\", \"denim_shorts\"],
    },
    \"outer\": {
        \"jacket\":   [\"jacket\", \"souvenir_jacket\", \"liner_jacket\",
                     \"trucker_jacket\", \"harrington_jacket\",
                     \"hooded_jacket\", \"field_jacket\", \"zip_up_jacket\"],
        \"blouson\":  [\"blouson\"],
        \"blazer\":   [\"blazer\"],
    },
    \"accessory\": {
        \"belt\":      [\"belt\"],
        \"hat\":       [\"ball_cap\"],
        \"neckwear\":  [\"necktie\"],
        \"bag\":       [\"tote_bag\", \"shopper_bag\"],
    },
}

This structure has 3 levels:

The first level is the top category: top, bottom, outer, or accessory.

The second level is the middle category.

The third level is the most specific category.

You must analyze the user's query and return the most appropriate category.
If the query contains a match at the most specific level, return that specific category.
If the query is less detailed, return the broader matching category.

If the user's query does not provide enough information to determine a category, return None."""),
        ],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

    response_text = ""
    for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
    return response_text





if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    query_json = parse_fashion_query("도쿄의 빈티지 숍에서 찾을 것 같은 워크웨어 자켓") 
    category = query_categorizer("헤응")
    print(query_json)
    print(category)
