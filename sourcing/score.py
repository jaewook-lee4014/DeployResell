"""추천도: 규칙마다 점수를 더하고 별로 바꾼다. 계산할 수 없는 규칙(기록 없음 등)은 0점 + 사유를 남긴다."""
import config


def score(deal_price, cat, comp, hist, conf="높음"):
    R = config.RULES
    rules, total = [], 0

    def add(key, ok, pts, why):
        nonlocal total
        got = pts if ok else 0
        total += got
        rules.append({"rule": key, "ok": ok, "pts": got, "why": why})

    low = cat["price"]
    diff = (low - deal_price) / low * 100
    if conf == "낮음":  # 다른 상품일 수 있어서 가격 점수는 주지 않는다 (가격비교 열어서 확인)
        add("최저가보다 싸다", None, R["cheaper_pts"], f"핫딜 {deal_price:,} vs 최저가 {low:,} ({diff:+.0f}%) · 매칭 낮음이라 확인 필요")
    else:
        add("최저가보다 싸다", diff >= R["cheaper_pct"], R["cheaper_pts"],
            f"핫딜 {deal_price:,} vs 최저가 {low:,} ({diff:+.0f}%)")

    if hist["low"]:
        ok = deal_price <= hist["low"] * (1 + R["near_record_pct"] / 100)
        add("역대 최저가 수준", ok, R["near_record_pts"], f"기록 최저 {hist['low']:,} (기록 {hist['points']}건)")
    else:
        add("역대 최저가 수준", None, R["near_record_pts"], "기록 없음 (첫 확인)")

    calm = comp["near"] < R["compete_max"]
    add("경쟁 약함", calm, R["compete_pts"],
        f"최저가 근처 판매처 {comp['near']}곳 / 비교 {comp['offers']}곳 ({comp['source']})")

    add("리뷰 많음", cat["reviews"] >= R["reviews_min"], R["reviews_pts"], f"리뷰 {cat['reviews']:,}개")

    stars = next(s for th, s in config.STARS if total >= th)
    return {"points": total, "stars": stars, "rules": rules}
