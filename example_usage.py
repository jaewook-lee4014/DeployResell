from naver_commerce_api_test import NaverCommerceAPI
from config import NAVER_COMMERCE_CLIENT_ID, NAVER_COMMERCE_CLIENT_SECRET, TEST_SEARCH_TERMS
import json

def example_basic_usage():
    """기본 사용 예제"""
    print("📌 기본 사용 예제")
    print("=" * 40)
    
    # API 클라이언트 초기화
    api = NaverCommerceAPI(NAVER_COMMERCE_CLIENT_ID, NAVER_COMMERCE_CLIENT_SECRET)
    
    # 1. 토큰 발급
    print("\n1️⃣ 토큰 발급...")
    token_result = api.get_access_token()
    
    if "error" in token_result:
        print(f"❌ 토큰 발급 실패: {token_result['error']}")
        return
    
    # 2. 카탈로그 검색
    print("\n2️⃣ 카탈로그 검색...")
    search_term = "삼성"
    catalog_result = api.get_catalog_list(search_term, page=1, size=5)
    
    if "error" not in catalog_result:
        print(f"✅ '{search_term}' 검색 결과: {catalog_result.get('totalElements', 0)}개")
        
        # 결과 상세 출력
        contents = catalog_result.get('contents', [])
        for i, item in enumerate(contents):
            print(f"\n  📦 상품 {i+1}:")
            print(f"     ID: {item.get('id')}")
            print(f"     이름: {item.get('name')}")
            print(f"     카테고리: {item.get('wholeCategoryName')}")
            print(f"     브랜드: {item.get('brandName')}")
            print(f"     제조사: {item.get('manufacturerName')}")
    else:
        print(f"❌ 검색 실패: {catalog_result['error']}")

def example_multiple_searches():
    """여러 검색어로 테스트하는 예제"""
    print("\n📌 다중 검색 예제")
    print("=" * 40)
    
    api = NaverCommerceAPI(NAVER_COMMERCE_CLIENT_ID, NAVER_COMMERCE_CLIENT_SECRET)
    
    # 토큰 발급
    token_result = api.get_access_token()
    if "error" in token_result:
        print(f"❌ 토큰 발급 실패: {token_result['error']}")
        return
    
    # 여러 검색어로 테스트
    search_results = {}
    
    for term in TEST_SEARCH_TERMS[:3]:  # 처음 3개만 테스트
        print(f"\n🔍 '{term}' 검색 중...")
        result = api.get_catalog_list(term, page=1, size=10)
        
        if "error" not in result:
            count = result.get('totalElements', 0)
            search_results[term] = count
            print(f"   결과: {count}개")
        else:
            search_results[term] = 0
            print(f"   오류: {result['error']}")
    
    # 결과 요약
    print("\n📊 검색 결과 요약:")
    for term, count in search_results.items():
        print(f"  {term}: {count:,}개")

def example_detailed_product_info():
    """상품 상세 정보 조회 예제"""
    print("\n📌 상품 상세 정보 조회 예제")
    print("=" * 40)
    
    api = NaverCommerceAPI(NAVER_COMMERCE_CLIENT_ID, NAVER_COMMERCE_CLIENT_SECRET)
    
    # 토큰 발급
    token_result = api.get_access_token()
    if "error" in token_result:
        print(f"❌ 토큰 발급 실패: {token_result['error']}")
        return
    
    # 먼저 카탈로그에서 상품 찾기
    search_result = api.get_catalog_list("iPhone", page=1, size=5)
    
    if "error" not in search_result and search_result.get('contents'):
        # 첫 번째 상품의 상세 정보 가져오기
        first_product = search_result['contents'][0]
        product_id = first_product.get('id')
        
        print(f"\n📱 상품 ID {product_id}의 상세 정보:")
        print(f"  이름: {first_product.get('name')}")
        print(f"  카테고리: {first_product.get('wholeCategoryName')}")
        print(f"  브랜드: {first_product.get('brandName')}")
        print(f"  제조사: {first_product.get('manufacturerName')}")
        
        # JSON 형태로도 출력
        print(f"\n📄 JSON 형태:")
        print(json.dumps(first_product, indent=2, ensure_ascii=False))
        
    else:
        print("❌ 검색 결과가 없거나 오류가 발생했습니다.")

def example_pagination():
    """페이지네이션 예제"""
    print("\n📌 페이지네이션 예제")
    print("=" * 40)
    
    api = NaverCommerceAPI(NAVER_COMMERCE_CLIENT_ID, NAVER_COMMERCE_CLIENT_SECRET)
    
    # 토큰 발급
    token_result = api.get_access_token()
    if "error" in token_result:
        print(f"❌ 토큰 발급 실패: {token_result['error']}")
        return
    
    search_term = "삼성"
    page_size = 5
    
    # 첫 번째 페이지 조회
    result = api.get_catalog_list(search_term, page=1, size=page_size)
    
    if "error" not in result:
        total_elements = result.get('totalElements', 0)
        total_pages = result.get('totalPages', 0)
        
        print(f"🔍 '{search_term}' 검색 결과:")
        print(f"  전체 개수: {total_elements:,}개")
        print(f"  전체 페이지: {total_pages:,}페이지")
        print(f"  페이지 크기: {page_size}개")
        
        # 처음 2페이지만 조회해보기
        for page in range(1, min(3, total_pages + 1)):
            print(f"\n📄 {page}페이지:")
            page_result = api.get_catalog_list(search_term, page=page, size=page_size)
            
            if "error" not in page_result:
                contents = page_result.get('contents', [])
                for i, item in enumerate(contents):
                    print(f"  {(page-1)*page_size + i + 1}. {item.get('name')}")
            else:
                print(f"  오류: {page_result['error']}")

def main():
    """모든 예제 실행"""
    print("🚀 네이버 커머스 API 사용 예제 모음")
    print("=" * 50)
    
    if (NAVER_COMMERCE_CLIENT_ID == "YOUR_CLIENT_ID_HERE" or 
        NAVER_COMMERCE_CLIENT_SECRET == "YOUR_CLIENT_SECRET_HERE"):
        print("❌ config.py에서 실제 API 키를 설정해주세요!")
        print("NAVER_COMMERCE_CLIENT_ID와 NAVER_COMMERCE_CLIENT_SECRET를 실제 값으로 교체하세요.")
        return
    
    try:
        # 기본 사용 예제
        example_basic_usage()
        
        # 다중 검색 예제
        example_multiple_searches()
        
        # 상품 상세 정보 예제
        example_detailed_product_info()
        
        # 페이지네이션 예제
        example_pagination()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류 발생: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 모든 예제 실행 완료")

if __name__ == "__main__":
    main() 