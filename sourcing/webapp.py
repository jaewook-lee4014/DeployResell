"""내부 사이트(Apps Script 웹앱) 통신. naver_price_monitor.py 의 webapp() 과 같은 방식 (doPost + 302 직접 따라가기)."""
import json
import os
import time
import urllib.error
import urllib.request

import config


def load_env():
    env = {}
    for path in (config.BASE.parent / ".env", config.BASE.parent / "store_bi" / ".env"):
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k.strip(), v.strip())
    for k in ("WEBAPP_URL", "WORKER_TOKEN"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


ENV = load_env()
ON = bool(ENV.get("WEBAPP_URL") and ENV.get("WORKER_TOKEN"))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def call(op, **payload):
    body = json.dumps({"token": ENV["WORKER_TOKEN"], "op": op, **payload}, ensure_ascii=False).encode("utf-8")
    opener = urllib.request.build_opener(_NoRedirect)
    text = ""
    for attempt in range(3):
        req = urllib.request.Request(ENV["WEBAPP_URL"], data=body, headers={"Content-Type": "application/json"})
        try:
            try:
                with opener.open(req, timeout=60) as r:
                    text = r.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                if e.code not in (301, 302, 303, 307):
                    raise
                with urllib.request.urlopen(e.headers["Location"], timeout=60) as r:
                    text = r.read().decode("utf-8")
            d = json.loads(text)
            break
        except urllib.error.HTTPError as e:
            if attempt == 2 or not (e.code == 404 or e.code >= 500):
                raise
            time.sleep(5 * (attempt + 1))
        except json.JSONDecodeError:
            if attempt == 2:
                raise RuntimeError(f"웹사이트가 JSON 이 아닌 응답을 보냄: {text[:120]!r}")
            time.sleep(5 * (attempt + 1))
        except OSError as e:
            if attempt == 2:
                raise RuntimeError(f"웹사이트 연결 실패: {type(e).__name__}: {e}")
            time.sleep(5 * (attempt + 1))
    if not d.get("ok"):
        raise RuntimeError(f"웹사이트 응답 오류: {d.get('error')}")
    return d
