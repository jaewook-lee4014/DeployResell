"""핫딜 상품명 <-> 가격비교 카탈로그 매칭, 수량 맞춘 단가 비교, 검색 결과로 경쟁도 근사."""
import re

import config

# 용량: 1.8L, 210g, 340ml, 1kg / 개수: 24개, 3개입, 400T, 430포, 72입, 2종
SIZE = re.compile(r"(\d+(?:\.\d+)?)\s*(kg|g|ml|l|mg)(?![a-z가-힣])", re.I)
COUNT = re.compile(r"(\d+)\s*(개입|개|입|매|포|정|t|캡슐|롤|팩|병|통|봉|구|종)(?![a-z가-힣])", re.I)
MULT = re.compile(r"(\d+)\s*(?:개|입|봉)?\s*[x×*]\s*(\d+)", re.I)
STOP = {"1개", "개", "세트", "리필", "용", "정품", "무료", "배송", "본품", "the"}


def tokens(s):
    s = re.sub(r"[^\w가-힣.]+", " ", s.lower())
    return [t for t in s.split() if len(t) >= 2 and t not in STOP and not SIZE.fullmatch(t) and not COUNT.fullmatch(t)]


def size_of(s):
    s = re.sub(r"(\d)\s*(키로|킬로|kilo)", r"\1kg", s, flags=re.I)
    s = re.sub(r"(\d)\s*리터", r"\1l", s)
    m = SIZE.findall(s)
    if not m:
        return None
    v, u = m[0]
    v, u = float(v), u.lower()
    return {"kg": (v * 1000, "g"), "g": (v, "g"), "l": (v * 1000, "ml"), "ml": (v, "ml"), "mg": (v / 1000, "g")}[u]


def count_of(s):
    """총 개수. '3개입, 2개' -> 6, '9개×2봉' -> 18, 숫자 없으면 1"""
    m = MULT.search(s)
    if m:
        return int(m.group(1)) * int(m.group(2))
    nums = [int(n) for n, u in COUNT.findall(s) if u.lower() not in ("종",)]
    if not nums:
        return 1
    tot = 1
    for n in nums[:2]:  # '3개입, 2개' 처럼 두 개까지만 곱한다
        tot *= n
    return tot if tot <= 2000 else nums[0]


def similarity(name, title):
    a, b = set(tokens(name)), " ".join(tokens(title))
    if not a:
        return 0.0
    hit = sum(1 for t in a if t in b or (len(t) >= 3 and any(t in w or w in t for w in b.split() if len(w) >= 3)))
    return hit / len(a)


def pick_catalog(deal, prods):
    """핫딜과 가장 맞는 카탈로그. 이름 유사도 + 용량 일치 + 개수 일치"""
    d_size, d_cnt = size_of(deal["name"]), count_of(deal["name"])
    best = None
    for p in prods:
        if not p["catalog"] or not p["price"]:
            continue
        sim = similarity(deal["name"], p["title"])
        c_size, c_cnt = size_of(p["title"]), count_of(p["title"])
        both = bool(d_size and c_size)
        same_unit = both and d_size[1] == c_size[1]
        exact = same_unit and abs(d_size[0] - c_size[0]) < 0.01 * d_size[0] + 0.5
        # 용량이 같으면 가산, 단위만 같고 양이 다르면 0 (총량으로 환산해서 비교), 단위가 다르면(g vs ml) 감점
        score = sim + (0.2 if exact else 0) - (0.4 if both and not same_unit else 0) + (0.2 if d_cnt == c_cnt else 0)
        # 한쪽 제목에만 개수가 적혀 있으면(예: '30롤 2팩' vs '25m 롤화장지') 환산할 근거가 없다
        unknown = d_cnt != c_cnt and not (has_count(deal["name"]) and has_count(p["title"]))
        if not best or score > best["score"]:
            qd = d_cnt * (d_size[0] if same_unit else 1)
            qc = c_cnt * (c_size[0] if same_unit else 1)
            best = {"score": round(score, 2), "p": p, "sim": sim, "size_ok": exact or not both, "cnt_deal": d_cnt, "cnt_cat": c_cnt,
                    "qty_deal": qd, "qty_cat": qd if unknown else qc, "unit": d_size[1] if same_unit else "개", "qty_unknown": unknown}
    if not best or best["score"] < config.MATCH_MIN:
        return None
    best["conf"] = "높음" if best["score"] >= 1.1 else "보통" if best["score"] >= 0.8 else "낮음"
    if best["qty_unknown"]:
        best["conf"] = "낮음"
    return best


def has_count(s):
    return bool(MULT.search(s) or COUNT.search(s))


def normalized_deal_price(deal, m):
    """핫딜가를 카탈로그 총량 기준으로 환산. 총량 = 개수 x 용량(같은 단위일 때). 예: 1kg 17,610원 vs 5kg 카탈로그 -> 88,050원"""
    qd, qc = m.get("qty_deal") or m["cnt_deal"], m.get("qty_cat") or m["cnt_cat"]
    if not qd or abs(qd - qc) < 1e-9:
        return deal["price"]
    return round(deal["price"] / qd * qc)


def competition(cat, prods):
    """검색 결과 속 같은 상품(이름·용량·개수 일치) 판매처 가격으로 경쟁도 근사.
    카탈로그 최저가 근처(1000원 또는 1% 이내)에 붙은 판매처 수를 센다."""
    R = config.RULES
    c_size, c_cnt = size_of(cat["title"]), count_of(cat["title"])
    prices = [cat["price"]]
    for p in prods:
        if p["catalog"] or not p["price"]:
            continue
        if similarity(cat["title"], p["title"]) < 0.6 or count_of(p["title"]) != c_cnt:
            continue
        s = size_of(p["title"])
        if c_size and s and (s[1] != c_size[1] or abs(s[0] - c_size[0]) > 0.01 * c_size[0] + 0.5):
            continue
        prices.append(p["price"] + (p["ship"] or 0))  # 판매처끼리는 배송비 포함 가격으로 비교
    prices.sort()
    low = prices[0]
    gap = max(R["compete_gap_won"], low * R["compete_gap_pct"] / 100)
    near = sum(1 for x in prices if x - low <= gap)
    return {"near": near, "offers": len(prices), "gap12": (prices[1] - prices[0]) if len(prices) > 1 else None,
            "prices": prices[:8], "source": "검색결과 근사"}
