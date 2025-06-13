"""
맘이베베 크롤러 설정 파일
"""
import os
from pathlib import Path

# 기본 설정
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# 네이버 카페 설정
CAFE_CONFIG = {
    'base_url': 'https://cafe.naver.com/맘이베베/ArticleList.nhn?search.clubid=29434212',
    'club_id': '29434212',
    'menu_id': '2',
    'max_pages': 100
}

# 파일 경로 설정
FILES = {
    'search_info': DATA_DIR / "search_info.xlsx",
    'results': DATA_DIR / "results.xlsx",
    'chromedriver': "/opt/homebrew/bin/chromedriver"  # macOS 기본 경로
}

# 크롤링 설정
CRAWLING_CONFIG = {
    'implicit_wait': 10,
    'page_load_timeout': 30,
    'sleep_between_requests': 1,
    'sleep_after_cycle': 600,  # 10분
    'max_retries': 3
}

# 지원 쇼핑몰 XPath 설정
SHOPPING_MALL_SELECTORS = {
    'auction': [
        '/html/body/div[9]/div[2]/div[2]/form/h1',
        '//*[@id="frmMain"]/h1'
    ],
    'lotteon': [
        '/html/body/div[1]/main/div/div[1]/div[2]/div[1]/div[2]/h1',
        '/html/body/div[1]/main/div/div[1]/div[2]/div[1]/div[3]/h1',
        '//*[@id="stickyTopParent"]/div[2]/div[2]/div[3]/h1'
    ],
    'wemakeprice': [
        '/html/body/div[2]/div[2]/div/div[1]/div[3]/div[1]/div[2]/div[1]/h3',
        '//*[@id="_infoDescription"]/div[1]/h3'
    ],
    'gmarket': [
        '/html/body/div[4]/div[2]/div[2]/div[1]/div/div[1]/h1',
        '/html/body/div[1]/div[4]/div[2]/div[1]/div[2]/div[2]/div[2]/div[1]/h3',
        '//*[@id="goodsDetailTab"]/div[2]/div/div[3]/h3',
        '/html/body/div[1]/div[4]/div[2]/div[1]/div[2]/div/div[2]/div[1]/h3'
    ],
    'gs': [
        '/html/body/div[4]/div[1]/section[1]/h1',
        '//*[@id="mainInfo"]/div[1]/section[1]/h1'
    ],
    'tmon': [
        '/html/body/div[3]/div[2]/div/div/section[1]/section[1]/section[1]/div[3]/article[1]/div[2]/h2',
        '/html/body/div[2]/section[1]/section[1]/div[4]/article[1]/div[2]/h2',
        '/html/body/div[2]/div/div/div/section[1]/section[1]/section[1]/div[3]/article[1]/div[2]/h2',
        '/html/body/div[2]/div/div/div[1]/div[3]/div[1]/p[1]'
    ],
    '11st': [
        '/html/body/div[2]/div[3]/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[3]/h1',
        '/html/body/div[2]/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[2]/h1',
        '//*[@id="layBodyWrap"]/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[2]/h1'
    ],
    'interpark': [
        '/html/body/div[1]/div[5]/div/div[2]/div/div/div[2]/h2/span[2]'
    ],
    'coupang': [
        '/html/body/div[1]/section/div[1]/div/div[3]/div[3]/h2'
    ],
    'naver': [
        '/html/body/div/div/div[2]/div[2]/div[2]/div[2]/fieldset/div[2]/div[1]/h3',
        '/html/body/div/div/div[3]/div/div[1]/h2',
        '/html/body/div/div/div[3]/div[2]/div[2]/div/div[2]/div[2]/fieldset/div[1]/div[1]/h3',
        '/html/body/div/div/div[2]/div/div[2]/div/div[2]/div[2]/fieldset/div[1]/div[2]/div/strong/span[2]'
    ],
    'brand.naver': [
        '/html/body/div/div/div[2]/div/div[2]/div/div[2]/div[2]/fieldset/div[1]/div[1]/h3'
    ],
    'kakao': [
        '/html/body/fu-app-root/fu-talkstore-wrapper/div/div/fu-pw-product-detail/div/div[1]/strong'
    ],
    'yes24': [
        '/html/body/div/div[4]/div[2]/div[1]/div/h2'
    ],
    'nsmall': [
        '/html/body/div/div[1]/div/div/section[1]/div[2]/div[1]/h3'
    ],
    'ssg': [
        '/html/body/div[4]/div[6]/div[2]/div[1]/div[2]/div[2]/h2',
        '/html/body/div[4]/div[6]/div/div[2]/div[1]/div[2]/div[2]/h2'
    ]
}

# 네이버 쇼핑 설정
NAVER_SHOPPING_CONFIG = {
    'base_url': 'https://shopping.naver.com/',
    'search_input_xpath': '//*[@id="_verticalGnbModule"]/div/div[2]/div/div[2]/div/div[2]/form/fieldset/div/input',
    'search_button_xpath': '//*[@id="_verticalGnbModule"]/div/div[2]/div/div[2]/div/div[2]/form/fieldset/div/button[2]',
    'price_compare_xpath': '//*[@id="__next"]/div/div[2]/div/div[3]/div[1]/div[1]/ul/li[2]/a'
}

# 로깅 설정
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': LOGS_DIR / 'crawler.log'
}

# Chrome 드라이버 옵션
CHROME_OPTIONS = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--window-size=1920,1080',
    '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# 정규식 패턴
REGEX_PATTERNS = {
    'url': r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»""'']))",
    'price_6': r'[\S\s]*([0-9]{6}원)[\S\s]*',
    'price_5': r'[\S\s]*([0-9]{5}원)[\S\s]*',
    'price_4': r'[\S\s]*([0-9]{4}원)[\S\s]*',
    'price_6_no_won': r'[\S\s]*([0-9]{6})[\S\s]*',
    'price_5_no_won': r'[\S\s]*([0-9]{5})[\S\s]*',
    'price_4_no_won': r'[\S\s]*([0-9]{4})[\S\s]*'
} 