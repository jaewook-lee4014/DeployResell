"""네이버 쇼핑 카테고리 이름표 만들기 -> data/categories.json ({ID: '식품>축산물>소고기'}).

perish.py 1단계(카테고리 이름으로 음식 제외)에 쓴다. 없어도 발굴은 돌아가고, 그때는 대분류 '식품'만 보고 상품명 키워드로 판단한다.
네이버 커머스 API 는 등록된 고정 IP 에서만 호출되므로 VM(작업기)에서 실행한다. 카테고리는 거의 안 바뀌니 가끔 한 번이면 된다.

사용 (VM):
  python fetch_categories.py                    # ../store_bi/worker/worker.py 의 Commerce 로 받아 저장
  python fetch_categories.py --from cats.json   # 다른 곳에서 받은 /v1/categories 응답(JSON 목록)으로 저장
그 다음 categories.json 을 발굴 PC 의 sourcing/data/ 에 복사하고 `run.py --reclassify`.
"""
import argparse
import json
import sys

import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", help="/v1/categories 응답 JSON 파일")
    a = ap.parse_args()
    if a.src:
        rows = json.loads(open(a.src, encoding="utf-8").read())
    else:
        sys.path.insert(0, str(config.BASE.parent / "store_bi" / "worker"))
        import worker  # noqa: E402  (.env 의 NAVER_CLIENT_ID / SECRET 사용)
        st, rows = worker.Commerce().call("GET", "/v1/categories")
        if st != 200:
            sys.exit(f"카테고리 조회 실패 ({st}): {rows}")
    out = {str(r["id"]): r["wholeCategoryName"] for r in rows if r.get("id") and r.get("wholeCategoryName")}
    p = config.BASE / "data" / "categories.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    food = sum(1 for v in out.values() if v.startswith("식품"))
    print(f"저장 {p} : 카테고리 {len(out)}개 (식품 {food}개)")


if __name__ == "__main__":
    main()
