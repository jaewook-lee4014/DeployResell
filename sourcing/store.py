"""로컬 기록 (SQLite): 처리한 핫딜 글, 카탈로그 최저가 이력. 과거 최저가 비교는 여기서 한다."""
import json
import sqlite3
from datetime import datetime, timedelta, timezone

import config

KST = timezone(timedelta(hours=9))


def now():
    return datetime.now(KST).isoformat(timespec="seconds")


def db():
    config.DB_PATH.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS deals(
      article_id INTEGER PRIMARY KEY, posted_at TEXT, subject TEXT, mall TEXT, name TEXT, deal_price INTEGER,
      status TEXT, nv_mid TEXT, result TEXT, checked_at TEXT);
    CREATE TABLE IF NOT EXISTS catalog_prices(
      nv_mid TEXT, at TEXT, price INTEGER, sellers INTEGER, reviews INTEGER, source TEXT);
    CREATE INDEX IF NOT EXISTS ix_cp ON catalog_prices(nv_mid, at);
    CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
    """)
    cols = {r["name"] for r in c.execute("PRAGMA table_info(deals)")}
    if "pushed" not in cols:  # 웹사이트 전송 여부 (0이면 다음 사이클에 다시 보낸다)
        c.execute("ALTER TABLE deals ADD COLUMN pushed INTEGER DEFAULT 0")
    return c


def meta_get(c, k, default=None):
    r = c.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
    return r["v"] if r else default


def meta_set(c, k, v):
    c.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, str(v)))
    c.commit()


def unpushed(c, limit=50):
    return c.execute("SELECT * FROM deals WHERE pushed=0 ORDER BY article_id LIMIT ?", (limit,)).fetchall()


def mark_pushed(c, ids):
    c.executemany("UPDATE deals SET pushed=1 WHERE article_id=?", [(i,) for i in ids])
    c.commit()


def refresh_targets(c, min_stars, days=7):
    """가격 기록을 계속 쌓을 카탈로그: 최근 며칠 안에 ★min_stars 이상 나온 것 (카탈로그당 최신 글 1개)"""
    rows = c.execute("""SELECT d.* FROM deals d JOIN (
                          SELECT nv_mid, MAX(article_id) a FROM deals
                          WHERE status='ok' AND posted_at >= datetime('now', ?) GROUP BY nv_mid) x
                        ON d.article_id = x.a""", (f"-{days} days",)).fetchall()
    out = []
    for r in rows:
        res = json.loads(r["result"] or "{}")
        if res.get("stars", 0) >= min_stars:
            out.append((r, res))
    return out


def seen(c, article_id):
    return c.execute("SELECT 1 FROM deals WHERE article_id=?", (article_id,)).fetchone() is not None


def past_low(c, nv_mid):
    """이번 확인 이전의 우리 기록 속 최저가 (카탈로그 최저가 + 같은 카탈로그의 과거 핫딜가)"""
    a = c.execute("SELECT MIN(price) m, COUNT(*) n, MIN(at) since FROM catalog_prices WHERE nv_mid=?", (nv_mid,)).fetchone()
    b = c.execute("SELECT MIN(deal_price) m, COUNT(*) n FROM deals WHERE nv_mid=? AND status='ok'", (nv_mid,)).fetchone()
    lows = [x for x in (a["m"], b["m"]) if x]
    return {"low": min(lows) if lows else None, "points": (a["n"] or 0) + (b["n"] or 0), "since": a["since"]}


def add_price(c, nv_mid, price, sellers, reviews, source="search"):
    c.execute("INSERT INTO catalog_prices VALUES(?,?,?,?,?,?)", (nv_mid, now(), price, sellers, reviews, source))


def save_deal(c, art, deal, status, nv_mid=None, result=None):
    c.execute("INSERT OR REPLACE INTO deals VALUES(?,?,?,?,?,?,?,?,?,?,0)", (
        art["articleId"], datetime.fromtimestamp(art["writeDateTimestamp"] / 1000, KST).isoformat(timespec="seconds"),
        art["subject"], deal["mall"], deal["name"], deal["price"], status, nv_mid,
        json.dumps(result, ensure_ascii=False) if result else None, now()))
    c.commit()
