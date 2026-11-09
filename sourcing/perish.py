"""상하기 쉬운 / 보관이 어려운 음식 자동 제외.

원칙: 확실한 것만 자동 제외. 대분류가 '식품'으로 확인된 상품만 판단하고, 카테고리를 모르면 제외하지 않는다.
(상품명만 보고 음식이라고 짐작하면 '딸기슈가 푸드 마스크' 같은 화장품이 걸린다)

1단계 카테고리: 검색결과 카드의 카테고리 ID (lCatId > mCatId > sCatId > ssCatId)
   - 대분류가 '식품'이 아니면 판단하지 않는다 (화장품·유아용품·생활용품은 통과)
   - 축산물·김치·수산물·농산물(쌀 포함)·빵 중분류, 우유 소분류는 통째로 제외 (EXCLUDE_M / EXCLUDE_S)
   - data/categories.json (ID -> '식품>축산물>소고기') 이 있으면 중·소분류 이름으로 바로 제외
     (만드는 법: fetch_categories.py — 네이버 커머스 API 라 고정 IP(VM)에서 실행)
2단계 상품명 키워드: 핫딜 상품명 + 카탈로그명에서 냉동·냉장·생크림·한우 같은 말
   - '상온·실온·멸균·레토르트·냉동건조' 처럼 상온 보관이라고 적혀 있으면 자동 제외하지 않는다

확실할 때만 자동 제외하고, 애매하면 그대로 둔다. 사람이 웹사이트 발굴 탭에서 [제외] / [제외 해제] 한다.
단어 목록은 아래 상수에서 고친다.
"""
import json
import re

import config

FOOD = "50000006"
BABY = "50000005"
# 네이버 쇼핑 대분류 (검색결과 페이지 categoryId 로 식품·출산/육아·생활/건강 확인)
TOP = {"50000000": "패션의류", "50000001": "패션잡화", "50000002": "화장품/미용", "50000003": "디지털/가전",
       "50000004": "가구/인테리어", "50000005": "출산/육아", "50000006": "식품", "50000007": "스포츠/레저",
       "50000008": "생활/건강", "50000009": "여가/생활편의", "50000010": "면세점"}

# 1단계-가: 카테고리 ID (이름표 없이도 동작). 2026-11-09~10 들어온 핫딜의 카탈로그로 확인한 ID
EXCLUDE_M = {  # 식품 중분류 -> 통째로 제외
    "50000145": "축산물 (고기·계란·소시지·너겟)",
    "50000147": "김치",
    "50000159": "수산물",
    "50000160": "농산물 (쌀·잡곡·과일·채소)",
    "50022959": "빵",
}
EXCLUDE_S = {"50012820": "우유"}  # 소분류 단위로 제외 (음료>우유)
KEEP_S = {"50001078": "견과류", "50001176": "김"}  # 위 중분류 안이지만 상온 보관이 쉬운 소분류
# 수산물 중 상온 건어물은 상품명으로 살린다
DRY_SEAFOOD = re.compile(r"멸치|다시마|미역|황태|북어|건새우|쥐포|진미채|김자반|조미김|곱창김|구운\s*김|돌김")

# 1단계-나: 카테고리 이름 (categories.json 이 있을 때). 중·소·세분류 이름에 이 말이 있으면 제외
CAT_PERISH = ("축산", "정육", "소고기", "돼지고기", "닭고기", "오리고기", "양고기", "수산", "생선", "해산물", "회/",
              "과일", "채소", "냉동", "냉장", "유제품", "우유", "요구르트", "요거트", "치즈", "아이스크림",
              "반찬", "김치", "베이커리", "케이크", "빵", "떡", "계란", "달걀", "두부", "밀키트", "샐러드",
              "쌀", "잡곡", "농산물")  # 쌀·잡곡: 상하진 않지만 무겁고 보관이 번거로워 제외 (사용자 결정 2026-11-10)
# 그 분류 안이어도 가장 작은 분류 이름에 이 말이 있으면 상온 보관품 (과자/베이커리>과자, 농산물>쌀 등)
CAT_SAFE = ("과자", "쿠키", "스낵", "건조", "건어물", "육포", "통조림", "캔", "레토르트", "즉석",
            "견과", "분유", "시리얼", "멸균", "차류", "커피", "음료", "김")
# 출산/육아 안의 음식 (이유식·유아식은 상온 파우치와 냉동 큐브가 섞여 있어 2단계 키워드로 본다)
BABY_FOOD_CAT = ("이유식", "유아식", "유아간식", "유아음료")

