"""맘이베베 핫딜방: 글 목록 가져오기 + 제목에서 쇼핑몰·상품명·핫딜가 뽑기 (로그인 불필요)."""
import re

from scrapling.fetchers import Fetcher

import config

LIST_URL = ("https://apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json?search.clubid={cafe}"
            "&search.queryType=lastArticle&search.menuid={menu}&search.page={page}&search.perPage={per}")

ENDED = re.compile(r"^\s*(끝|종료|품절|마감)\s*[)\].:]?\s*")
KNOWN_MALLS = ("쿠팡", "지마켓", "g마켓", "옥션", "11번가", "네이버쇼핑", "네이버", "위메프", "티몬", "롯데온",
               "ssg", "이마트", "홈플러스", "컬리", "토스", "카카오", "오아시스", "cj더마켓", "공홈")
# 가격이 아닌 금액: 괄호, '개당 ~원', '/적립 ~', '포인트 ~원', '쿠폰 ~원'
NOISE = [re.compile(p) for p in (
    r"\([^)]*\)", r"\[[^\]]*\]", r"개당\s*[\d,]+\s*원?대?", r"/?\s*적립[^/]*", r"[+]?\s*(네페|네이버페이)?\s*포인트\s*[\d,]+\s*원?",
    r"[\d,]+\s*원?\s*(쿠폰|적립|할인쿠폰)", r"체감가?", r"선착순?", r"무배|무료배송", r"삼/국/농/롯|[가-힣]{1,2}카(/[가-힣]{1,2}카)+",
)]
WON = re.compile(r"(\d{1,3}(?:,\d{3})+|\d{3,7})\s*원")
BARE = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d{3,7})(?![\d.,]|\s*(?:g|kg|ml|l|개|입|매|포|정|t|매입|캡슐|롤|구|팩|박스|병|통|세트|%|일|mg)\b)", re.I)


def fetch_list(page=1):
    url = LIST_URL.format(cafe=config.CAFE_ID, menu=config.MENU_ID, page=page, per=config.PER_PAGE)
    r = Fetcher.get(url, stealthy_headers=True, headers={"Referer": "https://cafe.naver.com/"}, timeout=20)
    if r.status != 200:
        raise RuntimeError(f"카페 목록 HTTP {r.status}")
    res = r.json()["message"]["result"]
    return res["articleList"], res.get("hasNext", False)


def parse_title(subject: str):
    s = re.sub(r"\s+", " ", subject).strip()
    ended = bool(ENDED.match(s))
    s = ENDED.sub("", s)
    mall, rest = "", s
    m = re.match(r"^([^)]{1,25})\)\s*(.+)$", s)
    if m:
        mall, rest = m.group(1).strip(), m.group(2).strip()
    else:
        low = s.lower()
        for k in KNOWN_MALLS:
            if low.startswith(k):
                mall, rest = s[:len(k)], s[len(k):].strip()
                break
    clean = rest
    for p in NOISE:
        clean = p.sub(" ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    price, cut = None, None
    won = list(WON.finditer(clean))
    if won:
        price, cut = int(won[-1].group(1).replace(",", "")), won[0].start()
    else:
        bare = [b for b in BARE.finditer(clean) if int(b.group(1).replace(",", "")) >= 500]
        if bare:
            price, cut = int(bare[-1].group(1).replace(",", "")), bare[0].start()
    name = clean[:cut] if cut is not None else clean
    name = re.sub(r"[!~★☆♥]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" ,-/+")
    if price is not None and price < 500:
        price = None
    return {"ended": ended, "mall": mall, "name": name, "price": price}


def is_candidate(t):
    """발굴 대상: 마감 아님, 가격 있음, 상품명 있음 (쿠폰·이벤트 글 제외)"""
    if t["ended"] or not t["price"] or len(t["name"]) < 4:
        return False
    return not re.search(r"쿠폰|이벤트|응모|출석|룰렛|예약|픽업|오프\b|매장|상품권|\d+천?원권|기프티|아메리카노|러시", t["name"])
