# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Tooling for a small Naver Smartstore resale business ("마마솔루션", selling 베러데이 키즈데이 supplements: SKUs grape / apple / calmadi). Comments, logs, sheet names and user-facing text are in Korean — keep new code consistent with that.

There is no build system, test suite, or linter. "Tests" are standalone scripts (`*_test.py`) run directly with `python`.

## Environment quirks (Windows)

- Python is Anaconda at `C:\ProgramData\Anaconda3`. From Git Bash, HTTPS fails unless the Anaconda SSL DLLs are on PATH:
  `PATH="/c/ProgramData/Anaconda3/Library/bin:$PATH" python <script>.py` (plain `python` works from Anaconda Prompt). `monitor_supervisor.py` patches PATH itself for this reason.
- Secrets live in `.env` (repo root and/or `store_bi/.env`, `store_bi/worker/.env`): `WEBAPP_URL`, `WORKER_TOKEN`, `NAVER_ID`/`NAVER_PW` (cafe login), `NAVER_CLIENT_ID`/`SECRET` (Commerce API), `NAVER_SEARCH_ID`/`SECRET`. Root `config.py` (from `config.example.py`) holds Commerce API keys. All are gitignored.
- Much of the active code (`store_bi/`, root `naver_*` scripts, `monitor_supervisor.py`) is currently **untracked** in git — check `git status` before assuming a file is versioned. `store_bi/data/` (SQLite `store.db`, `app_data.json`) is gitignored.

## Architecture

The hub is a **Google Apps Script webapp** ("우리 내부 사이트", URL = `WEBAPP_URL`) backed by a Google Sheet. Source: `store_bi/web/Code.gs` + `Index.html`. The `WORKER_TOKEN` constant in `Code.gs` is the placeholder `__WORKER_TOKEN__` in source and must be replaced with the real token in the deployed copy. Each sheet tab's columns are documented in the header comment of `Code.gs`.

- Humans use `doGet` (code-name login, `CODES`).
- Programs use `doPost` with `{token, op, ...}`. Ops: `pull` / `snapshot` (worker), `crawlPull` / `lowest` (price monitor), `supPull` (supervisor), and `result` (all three, to close a request). Programs **poll** the webapp for queued requests in the `요청` tab, because the webapp cannot call out to them.

Producers / consumers around that hub:

| Component | Runs where | Role |
|---|---|---|
| `naver_lowest_price_crawler.py` | local | Core Naver Shopping parser. PC search returns HTTP 418 to bots, so it rebuilds the query against the **mobile SERP** (`m.search.naver.com`, `where=m_shop`) and parses server-rendered catalog cards (nv_mid, lowest price, shipping, seller count, rating, reviews). stdlib only. Exposes `crawl`, `annotate`, `CrawlError` for reuse. |
| `naver_price_monitor.py` | local, long-running | Crawls `SEARCH_URLS` hourly with the crawler above, appends to `naver_price_history.csv`, pushes cycles (`op: lowest`) to the `최저가`/`최저가요약` tabs, and polls every minute for [업데이트] requests. Flags: `--once`, `--interval MIN`, `--sync`, `--add-url`. Without `WEBAPP_URL`/`WORKER_TOKEN` it runs CSV-only. |
| `monitor_supervisor.py` | Windows Task Scheduler, every 1 min (pythonw) | Single pass: checks the monitor process (psutil), reports status/log tail to the site, executes [재시작]/[중지] requests, and auto-restarts the monitor (max once per 5 min, not after a manual 중지). State is in `monitor_supervisor.state.json`. |
| `store_bi/worker/worker.py` | remote fixed-IP server, cron every minute | Naver Commerce API is IP-allowlisted, so all real price changes happen here: `analyze` (competitor prices → price proposal) / `apply` (change instant discount and add-on prices, then verify), and a state snapshot every 30 minutes. |
| `store_bi/collect.py` | local | Pulls order and product history from the Commerce API into `store_bi/data/store.db`. Incremental; `--since YYYY-MM-DD`. |
| `store_bi/build_dashboard.py` → `dashboard.html`; `build_app.py` → `app.html`, `data/app_data.json` | local | Aggregate `store.db` into single-file HTML. They deliberately strip PII (region only down to 시·도, buyers anonymized). `build_app.py` imports constants (`SKUS`, `VOID`, `SHIP_COST`, `betterday_sku`) from `build_dashboard.py`. |
| `store_bi/extension/` | Chrome MV3 extension | On a 가격비교 catalog page, scrapes seller prices and posts them to the webapp (`config.js` holds `APP_URL` and the code name). |
| `store_bi/scrape/*.mjs` | local, `node --experimental-websocket catalog.mjs <catalogId>...` | Launches real headed Chrome via the CDP websocket (its own profile dir) to read catalog seller lists or probe pages for login or blocks. |

### Legacy / sourcing code

- `hotdeal/` — older Playwright pipeline: 맘이베베 Naver cafe hotdeal board → mall product title → Naver Shopping lowest price → `data/results.xlsx`, plus a Streamlit `dashboard.py`. Run from `hotdeal/`: `pip install -r requirements.txt && python -m playwright install chromium`, `python main.py [--continuous]`, `streamlit run dashboard.py`. It is often hit by Naver's captcha/verification page (`_check_verification_page` dumps `verification_page_*.png` into `hotdeal/`; these are junk).
- `맘이베베/`, `다른-사이트/` (뽐뿌, 루리웹) — old Selenium scripts kept for reference.
- `naver_commerce_api_test.py`, `catalog_detail_test.py`, `example_usage.py` — Commerce API exploration (see `NAVER_COMMERCE_API_README.md`).

## Planned direction (new-product sourcing)

New sourcing work should follow this flow: 맘이베베 hotdeal posts (login required; 뽐뿌/루리웹 out of scope) → search each product on Naver Shopping, keeping only 가격비교 catalog (nv_mid) results with the current lowest price and its history → rule-based recommendation score → show the scored list on the Apps Script webapp. Score rules, with thresholds kept in config:

- hotdeal price ≥10% below the current catalog lowest price: +2
- hotdeal price at or near the historical low: +2
- low competition: +1. Judge this by how tightly the bottom sellers' prices cluster (within ~10–1000원), **not** by seller count.
- reviews ≥300: +1

The preferred crawling library for new code is Scrapling. Reuse the mobile-SERP parsing in `naver_lowest_price_crawler.py` and the webapp push pattern (`webapp(op, **payload)`) in `naver_price_monitor.py` rather than re-inventing them.
