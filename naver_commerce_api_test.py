import http.client
import json
import urllib.parse
import time
import base64
import bcrypt
from datetime import datetime, timedelta

class NaverCommerceAPI:
    def __init__(self, client_id=None, client_secret=None):
        """
        네이버 커머스 API 클라이언트 초기화
        
        Args:
            client_id (str): 네이버 커머스 API 클라이언트 ID
            client_secret (str): 네이버 커머스 API 클라이언트 시크릿
        """
        self.base_url = "api.commerce.naver.com"
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        
    def generate_signature(self, timestamp):
        """
        네이버 커머스 API 전자서명 생성
        
        Args:
            timestamp (int): 밀리초 단위 타임스탬프
            
        Returns:
            str: Base64 인코딩된 전자서명
        """
        try:
            # client_id_timestamp 형태로 password 생성
            password = f"{self.client_id}_{timestamp}"
            
            # bcrypt 해싱
            hashed = bcrypt.hashpw(password.encode('utf-8'), self.client_secret.encode('utf-8'))
            
            # base64 인코딩
            signature = base64.b64encode(hashed).decode('utf-8')
            
            return signature
        except Exception as e:
            print(f"❌ 전자서명 생성 실패: {str(e)}")
            return None

    def get_access_token(self, account_type="SELF", account_id=None):
        """
        OAuth 2.0 인증 토큰 발급 요청
        
        Args:
            account_type (str): 계정 유형 (SELF 또는 SELLER)
            account_id (str): 계정 ID (SELLER 타입일 때 필수)
            
        Returns:
            dict: 토큰 정보 또는 에러 정보
        """
        try:
            conn = http.client.HTTPSConnection(self.base_url)
            
            # 현재 시간을 밀리초 단위로 생성
            timestamp = int(time.time() * 1000)
            
            # 전자서명 생성
            client_secret_sign = self.generate_signature(timestamp)
            if not client_secret_sign:
                return {"error": "전자서명 생성 실패"}
            
            # 요청 본문 구성
            payload_data = {
                'client_id': self.client_id,
                'timestamp': timestamp,
                'client_secret_sign': client_secret_sign,
                'grant_type': 'client_credentials',
                'type': account_type
            }
            
            if account_id:
                payload_data['account_id'] = account_id
                
            payload = urllib.parse.urlencode(payload_data)
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            print(f"토큰 발급 요청 중...")
            print(f"URL: https://{self.base_url}/external/v1/oauth2/token")
            print(f"Client ID: {self.client_id}")
            print(f"Timestamp: {timestamp}")
            print(f"Type: {account_type}")
            print(f"Signature: {client_secret_sign[:50]}...")
            
            conn.request("POST", "/external/v1/oauth2/token", payload, headers)
            res = conn.getresponse()
            data = res.read()
            
            print(f"응답 상태 코드: {res.status}")
            
            response_text = data.decode("utf-8")
            print(f"응답 본문: {response_text}")
            
            if res.status == 200:
                token_info = json.loads(response_text)
                self.access_token = token_info.get('access_token')
                expires_in = token_info.get('expires_in', 10800)  # 기본 3시간
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                print(f"✅ 토큰 발급 성공!")
                print(f"Access Token: {self.access_token[:20]}...")
                print(f"Token Type: {token_info.get('token_type', 'Bearer')}")
                print(f"만료 시간: {self.token_expires_at}")
                
                return token_info
            else:
                print(f"❌ 토큰 발급 실패 (상태 코드: {res.status})")
                try:
                    error_info = json.loads(response_text)
                    return {"error": error_info, "status_code": res.status}
                except:
                    return {"error": response_text, "status_code": res.status}
                    
        except Exception as e:
            print(f"❌ 토큰 발급 중 예외 발생: {str(e)}")
            return {"error": str(e)}
            
    def is_token_valid(self):
        """토큰 유효성 확인"""
        if not self.access_token or not self.token_expires_at:
            return False
        return datetime.now() < self.token_expires_at
        
    def get_catalog_list(self, name, page=1, size=100):
        """
        카탈로그 조회
        
        Args:
            name (str): 검색할 카탈로그 이름 (필수)
            page (int): 페이지 번호 (기본값: 1)
            size (int): 페이지 크기 (기본값: 100)
            
        Returns:
            dict: 카탈로그 정보 또는 에러 정보
        """
        if not self.is_token_valid():
            print("❌ 유효한 토큰이 없습니다. 먼저 토큰을 발급받으세요.")
            return {"error": "Invalid or missing access token"}
            
        try:
            conn = http.client.HTTPSConnection(self.base_url)
            
            # 쿼리 파라미터 구성
            query_params = {
                'name': name,
                'page': page,
                'size': size
            }
            query_string = urllib.parse.urlencode(query_params)
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json;charset=UTF-8'
            }
            
            url = f"/external/v1/product-models?{query_string}"
            
            print(f"\n카탈로그 조회 요청 중...")
            print(f"URL: https://{self.base_url}{url}")
            print(f"검색어: {name}")
            print(f"페이지: {page}, 크기: {size}")
            
            conn.request("GET", url, headers=headers)
            res = conn.getresponse()
            data = res.read()
            
            print(f"응답 상태 코드: {res.status}")
            
            response_text = data.decode("utf-8")
            
            if res.status == 200:
                catalog_info = json.loads(response_text)
                print(f"✅ 카탈로그 조회 성공!")
                print(f"전체 개수: {catalog_info.get('totalElements', 0)}")
                print(f"전체 페이지 수: {catalog_info.get('totalPages', 0)}")
                
                contents = catalog_info.get('contents', [])
                if contents:
                    print(f"\n📋 조회된 카탈로그 목록 (처음 3개):")
                    for i, item in enumerate(contents[:3]):
                        print(f"  {i+1}. ID: {item.get('id')}")
                        print(f"     이름: {item.get('name')}")
                        print(f"     카테고리: {item.get('wholeCategoryName')}")
                        print(f"     브랜드: {item.get('brandName')}")
                        print(f"     제조사: {item.get('manufacturerName')}")
                        print()
                else:
                    print("조회된 카탈로그가 없습니다.")
                
                return catalog_info
            else:
                print(f"❌ 카탈로그 조회 실패 (상태 코드: {res.status})")
                print(f"응답 본문: {response_text}")
                try:
                    error_info = json.loads(response_text)
                    return {"error": error_info, "status_code": res.status}
                except:
                    return {"error": response_text, "status_code": res.status}
                    
        except Exception as e:
            print(f"❌ 카탈로그 조회 중 예외 발생: {str(e)}")
            return {"error": str(e)}
            
    def get_catalog_detail(self, catalog_id):
        """
        카탈로그 단건 조회
        
        Args:
            catalog_id (str): 카탈로그 ID
            
        Returns:
            dict: 카탈로그 상세 정보 또는 에러 정보
        """
        if not self.is_token_valid():
            print("❌ 유효한 토큰이 없습니다. 먼저 토큰을 발급받으세요.")
            return {"error": "Invalid or missing access token"}
            
        try:
            conn = http.client.HTTPSConnection(self.base_url)
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json;charset=UTF-8'
            }
            
            url = f"/external/v1/product-models/{catalog_id}"
            
            print(f"\n카탈로그 상세 정보 조회 요청 중...")
            print(f"URL: https://{self.base_url}{url}")
            print(f"카탈로그 ID: {catalog_id}")
            
            conn.request("GET", url, headers=headers)
            res = conn.getresponse()
            data = res.read()
            
            print(f"응답 상태 코드: {res.status}")
            
            response_text = data.decode("utf-8")
            
            if res.status == 200:
                catalog_detail = json.loads(response_text)
                print(f"✅ 카탈로그 상세 정보 조회 성공!")
                return catalog_detail
            else:
                print(f"❌ 카탈로그 상세 정보 조회 실패 (상태 코드: {res.status})")
                print(f"응답 본문: {response_text}")
                try:
                    error_info = json.loads(response_text)
                    return {"error": error_info, "status_code": res.status}
                except:
                    return {"error": response_text, "status_code": res.status}
                    
        except Exception as e:
            print(f"❌ 카탈로그 상세 정보 조회 중 예외 발생: {str(e)}")
            return {"error": str(e)}

    def get_first_catalog_details(self, search_term):
        """
        검색어로 첫 번째 카탈로그의 상세 정보를 조회
        
        Args:
            search_term (str): 검색할 카탈로그 이름
            
        Returns:
            dict: 카탈로그 상세 정보 또는 에러 정보
        """
        # 1. 카탈로그 목록 조회
        catalog_list = self.get_catalog_list(search_term, page=1, size=1)
        
        if "error" in catalog_list:
            return {"error": "카탈로그 목록 조회 실패", "details": catalog_list["error"]}
        
        contents = catalog_list.get('contents', [])
        if not contents:
            return {
                "search_term": search_term,
                "result": "카탈로그 없음",
                "message": f"'{search_term}' 검색 결과가 없습니다."
            }
        
        # 2. 첫 번째 카탈로그 정보
        first_catalog = contents[0]
        catalog_id = first_catalog.get('id')
        catalog_name = first_catalog.get('name')
        
        print(f"\n📋 첫 번째 카탈로그 정보:")
        print(f"   ID: {catalog_id}")
        print(f"   이름: {catalog_name}")
        print(f"   카테고리: {first_catalog.get('wholeCategoryName')}")
        print(f"   브랜드: {first_catalog.get('brandName')}")
        print(f"   제조사: {first_catalog.get('manufacturerName')}")
        
        # 3. 카탈로그 상세 정보 조회 (현재 API에서는 제한적 정보만 제공)
        catalog_detail = self.get_catalog_detail(catalog_id)
        
        if "error" in catalog_detail:
            # 카탈로그 단건 조회 실패 시 기본 정보만 반환
            return {
                "search_term": search_term,
                "result": "기본 정보만 조회됨",
                "catalog_info": {
                    "id": catalog_id,
                    "name": catalog_name,
                    "category": first_catalog.get('wholeCategoryName'),
                    "brand": first_catalog.get('brandName'),
                    "manufacturer": first_catalog.get('manufacturerName'),
                    "reviews_count": "정보 없음",
                    "sellers": "정보 없음",
                    "prices": "정보 없음"
                },
                "note": "현재 네이버 커머스 API에서는 리뷰 개수, 판매처, 가격 정보를 직접 제공하지 않습니다."
            }
        
        # 4. 결과 구성 (API 제한사항으로 인해 기본 정보만 포함)
        result = {
            "search_term": search_term,
            "result": "조회 성공",
            "catalog_info": {
                "id": catalog_id,
                "name": catalog_name,
                "category": first_catalog.get('wholeCategoryName'),
                "brand": first_catalog.get('brandName'),
                "manufacturer": first_catalog.get('manufacturerName'),
                "category_id": first_catalog.get('categoryId'),
                "brand_code": first_catalog.get('brandCode'),
                "manufacturer_code": first_catalog.get('manufacturerCode'),
                "reviews_count": "API 제한으로 조회 불가",
                "sellers": "API 제한으로 조회 불가", 
                "prices": "API 제한으로 조회 불가"
            },
            "raw_data": catalog_detail,
            "note": "네이버 커머스 API는 카탈로그 기본 정보만 제공합니다. 리뷰, 판매처, 가격 정보는 별도 API가 필요할 수 있습니다."
        }
        
        return result