# 2단계: 상품명 키워드 (정규식). 'OO맛', 'OO향' 은 맛 이름이라 제외하지 않는다
NOT_FLAVOR = r"(?!\s*(?:맛|향|색|모양|과자|칩|깡|스낵|볼|링|크래커|팝콘|사탕|젤리|캔디|껌|라면|사발면|컵라면|면|크림|샌드|소스|가루|파우더))"
NAME_PERISH = [
    ("냉동", r"냉동"), ("냉장", r"냉장"), ("아이스박스", r"아이스\s*박스|아이스팩|드라이아이스|보냉"),
    ("신선식품", r"신선식품|산지직송|당일\s*(?:제조|생산|도축|수확|조업)|생물\b|활\s*(?:전복|낙지|꽃게|새우|장어)"),
    ("생크림·케이크", r"생크림|케이크|케잌"), ("아이스크림", r"아이스크림|아이스\s*바\b"), ("우유", r"(?<!두유|멸균)우유" + NOT_FLAVOR),
    ("요거트", r"(?:요거트|요구르트|요플레)" + NOT_FLAVOR), ("치즈", r"치즈" + NOT_FLAVOR),
    ("계란", r"계란|달걀|구운란|메추리알|유정란|특란|왕란"), ("두부", r"두부" + NOT_FLAVOR), ("김치·반찬", r"김치" + NOT_FLAVOR + r"|반찬"),
    ("정육", r"정육|한우|한돈|삼겹살|목살|등심|차돌|우삼겹|생닭|닭다리살|닭가슴살|오리고기"),
    ("수산", r"연어|전복|생굴|굴비|새우" + NOT_FLAVOR + r"|오징어회|광어|우럭|갈치|고등어|꽃게|대게|킹크랩|낙지|쭈꾸미|주꾸미"),
    ("과일·채소", r"생과일|과일\s*(?:선물|세트|박스)|\d+\s*(?:kg|키로)\s*(?:사과|배|귤|감귤|딸기|포도|복숭아|수박|참외|토마토|감자|고구마|양파)"
                + r"|(?:사과|배|귤|감|한라봉|천혜향|레드향|키위|망고|블루베리|체리|자두|포도|딸기|샤인머스캣|복숭아|수박|참외|토마토"
                + r"|감자|고구마|양파|당근|상추|버섯|오이|호박|배추|무)\s*\d+(?:\.\d+)?\s*(?:kg|키로)"),
    ("빵·떡", r"식빵|베이글|크루아상|모닝빵|생지|떡(?!볶이|국떡|뻥)"), ("생면", r"생면|생칼국수|생우동"),
    ("밀키트·샐러드", r"밀키트|샐러드" + NOT_FLAVOR), ("냉장 주스", r"아임리얼|착즙|NFC\s*주스|생과일\s*주스"),
    ("쌀·잡곡", r"(?:쌀|햅쌀|현미|찹쌀|흑미|잡곡|보리|오곡|귀리)\s*\d+(?:\.\d+)?\s*(?:kg|키로)|\d+\s*(?:kg|키로)\s*(?:쌀|햅쌀|현미|찹쌀|잡곡)"),
    ("훈제·너겟", r"훈제\s*(?:치킨|오리|연어|닭)|치킨\s*너겟|너겟|만두|핫도그"), ("수제", r"수제\s*(?:쿠키|잼|청|반찬|도시락|이유식)"),
]
NAME_PERISH = [(k, re.compile(p, re.I)) for k, p in NAME_PERISH]
# 상온 보관이라고 적혀 있으면 자동 제외하지 않는다 (사람이 본다)
NAME_SAFE = re.compile(r"상온|실온|멸균|레토르트|통조림|냉동\s*건조|동결\s*건조|건조\s*(?:과일|야채|채소)|파우더|분말|스틱\s*커피", re.I)

_names = None


def names():
    """data/categories.json: {카테고리ID: '식품>축산물>소고기'}. 없으면 빈 dict"""
    global _names
    if _names is None:
        p = config.BASE / "data" / "categories.json"
        try:
            _names = {str(k): v for k, v in json.loads(p.read_text(encoding="utf-8")).items()}
        except (OSError, ValueError):
            _names = {}
    return _names


def category_path(cat):
    """가장 작은 분류부터 이름을 찾는다. 이름표가 없으면 대분류 이름만"""
    if not cat:
        return ""
    N = names()
    for k in ("ss", "s", "m", "l"):
        if cat.get(k) and str(cat[k]) in N:
            return N[str(cat[k])]
    return TOP.get(str(cat.get("l") or ""), "")


def classify(texts, cat):
    """texts: [핫딜 상품명, 카탈로그명], cat: {'l','m','s','ss'} 카테고리 ID.
    -> {'excluded': bool, 'stage': 'category'|'keyword'|'', 'why': str, 'category': str, 'food': bool}"""
    path = category_path(cat)
    parts = path.split(">")
    l_id = str((cat or {}).get("l") or "")
    text = " ".join(t for t in texts if t)
    # 음식인지는 카테고리로만 정한다. 상품명으로 짐작하지 않는다
    # (예: '딸기슈가 푸드 마스크'는 화장품, '이유식 냉동 보관 용기'는 육아용품). 카테고리를 모르면 사람이 본다.
    food = l_id == FOOD or parts[0] == "식품" or any(w in path for w in BABY_FOOD_CAT)
    out = {"excluded": False, "stage": "", "why": "", "category": path, "food": food}
    if not food:
        return out
    safe = NAME_SAFE.search(text)
    if safe:
        out["why"] = f"상온 보관 표시 '{safe.group(0)}' · 자동 제외 안 함"
        return out

    # 1단계-가: 카테고리 ID
    m_id, s_id = str((cat or {}).get("m") or ""), str((cat or {}).get("s") or "")
    if l_id == FOOD and s_id not in KEEP_S:
        label = EXCLUDE_S.get(s_id) or EXCLUDE_M.get(m_id)
        if label and not (m_id == "50000159" and DRY_SEAFOOD.search(text)):
            out.update(excluded=True, stage="category", why=f"카테고리 {label}")
            return out

    # 1단계-나: 카테고리 이름 (식품·이유식의 중분류 이하만 본다)
    if (parts[0] == "식품" or any(w in path for w in BABY_FOOD_CAT)) and len(parts) > 1:
        leaf = parts[-1]
        hit = next((w for w in CAT_PERISH if any(w in p for p in parts[1:])), None)
        if hit and not any(w in leaf for w in CAT_SAFE):
            out.update(excluded=True, stage="category", why=f"카테고리 {path}")
            return out

    # 2단계: 상품명 키워드
    for key, rx in NAME_PERISH:
        m = rx.search(text)
        if m:
            out.update(excluded=True, stage="keyword", why=f"상품명 '{m.group(0).strip()}' ({key})")
            return out
    return out
