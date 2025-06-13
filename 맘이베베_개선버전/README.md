# 맘이베베 크롤러 개선버전

네이버 카페 "맘이베베"의 핫딜 정보를 자동으로 수집하고 분석하는 웹 크롤링 프로그램의 개선된 버전입니다.

## 🚀 주요 개선사항

### 기존 버전 대비 개선점
- **모듈화된 구조**: 기능별로 클래스를 분리하여 유지보수성 향상
- **최신 Selenium 4.x**: deprecated된 메서드들을 최신 문법으로 교체
- **설정 파일 분리**: 하드코딩된 값들을 config.py로 분리
- **로깅 시스템**: 체계적인 로그 관리로 디버깅 용이성 향상
- **타입 힌트**: Python 타입 힌트 적용으로 코드 안정성 향상
- **에러 처리 강화**: 재시도 로직과 예외 처리 개선
- **크롤링 효율성**: 불필요한 요청 최소화 및 대기 시간 최적화

## 📁 프로젝트 구조

```
맘이베베_개선버전/
├── config.py                    # 설정 파일
├── utils.py                     # 유틸리티 함수들
├── cafe_crawler.py              # 네이버 카페 크롤러
├── shopping_mall_crawler.py     # 쇼핑몰 크롤러
├── naver_shopping_crawler.py    # 네이버쇼핑 크롤러
├── main.py                      # 메인 실행 파일
├── requirements.txt             # 패키지 의존성
├── README.md                   # 프로젝트 설명
├── data/                       # 데이터 저장 폴더
│   ├── search_info.xlsx        # 검색 상태 정보
│   └── results.xlsx            # 크롤링 결과
└── logs/                       # 로그 파일 폴더
    └── crawler.log             # 크롤링 로그
```

## 🛠 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. Chrome 브라우저 및 ChromeDriver 설치

#### macOS (Homebrew)
```bash
# Chrome 브라우저 설치 (이미 설치된 경우 생략)
brew install google-chrome

# ChromeDriver 설치
brew install chromedriver
```

#### 수동 설치
1. [Chrome 브라우저](https://www.google.com/chrome/) 설치
2. [ChromeDriver](https://chromedriver.chromium.org/) 다운로드 후 PATH에 추가

### 3. 설정 수정 (필요시)
`config.py` 파일에서 다음 설정들을 환경에 맞게 수정:

- **ChromeDriver 경로**: `FILES['chromedriver']`
- **크롤링 주기**: `CRAWLING_CONFIG['sleep_after_cycle']`
- **재시도 횟수**: `CRAWLING_CONFIG['max_retries']`

## 🚀 사용법

### 1. 단일 실행 (테스트용)
```bash
python main.py --once
```

### 2. 지속적 실행 (운영용)
```bash
python main.py
```

### 3. 백그라운드 실행 (macOS/Linux)
```bash
nohup python main.py > output.log 2>&1 &
```

## 📊 지원 쇼핑몰

- 🛒 **옥션** (auction)
- 🏪 **롯데온** (lotteon)
- 💰 **위메프** (wemakeprice)
- 🏬 **G마켓** (gmarket)
- 🏪 **GS샵** (gs)
- 🎯 **티몬** (tmon)
- 🏬 **11번가** (11st)
- 🎪 **인터파크** (interpark)
- 📦 **쿠팡** (coupang)
- 🔍 **네이버쇼핑** (naver)
- 🏪 **네이버브랜드스토어** (brand.naver)
- 💬 **카카오톡스토어** (kakao)
- 📚 **YES24** (yes24)
- 📺 **NS홈쇼핑** (nsmall)
- 🛍 **SSG** (ssg)

## 📈 수집 데이터

| 컬럼명 | 설명 |
|--------|------|
| 시간 | 크롤링 수행 시간 |
| 핫딜몰 | "맘이베베" 고정값 |
| 게시글 id | 카페 게시글 고유 번호 |
| 핫딜몰 링크 | 원본 게시글 URL |
| 핫딜몰 제품명 | 게시글 제목 |
| 보정 제품명 | 정제된 상품명 |
| 쇼핑몰 주소 | 실제 쇼핑몰 링크 |
| 쇼핑몰 제목 | 쇼핑몰에서 추출한 상품명 |
| 네이버 주소 | 네이버쇼핑 상품 페이지 |
| 네이버 번호 | 네이버 카탈로그 ID |
| 네이버 제목 | 네이버쇼핑 상품명 |
| 네이버 가격 | 네이버쇼핑 최저가 |
| 네이버 배송료 | 배송비 정보 |
| 네이버 리뷰 개수 | 상품 리뷰 수 |

## 🔧 주요 기능

### 1. 증분 크롤링
- 이전 크롤링 이후의 새 게시글만 수집
- 중복 수집 방지로 효율적 운영

### 2. 에러 복구
- 네트워크 오류 시 자동 재시도
- 페이지 구조 변경에 대한 fallback 처리

### 3. 로깅 시스템
- 파일과 콘솔에 동시 로그 출력
- 크롤링 진행 상황 실시간 모니터링

### 4. 설정 관리
- 중앙화된 설정으로 쉬운 커스터마이징
- 환경별 설정 분리 가능

## ⚠️ 주의사항

1. **법적 준수**: 웹 크롤링 시 해당 사이트의 robots.txt와 이용약관을 확인하세요.
2. **요청 제한**: 과도한 요청으로 서버에 부하를 주지 않도록 적절한 지연시간을 설정하세요.
3. **개인정보**: 수집된 데이터의 개인정보 보호에 주의하세요.

## 📝 로그 확인

```bash
# 실시간 로그 확인
tail -f logs/crawler.log

# 오류 로그만 확인
grep ERROR logs/crawler.log
```

## 🐛 문제 해결

### ChromeDriver 관련 오류
```bash
# ChromeDriver 버전 확인
chromedriver --version

# Chrome 브라우저 버전 확인 (macOS)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

### 권한 오류 (macOS)
```bash
# ChromeDriver 실행 권한 부여
xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
```

## 📜 라이선스

이 프로젝트는 개인적인 용도로만 사용하시기 바랍니다.

## 🤝 기여

버그 리포트나 기능 개선 제안은 언제든 환영합니다! 