# 네이버 커머스 API 설정 템플릿
# 이 파일을 config.py로 복사한 후 실제 값으로 교체하세요

# OAuth 2.0 클라이언트 정보
NAVER_COMMERCE_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
NAVER_COMMERCE_CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"

# API 기본 설정
API_BASE_URL = "api.commerce.naver.com"
DEFAULT_PAGE_SIZE = 100
TOKEN_EXPIRY_HOURS = 3

# 테스트용 검색 키워드
TEST_SEARCH_TERMS = [
    "삼성",
    "iPhone", 
    "노트북",
    "스마트폰",
    "갤럭시",
    "맥북",
    "아이패드"
] 