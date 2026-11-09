"""perish.py 확인: .venv/Scripts/python test_perish.py"""
import sys

import perish

FOOD = {"l": perish.FOOD}
BABY = {"l": perish.BABY}
LIVING = {"l": "50000008"}

CASES = [
    # (상품명, 카테고리, 제외되어야 하나)
    ("한우 1++ 등심 500g", FOOD, True),
    ("비비고 왕교자 1.05kg 냉동", FOOD, True),
    ("서울우유 1L 6팩", FOOD, True),
    ("매일 멸균우유 200ml 24팩", FOOD, False),          # 멸균 = 상온
    ("바나나맛우유 240ml 8개", FOOD, True),
    ("빙그레 바나나맛 젤리", FOOD, False),
    ("요거트맛 젤리 20개", FOOD, False),
    ("덴마크 드링킹요구르트 12개", FOOD, True),
    ("치즈볼 과자 6봉", FOOD, False),
    ("오뚜기 진라면 매운맛 40개", FOOD, False),
    ("김치라면 20개", FOOD, False),
    ("종가 포기김치 5kg", FOOD, True),
    ("노르웨이 생연어 500g", FOOD, True),
    ("새우깡 90g 20개", FOOD, False),
    ("제주 감귤 5kg", FOOD, True),
    ("사과 3kg 가정용", FOOD, True),
    ("베러데이 키즈데이 사과맛 1100mg 90캡슐", FOOD, False),
    ("떡뻥 쌀과자 10개", FOOD, False),
    ("실온 닭가슴살 30팩", FOOD, False),                # 상온 보관 표시
    ("냉동건조 딸기 칩", FOOD, False),
    ("대란 계란 30구", FOOD, True),
    ("1번 유정란 60구", FOOD, True),
    ("과일꾼 대봉감 5kg 20과내", FOOD, True),
    ("오뚜기 당을줄인 딸기쨈290g", FOOD, False),
    ("포도 봉봉 제로 340ml 24개", FOOD, False),
    ("햇반 210g 36개", FOOD, False),
    ("맥심 모카골드 스틱커피 400T", FOOD, False),
    ("베베쿡 냉동 이유식 큐브", BABY, True),            # 출산/육아라도 이유식이면 음식으로 본다
    ("베베쿡 실온 이유식 파우치 10개", BABY, False),
    ("하기스 네이처메이드 기저귀 4단계", BABY, False),
    ("냉동실 정리 용기 10개", LIVING, False),           # 음식이 아니면 판단 안 함
    ("냉장고 탈취제", LIVING, False),
    ("한우 선물세트", None, True),                      # 카테고리 모르면 음식이 분명한 말만
    ("냉장고 탈취제", None, False),
    ("비비고 왕교자 냉동", None, False),                # 카테고리 모르면 '냉동'만으로는 제외 안 함 (사람이 본다)
    ("한우 선물세트", LIVING, False),                   # 카테고리가 음식이 아니면 판단 안 함
]


def main():
    fail = 0
    for name, cat, want in CASES:
        r = perish.classify([name], cat)
        ok = r["excluded"] == want
        fail += not ok
        print(("PASS " if ok else "FAIL ") + f"{name!r:42} 제외={r['excluded']!s:5} {r['why']}")

    # 1단계: 카테고리 이름표가 있을 때
    perish._names = {"1": "식품>축산물>소고기", "2": "식품>과자/베이커리>과자>쿠키", "3": "식품>과자/베이커리>빵",
                     "4": "식품>농산물>쌀", "5": "출산/육아>이유식>냉동이유식", "6": "식품>건강식품>비타민"}
    for name, cid, want in [("호주산 척롤", "1", True), ("버터쿠키 틴", "2", False), ("우리밀 통밀식", "3", True),
                            ("신동진 쌀 10kg", "4", False), ("아기 큐브", "5", True), ("키즈 비타민", "6", False)]:
        r = perish.classify([name], {"l": "50000006" if cid != "5" else perish.BABY, "ss": cid})
        ok = r["excluded"] == want
        fail += not ok
        print(("PASS " if ok else "FAIL ") + f"[카테고리 {perish._names[cid]}] {name} 제외={r['excluded']} {r['why']}")
    r = perish.classify(["호주산 척롤"], {"l": "50000006", "ss": "1"})
    fail += not (r["stage"] == "category" and r["category"] == "식품>축산물>소고기")
    perish._names = None
    print("실패", fail)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