def main():
    """
    테스트 실행 함수
    """
    print("🚀 네이버 커머스 API 테스트 시작")
    print("="*50)
    
    # config.py에서 API 키 가져오기
    try:
        from config import NAVER_COMMERCE_CLIENT_ID, NAVER_COMMERCE_CLIENT_SECRET
        client_id = NAVER_COMMERCE_CLIENT_ID
        client_secret = NAVER_COMMERCE_CLIENT_SECRET
    except ImportError:
        print("❌ config.py 파일이 없습니다!")
        print("config.example.py를 config.py로 복사하고 실제 API 키를 입력하세요.")
        return
    
    if client_id == "YOUR_CLIENT_ID_HERE" or client_secret == "YOUR_CLIENT_SECRET_HERE":
        print("❌ config.py에서 실제 API 키를 설정해주세요!")
        print("NAVER_COMMERCE_CLIENT_ID와 NAVER_COMMERCE_CLIENT_SECRET를 실제 값으로 교체하세요.")
        return
    
    api = NaverCommerceAPI(client_id, client_secret)
    
    # 1. 토큰 발급 테스트
    print("\n1️⃣ OAuth 2.0 토큰 발급 테스트")
    print("-" * 30)
    token_result = api.get_access_token()
    
    if "error" in token_result:
        print("토큰 발급에 실패했습니다. 클라이언트 정보를 확인해주세요.")
        return
    
    # 2. 첫 번째 카탈로그 상세 정보 조회 테스트
    print("\n2️⃣ 첫 번째 카탈로그 상세 정보 조회 테스트")
    print("-" * 50)
    
    # 테스트용 검색어들
    search_terms = ["삼성", "iPhone", "노트북"]
    
    for term in search_terms:
        print(f"\n🔍 '{term}' 첫 번째 카탈로그 상세 정보 조회...")
        catalog_detail = api.get_first_catalog_details(term)
        
        if catalog_detail.get("result") == "조회 성공":
            catalog_info = catalog_detail.get("catalog_info", {})
            print(f"✅ '{term}' 첫 번째 카탈로그 정보:")
            print(f"   📦 상품명: {catalog_info.get('name')}")
            print(f"   🏷️ 카테고리: {catalog_info.get('category')}")
            print(f"   🏭 브랜드: {catalog_info.get('brand')}")
            print(f"   🏭 제조사: {catalog_info.get('manufacturer')}")
            print(f"   ⭐ 리뷰 개수: {catalog_info.get('reviews_count')}")
            print(f"   🏪 판매처: {catalog_info.get('sellers')}")
            print(f"   💰 가격: {catalog_info.get('prices')}")
            break
        elif catalog_detail.get("result") == "카탈로그 없음":
            print(f"❌ '{term}' 검색 결과가 없습니다.")
        else:
            print(f"⚠️ '{term}' 조회 중 제한사항: {catalog_detail.get('note', '알 수 없는 오류')}")
            if "catalog_info" in catalog_detail:
                catalog_info = catalog_detail["catalog_info"]
                print(f"   📦 상품명: {catalog_info.get('name', 'N/A')}")
                print(f"   🏷️ 카테고리: {catalog_info.get('category', 'N/A')}")
            break
    
    print("\n" + "="*50)
    print("🏁 테스트 완료")

if __name__ == "__main__":
    main() 