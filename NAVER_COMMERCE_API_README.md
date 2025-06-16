# 네이버 커머스 API 테스트 도구

네이버 커머스 API를 활용하여 상품 정보를 조회하는 테스트 도구입니다. 기존 크롤러를 대체하기 위한 API 기반 솔루션을 제공합니다.

## 🚀 주요 기능

- **OAuth 2.0 인증**: 네이버 커머스 API 토큰 발급 및 관리
- **카탈로그 조회**: 상품명으로 카탈로그 검색
- **그룹상품 조회**: 그룹상품 상세 정보 조회
- **페이지네이션**: 대량 데이터 페이지별 조회
- **에러 처리**: 상세한 에러 정보 제공

## 📋 파일 구조

```
├── naver_commerce_api_test.py  # 메인 API 클라이언트
├── config.py                   # 설정 파일
├── example_usage.py           # 사용 예제
└── NAVER_COMMERCE_API_README.md # 이 파일
```

## 🔧 설정 방법

1. **API 키 설정**
   
   `config.py` 파일에서 실제 API 키로 변경:
   ```python
   NAVER_COMMERCE_CLIENT_ID = "실제_클라이언트_ID"
   NAVER_COMMERCE_CLIENT_SECRET = "실제_클라이언트_시크릿"
   ```

2. **의존성**
   
   Python 표준 라이브러리만 사용하므로 별도 설치 불필요:
   - `http.client`
   - `json`
   - `urllib.parse`
   - `datetime`

## 🎯 사용 방법

### 1. 기본 테스트 실행

```bash
python naver_commerce_api_test.py
```

### 2. 예제 코드 실행

```bash
python example_usage.py
```

### 3. 개별 사용

```python
from naver_commerce_api_test import NaverCommerceAPI

# API 클라이언트 초기화
api = NaverCommerceAPI("클라이언트_ID", "클라이언트_시크릿")

# 토큰 발급
token_result = api.get_access_token()

# 카탈로그 검색
catalog_result = api.get_catalog_list("삼성", page=1, size=10)

# 그룹상품 조회
group_result = api.get_group_product_info("그룹_ID")
```

## 📊 API 엔드포인트

### 1. 토큰 발급
- **URL**: `POST /external/v1/oauth2/token`
- **설명**: OAuth 2.0 인증 토큰 발급
- **유효기간**: 3시간 (10,800초)

### 2. 카탈로그 조회
- **URL**: `GET /external/v1/product-models`
- **설명**: 상품명으로 카탈로그 검색
- **파라미터**: 
  - `name` (필수): 검색할 카탈로그 이름
  - `page`: 페이지 번호 (기본값: 1)
  - `size`: 페이지 크기 (기본값: 100)

### 3. 그룹상품 조회
- **URL**: `GET /external/v2/product-groups/{groupId}`
- **설명**: 그룹상품 상세 정보 조회

## 🔍 조회 가능한 정보

카탈로그 조회를 통해 다음 정보를 얻을 수 있습니다:

```json
{
  "contents": [
    {
      "id": "카탈로그 ID",
      "name": "카탈로그명",
      "wholeCategoryName": "전체 카테고리명",
      "categoryId": "카테고리 ID",
      "manufacturerCode": "제조사 코드",
      "manufacturerName": "제조사명",
      "brandCode": "브랜드 코드",
      "brandName": "브랜드명"
    }
  ],
  "totalElements": "전체 개수",
  "totalPages": "전체 페이지 수",
  "page": "현재 페이지",
  "size": "페이지 크기"
}
```

## ⚠️ 주의사항

1. **API 제한사항**
   - 토큰 유효기간: 3시간
   - 동일 리소스에는 하나의 토큰만 발급
   - 남은 유효시간이 30분 이상이면 기존 토큰 반환

2. **에러 처리**
   - 모든 API 호출에 대해 상세한 에러 정보 제공
   - HTTP 상태 코드와 응답 메시지 포함

3. **보안**
   - API 키는 환경변수나 별도 설정 파일로 관리 권장
   - 코드에 직접 하드코딩하지 말 것

## 🔧 트러블슈팅

### 토큰 발급 실패
- 클라이언트 ID/시크릿 확인
- 네트워크 연결 상태 확인
- API 권한 설정 확인

### 카탈로그 조회 실패
- 토큰 유효성 확인
- 검색어 형식 확인
- 페이지 파라미터 범위 확인

### 응답 속도 개선
- 페이지 크기 조정 (기본 100개)
- 필요한 정보만 선별적 조회
- 토큰 재사용으로 인증 횟수 최소화

## 📈 성능 및 활용

### 크롤러 대체 장점
1. **안정성**: API 공식 지원으로 안정적
2. **효율성**: 필요한 데이터만 정확히 조회
3. **유지보수**: 웹사이트 변경에 영향받지 않음
4. **속도**: HTTP 요청 최적화로 빠른 응답

### 권장 사용 패턴
1. 토큰 캐싱으로 재사용
2. 배치 처리로 대량 데이터 효율적 조회
3. 에러 발생 시 재시도 로직 구현
4. 로그 기록으로 모니터링

## 📞 지원

네이버 커머스 API 관련 문의는 네이버 커머스 API 센터를 통해 문의하세요.

---

> **참고**: 이 도구는 네이버 커머스 API의 공식 문서를 기반으로 제작되었습니다. 최신 API 변경사항은 공식 문서를 참조하세요. 