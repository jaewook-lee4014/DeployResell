"""신상품 발굴 자동 실행 (계속 켜두는 프로그램).

주기:
  - 맘이베베 핫딜방 목록: 10분마다 (새벽 2~6시는 30분마다)
  - 새 후보 글만 네이버쇼핑 검색 (요청 간격 4~8초)
  - ★3 이상 카탈로그는 6시간마다 최저가를 다시 기록 (역대 최저가 비교용 이력)
  - 네이버가 막으면 멈추고 30분 -> 1시간 -> 2시간 기다린다
  - 결과는 내부 사이트 '발굴' 시트로 보낸다 (실패분은 다음 사이클에 다시)

사용:
  .venv/Scripts/python daemon.py            # 계속 실행
  .venv/Scripts/python daemon.py --once     # 1사이클만 (작업 스케줄러용)
"""
import argparse
import logging
import sys
import time
from datetime import datetime

import cafe
import config
import match
import run
import shop
import store
import webapp

INTERVAL_DAY, INTERVAL_NIGHT = 10 * 60, 30 * 60
NIGHT_HOURS = range(2, 6)
MAX_PAGES = 3                  # 오래 꺼져 있었을 때 따라잡을 최대 페이지 (30개 x 3)
REFRESH_EVERY_H = 6
REFRESH_MIN_STARS = 3
BACKOFF_MIN = [30, 60, 120]

log = logging.getLogger("sourcing")


def setup_log():
    (config.BASE / "logs").mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    fmt.converter = lambda t: datetime.fromtimestamp(t, store.KST).timetuple()  # 로그 시각은 한국 시간
    for h in (logging.FileHandler(config.BASE / "logs" / "daemon.log", encoding="utf-8"), logging.StreamHandler(sys.stdout)):
        h.setFormatter(fmt)
        log.addHandler(h)
    log.setLevel(logging.INFO)
    logging.getLogger("scrapling").setLevel(logging.WARNING)


def new_candidates(c):
    """처리 안 한 후보 글 (오래된 것부터). 첫 페이지가 전부 새 글이면 다음 페이지도 본다."""
    out = []
    for page in range(1, MAX_PAGES + 1):
        arts, has_next = cafe.fetch_list(page)
        fresh = [a for a in arts if not store.seen(c, a["articleId"])]
        for a in fresh:
            deal = cafe.parse_title(a["subject"])
            if cafe.is_candidate(deal):
                out.append((a, deal))
            else:
                store.save_deal(c, a, deal, "skip")  # 후보 아님도 기록해서 다시 보지 않는다
        if len(fresh) < len(arts) or not has_next:
            break
    out.sort(key=lambda x: x[0]["articleId"])
    return out


def refresh_prices(c):
    last = store.meta_get(c, "refresh_at")
    if not last:  # 첫 실행: 방금 검색한 가격이 있으니 6시간 뒤부터
        store.meta_set(c, "refresh_at", time.time())
        return 0
    if time.time() - float(last) < REFRESH_EVERY_H * 3600:
        return 0
    n = 0
    for d, res in store.refresh_targets(c, REFRESH_MIN_STARS):
        prods = shop.search(d["name"])
        cat = next((p for p in prods if p["nv_mid"] == d["nv_mid"]), None)
        if cat and cat["price"]:
            store.add_price(c, cat["nv_mid"], cat["price"], cat["sellers"], cat["reviews"], "refresh")
            n += 1
    c.commit()
    store.meta_set(c, "refresh_at", time.time())
    return n


STATUS = {"at": None, "nextAt": None, "error": "", "last": ""}


def push(c):
    """안 보낸 결과를 25개씩 보내고, 마지막에 상태(마지막·다음 확인 시각)도 보낸다"""
    if not webapp.ON:
        return 0
    sent = 0
    while True:
        rows = store.unpushed(c, 25)
        if not rows:
            break
        items = [run.to_row(r) for r in rows if r["status"] != "skip"]
        if items:
            webapp.call("sourcing", items=items)
        store.mark_pushed(c, [r["article_id"] for r in rows])
        sent += len(items)
    webapp.call("sourcing", items=[], status=STATUS)
    return sent


def next_wait():
    # PC 시간대가 한국이 아닐 수 있다(이 PC는 GMT). 새벽 판단은 항상 한국 시간으로.
    return INTERVAL_NIGHT if datetime.now(store.KST).hour in NIGHT_HOURS else INTERVAL_DAY


def cycle(c):
    t0 = time.time()
    cands = new_candidates(c)
    ok = nocat = 0
    for art, deal in cands:
        r = run.process(c, art, deal)
        if r["status"] == "ok":
            ok += 1
            if r["stars"] >= 4:
                log.info(f"★{r['stars']} {deal['name']} 핫딜 {deal['price']:,} / 최저 {r['catalog']['price']:,}")
        else:
            nocat += 1
    refreshed = refresh_prices(c)
    STATUS.update(at=store.now(), error="", nextAt=datetime.fromtimestamp(time.time() + next_wait(), store.KST).isoformat(timespec="seconds"),
                  last=f"새 후보 {len(cands)} · 매칭 {ok} · 카탈로그 없음 {nocat}")
    try:
        sent = push(c)
    except Exception as e:
        sent = 0
        log.warning(f"웹사이트 전송 실패 (다음 사이클에 다시): {e}")
    log.info(f"사이클 완료 {time.time() - t0:.0f}초: 새 후보 {len(cands)} (매칭 {ok}, 카탈로그 없음 {nocat}), "
             f"가격 재기록 {refreshed}, 전송 {sent}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    setup_log()
    if not webapp.ON:
        log.warning(".env 에 WEBAPP_URL / WORKER_TOKEN 이 없어 로컬에만 기록합니다.")
    c = store.db()
    fails = 0
    while True:
        try:
            cycle(c)
            fails = 0
        except shop.Blocked as e:
            wait = BACKOFF_MIN[min(fails, len(BACKOFF_MIN) - 1)]
            fails += 1
            log.warning(f"{e} — {wait}분 쉬고 다시 시도")
            STATUS.update(error=f"{e} · {wait}분 뒤 다시", nextAt=datetime.fromtimestamp(time.time() + wait * 60, store.KST).isoformat(timespec="seconds"))
            try:
                push(c)
            except Exception:
                pass
            if a.once:
                sys.exit(2)
            time.sleep(wait * 60)
            continue
        except Exception as e:
            log.exception(f"사이클 오류: {e}")
        if a.once:
            break
        time.sleep(next_wait())


if __name__ == "__main__":
    main()
