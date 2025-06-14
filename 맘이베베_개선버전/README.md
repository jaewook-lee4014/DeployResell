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

## 📊 대시보드 사용 방법

### 1. 대시보드 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 대시보드 실행
streamlit run dashboard.py
```

### 2. 주요 기능

#### 필터링
- 📅 날짜 범위: 특정 기간의 핫딜만 확인
- 💰 가격 범위: 원하는 가격대의 상품만 필터링
- 🚚 배송비: 무료배송/유료배송 상품 선택
- 🏪 쇼핑몰: 특정 쇼핑몰의 상품만 확인
- 🔎 검색: 상품명으로 검색

#### 데이터 시각화
- 💹 가격 비교: 핫딜몰과 네이버 가격 차이 분포
- 🚚 배송비 현황: 무료배송/유료배송 비율
- 🏪 쇼핑몰 분포: 상위 10개 쇼핑몰 현황

#### 상품 정보
- 상품명과 가격
- 핫딜몰 vs 네이버 가격 비교
- 배송비 정보
- 핫딜몰/네이버쇼핑 링크

### 3. 사용 팁
- 자동 새로고침: 5분마다 자동으로 데이터 갱신
- 모바일 지원: 스마트폰에서도 확인 가능
- 링크 클릭: 상품 페이지로 바로 이동
- 가격 비교: 네이버 최저가와의 차이를 한눈에 확인

# 맘이베베 핫딜 크롤러 & 대시보드

실시간 핫딜 정보를 수집하고 분석하는 웹 대시보드입니다.

## 🚀 온라인 배포 가이드

### Streamlit Community Cloud 배포

1. **GitHub 저장소 생성**
   ```bash
   # 현재 프로젝트를 GitHub에 업로드
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

2. **Streamlit Community Cloud 배포**
   - [share.streamlit.io](https://share.streamlit.io) 방문
   - GitHub 계정으로 로그인
   - "New app" 클릭
   - Repository: `YOUR_USERNAME/YOUR_REPO_NAME`
   - Branch: `main`
   - Main file path: `맘이베베_개선버전/dashboard.py`
   - App URL: 원하는 URL 설정
   - "Deploy!" 클릭

3. **자동 배포 완료**
   - 몇 분 후 공개 URL 생성
   - 코드 변경 시 자동으로 재배포

### 기타 배포 옵션

#### Heroku (무료 플랜 종료, 유료)
```bash
# Procfile 생성 필요
echo "web: streamlit run 맘이베베_개선버전/dashboard.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile
```

#### Railway (무료 500시간/월)
- [railway.app](https://railway.app) 에서 GitHub 연동 배포

#### Render (무료)
- [render.com](https://render.com) 에서 정적 사이트 배포

## 📋 배포 전 체크리스트

- [ ] requirements.txt 파일 확인
- [ ] 민감한 정보 제거 (API 키 등)
- [ ] 데이터 파일 경로 확인
- [ ] 포트 설정 확인

## 🔧 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 대시보드 실행
streamlit run dashboard.py
```

## 📊 주요 기능

- 실시간 핫딜 정보 수집
- 가격 비교 및 할인율 계산
- 인터랙티브 필터링
- 시각적 차트 및 통계
- 반응형 웹 디자인

## 🛠️ 기술 스택

- **Backend**: Python, Pandas, BeautifulSoup
- **Frontend**: Streamlit, Plotly
- **Data**: Excel (results.xlsx)
- **Deployment**: Streamlit Community Cloud

## 📁 프로젝트 구조

```
맘이베베_개선버전/
├── dashboard.py          # 메인 대시보드
├── main.py              # 크롤러 실행
├── cafe_crawler.py      # 카페 크롤러
├── naver_shopping_crawler.py  # 네이버쇼핑 크롤러
├── utils.py             # 유틸리티 함수
├── config.py            # 설정 파일
├── requirements.txt     # 의존성
├── data/               # 데이터 저장소
│   ├── results.xlsx    # 크롤링 결과
│   └── search_info.xlsx # 검색 정보
└── logs/               # 로그 파일
    └── crawler.log
```

## 🔄 데이터 업데이트

크롤러를 실행하여 최신 데이터를 수집:

```bash
python main.py
```

## 📞 문의

프로젝트 관련 문의사항이 있으시면 GitHub Issues를 이용해주세요. 