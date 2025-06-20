# 맘이베베 크롤러 - Playwright 기반 🚀

네이버 카페 "맘이베베"에서 핫딜 정보를 수집하고 네이버쇼핑 최저가를 검색하는 자동화 크롤러입니다.

## ✨ 주요 특징

- **Playwright 기반**: 최신 웹 자동화 기술로 안정적인 크롤링
- **봇 감지 우회**: 고급 자동화 감지 방지 기능
- **실시간 모니터링**: 새로운 핫딜 게시글 자동 감지
- **가격 비교**: 네이버쇼핑 최저가 자동 검색
- **Streamlit 대시보드**: 웹 기반 모니터링 인터페이스

## 🛠️ 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Playwright 브라우저 설치

```bash
python -m playwright install chromium
```

### 3. 설정 파일 생성

`config.py`에서 다음 설정을 확인/수정하세요:

```python
# 네이버 카페 설정
CAFE_CONFIG = {
    'club_id': '10050146',  # 맘이베베 카페 ID
    'menu_id': '399',       # 핫딜 게시판 ID
    'max_pages': 3          # 크롤링할 최대 페이지 수
}

# 네이버쇼핑 설정
NAVER_SHOPPING_CONFIG = {
    'search_delay': 2,      # 검색 간 지연 시간
    'max_retries': 3        # 최대 재시도 횟수
}
```

## 🚀 사용법

### 단일 실행

```bash
python main.py
```

### 지속적 실행

```bash
python main.py --continuous
```

### 네이버 쇼핑 테스트

```bash
python naver_shopping_test.py
```

### 대시보드 실행

```bash
streamlit run dashboard.py
```

## 📁 프로젝트 구조

```
hotdeal/
├── main.py                     # 메인 실행 파일
├── config.py                   # 설정 파일
├── requirements.txt            # 의존성 목록
├── cafe_crawler.py            # 네이버 카페 크롤러
├── shopping_mall_crawler.py   # 쇼핑몰 크롤러
├── naver_shopping_crawler.py  # 네이버쇼핑 크롤러
├── utils.py                   # 유틸리티 함수
├── dashboard.py               # Streamlit 대시보드
├── naver_shopping_test.py     # 테스트 파일
└── data/                      # 데이터 저장 폴더
    ├── search_info.json       # 검색 정보
    └── results.xlsx           # 크롤링 결과
```

## 🔧 핵심 기능

### 1. 네이버 카페 크롤링
- 새로운 핫딜 게시글 자동 감지
- 제품명, 가격, 쇼핑몰 링크 추출
- iframe 처리 및 댓글 링크 추출

### 2. 쇼핑몰 크롤러
- 다양한 쇼핑몰 지원 (쿠팡, G마켓, 옥션 등)
- 상품명 자동 추출
- 동적 셀렉터 지원

### 3. 네이버쇼핑 검색
- 자연스러운 네비게이션으로 검색
- 가격, 리뷰수, 상품명 추출
- 봇 감지 우회 기능

### 4. 데이터 관리
- Excel 파일로 결과 저장
- 중복 검색 방지
- 진행 상황 로깅

## ⚙️ 고급 설정

### 브라우저 설정
- 헤드리스 모드 지원
- 사용자 에이전트 설정
- 자동화 감지 방지

### 크롤링 설정
```python
CRAWLING_CONFIG = {
    'sleep_between_requests': 3,   # 요청 간 지연
    'sleep_after_cycle': 1800,     # 사이클 간 지연 (30분)
    'max_retries': 3,              # 최대 재시도
    'page_load_timeout': 30        # 페이지 로드 타임아웃
}
```

## 🔍 모니터링

### 로그 확인
```bash
tail -f logs/crawler.log
```

### 대시보드 접속
브라우저에서 `http://localhost:8501` 접속

## 🛡️ 봇 감지 우회

- **자연스러운 네비게이션**: 메인 페이지 → 쇼핑 → 검색
- **랜덤 지연**: 인간과 유사한 행동 패턴
- **User-Agent 설정**: 실제 브라우저 모방
- **JavaScript 실행**: webdriver 속성 제거

## 📊 지원 쇼핑몰

- 쿠팡 (coupang.com)
- G마켓 (gmarket.co.kr)
- 옥션 (auction.co.kr)
- 11번가 (11st.co.kr)
- 위메프 (wemakeprice.co.kr)
- 티몬 (tmon.co.kr)
- 롯데온 (lotteon.com)
- 기타 다수

## 🚨 주의사항

1. **이용 약관 준수**: 각 사이트의 이용약관을 반드시 확인하세요
2. **적절한 지연**: 서버 부하를 방지하기 위해 적절한 지연을 설정하세요
3. **개인정보 보호**: 수집된 데이터의 개인정보를 적절히 보호하세요
4. **상업적 이용**: 상업적 목적 사용 시 해당 사이트의 허가를 받으세요

## 🔄 업데이트 내역

### v2.0.0 (2024-12)
- **Selenium → Playwright 전환**: 성능 및 안정성 대폭 향상
- **봇 감지 우회 강화**: 고급 자동화 감지 방지
- **비동기 처리**: 더 빠른 크롤링 속도
- **코드 정리**: 불필요한 테스트 파일 제거

### v1.0.0
- 초기 Selenium 기반 버전

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

## 📞 문의

문제가 있거나 개선사항이 있다면 이슈를 등록해주세요.

---

**⚠️ 면책조항**: 이 도구는 교육 및 연구 목적으로 제작되었습니다. 사용자는 관련 법률과 이용약관을 준수할 책임이 있습니다. 