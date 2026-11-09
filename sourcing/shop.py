"""네이버쇼핑 모바일 검색 결과 -> 상품 목록 (가격비교 카탈로그 + 개별 판매처 상품)."""
import json
import random
import re
import time
import urllib.parse

from scrapling.fetchers import Fetcher

import config

MOBILE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1")
BLOCK_MARKERS = ("일시적으로 제한", "네이버는 안정적인 쇼핑", "자동입력 방지", "자동 프로그램", "보안문자",
                 "비정상적인 접근", "잠시 후 다시 확인")


class Blocked(RuntimeError):
    pass


_last = [0.0]


def _throttle():
    lo, hi = config.SEARCH_DELAY
    wait = _last[0] + random.uniform(lo, hi) - time.time()
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()


def _plain(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(s or ""))).strip()


def parse_products(html: str):
    """검색 결과 HTML 속 상품 JSON ({"slotType":"CARD","data":{...}}) 파싱.
    naver_lowest_price_crawler.parse_products 와 같은 방식 + 카탈로그 여부·판매처명·구매수."""
    dec = json.JSONDecoder()
    out, seen = [], set()
    for m in re.finditer(r'\{"slotType":"CARD","data":', html):
        try:
            d = dec.raw_decode(html, m.start())[0]["data"]
        except (ValueError, KeyError, TypeError):
            continue
        nv = str(d.get("nvMid") or "")
        if not nv or nv in seen:
            continue
        seen.add(nv)
        catalog = d.get("cardType") == "CATALOG_CARD" or d.get("mallId") == "naver_model"
        price = d.get("discountedSalePrice") or d.get("salePrice") or None
        fee = (d.get("productDeliveryInfo") or {}).get("deliveryFee")
        url = d.get("productUrl") or {}
        out.append({
            "nv_mid": nv,
            "catalog": catalog,
            "title": _plain(d.get("productName")),
            "mall": "" if catalog else _plain(d.get("mallName")),
            "price": int(price) if price else None,
            "ship": int(fee) if isinstance(fee, (int, float)) else None,
            "sellers": int(d.get("mallCount") or 0) if catalog else None,
            "reviews": int(d["totalReviewCount"]) if d.get("totalReviewCount") else 0,
            "rating": float(d["averageReviewScore"]) if d.get("averageReviewScore") else None,
            # 카테고리 ID (대>중>소>세). 이름은 없어서 perish.py 가 data/categories.json 으로 찾는다
            "cat": {k: str(d.get(f) or "") for k, f in (("l", "lCatId"), ("m", "mCatId"), ("s", "sCatId"), ("ss", "ssCatId"))},
            "link": (f"https://search.shopping.naver.com/catalog/{nv}" if catalog
                     else url.get("mobileUrl") or url.get("pcUrl") or ""),
        })
    return out


def search(query: str):
    _throttle()
    url = ("https://m.search.naver.com/search.naver?"
           + urllib.parse.urlencode({"ssc": "tab.m_shopping.all", "where": "m_shop", "query": query}))
    r = Fetcher.get(url, headers={"User-Agent": MOBILE_UA, "Referer": "https://m.naver.com/",
                                  "Accept-Language": "ko-KR,ko;q=0.9"}, timeout=25)
    if r.status in (403, 418, 429):
        raise Blocked(f"네이버 검색 차단 (HTTP {r.status})")
    html = r.body.decode("utf-8", "ignore")
    prods = parse_products(html)
    if not prods and any(k in html for k in BLOCK_MARKERS):
        raise Blocked("네이버 검색 보안 확인 페이지")
    return prods
