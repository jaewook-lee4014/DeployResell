"""신상품 발굴 설정 — 숫자는 여기서만 바꾼다."""
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "data" / "sourcing.db"

# 맘이베베 핫딜방
CAFE_ID = 29434212
MENU_ID = 2
PER_PAGE = 30

# 요청 간격 (초). 네이버 검색은 너무 빨리 두드리면 막힌다.
SEARCH_DELAY = (4.0, 8.0)
CAFE_DELAY = (1.0, 2.0)

# 추천도 규칙
RULES = {
    "cheaper_pct": 10,        # 핫딜가가 카탈로그 최저가보다 이 % 이상 싸면
    "cheaper_pts": 2,
    "near_record_pct": 3,     # 우리 기록 속 과거 최저가의 +3% 이내면 '역대 최저가 수준'
    "near_record_pts": 2,
    "compete_gap_won": 1000,  # 최저가에서 이 금액 이내에 붙은 판매처를 센다
    "compete_gap_pct": 1.0,   #   (또는 최저가의 이 % 이내, 둘 중 큰 쪽)
    "compete_max": 3,         # 이 수 이상 붙어 있으면 '경쟁 심함'
    "compete_pts": 1,
    "reviews_min": 300,
    "reviews_pts": 1,
}
# 점수 합 -> 별 개수 (점수 이상이면 그 별)
STARS = [(5, 5), (4, 4), (3, 3), (2, 2), (0, 1)]

# 카탈로그 매칭 신뢰도 기준
MATCH_MIN = 0.5               # 이 점수 미만이면 '맞는 카탈로그 없음'
