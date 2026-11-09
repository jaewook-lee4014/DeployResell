"""신상품 발굴 1회 실행: 맘이베베 핫딜방 새 글 -> 네이버쇼핑 카탈로그 매칭 -> 추천도.

사용:
  .venv/Scripts/python run.py --limit 3        # 새 후보 글 3개만 처리 (시험용)
  .venv/Scripts/python run.py                  # 첫 페이지의 새 글 전부
  .venv/Scripts/python run.py --recheck ID     # 이미 처리한 글 다시
"""
import argparse
import json
import sys

import cafe
import config
import match
import score
import shop
import store


def process(c, art, deal):
    prods = shop.search(deal["name"])
    m = match.pick_catalog(deal, prods)
    if not m:
        store.save_deal(c, art, deal, "no_catalog", result={"found": len(prods)})
        return {"status": "no_catalog", "found": len(prods)}
    cat = m["p"]
    hist = store.past_low(c, cat["nv_mid"])        # 이번 가격을 넣기 전에 과거 기록을 본다
    store.add_price(c, cat["nv_mid"], cat["price"], cat["sellers"], cat["reviews"])
    deal_price = match.normalized_deal_price(deal, m)
    comp = match.competition(cat, prods)
    sc = score.score(deal_price, cat, comp, hist, m["conf"])
    res = {"status": "ok", "catalog": cat, "match": {k: m[k] for k in ("score", "conf", "cnt_deal", "cnt_cat", "qty_deal", "qty_cat", "unit")},
           "deal_price_norm": deal_price, "competition": comp, "history": hist, **sc}
    store.save_deal(c, art, deal, "ok", cat["nv_mid"], res)
    return res


ARTICLE_URL = "https://cafe.naver.com/ca-fe/cafes/{cafe}/articles/{aid}"


def to_row(d):
    """store.deals 한 줄 -> 웹사이트 '발굴' 시트 한 줄"""
    res = json.loads(d["result"] or "{}")
    cat, comp, mm = res.get("catalog") or {}, res.get("competition") or {}, res.get("match") or {}
    return {
        "articleId": d["article_id"], "postedAt": d["posted_at"], "subject": d["subject"], "mall": d["mall"],
        "name": d["name"], "dealPrice": d["deal_price"], "dealPriceNorm": res.get("deal_price_norm"),
        "status": d["status"], "nvMid": d["nv_mid"] or "", "catTitle": cat.get("title", ""),
        "catPrice": cat.get("price"), "sellers": cat.get("sellers"), "reviews": cat.get("reviews"),
        "near": comp.get("near"), "offers": comp.get("offers"), "gap12": comp.get("gap12"),
        "compSource": comp.get("source", ""), "matchConf": mm.get("conf", ""),
        "points": res.get("points"), "stars": res.get("stars"), "rules": res.get("rules", []),
        "histLow": (res.get("history") or {}).get("low"),
        "catLink": cat.get("link", ""), "articleUrl": ARTICLE_URL.format(cafe=config.CAFE_ID, aid=d["article_id"]),
        "checkedAt": d["checked_at"],
    }


def show(art, deal, r):
    print(f"\n[{art['articleId']}] {deal['mall']}) {deal['name']}  핫딜 {deal['price']:,}원")
    if r["status"] != "ok":
        print(f"   -> 맞는 가격비교 카탈로그 없음 (검색 결과 {r.get('found')}개)")
        return
    cat, mm = r["catalog"], r["match"]
    print(f"   카탈로그 {cat['nv_mid']} | {cat['title'][:55]}")
    print(f"   최저가 {cat['price']:,}원 · 판매처 {cat['sellers']} · 리뷰 {cat['reviews']:,} · 매칭 {mm['conf']}({mm['score']})"
          + (f" · 개수 환산 {mm['cnt_deal']}→{mm['cnt_cat']} = {r['deal_price_norm']:,}원" if mm["cnt_deal"] != mm["cnt_cat"] else ""))
    print(f"   경쟁 근사: 근처 {r['competition']['near']}곳 / 비교 {r['competition']['offers']}곳 · 가격 {r['competition']['prices']}")
    print(f"   추천도 {'★' * r['stars']}{'☆' * (5 - r['stars'])} ({r['points']}점)")
    for x in r["rules"]:
        mark = "✔" if x["ok"] else ("–" if x["ok"] is None else "✘")
        print(f"     {mark} {x['rule']} +{x['pts']}  {x['why']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="처리할 후보 글 수 (0=전부)")
    ap.add_argument("--recheck", type=int, action="append", default=[])
    a = ap.parse_args()

    c = store.db()
    arts, _ = cafe.fetch_list()
    done = 0
    for art in arts:
        deal = cafe.parse_title(art["subject"])
        if not cafe.is_candidate(deal):
            continue
        if store.seen(c, art["articleId"]) and art["articleId"] not in a.recheck:
            continue
        try:
            r = process(c, art, deal)
        except shop.Blocked as e:
            print(f"\n[중단] {e} — 다음 실행 때 이어서 처리")
            sys.exit(2)
        show(art, deal, r)
        done += 1
        if a.limit and done >= a.limit:
            break
    print(f"\n처리 {done}건")


if __name__ == "__main__":
    main()
