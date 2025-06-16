from naver_commerce_api_test import NaverCommerceAPI
from config import NAVER_COMMERCE_CLIENT_ID, NAVER_COMMERCE_CLIENT_SECRET
import json

def test_first_catalog_details():
    """첫 번째 카탈로그 상세 정보 조회 테스트"""
    print("🔍 첫 번째 카탈로그 상세 정보 조회 테스트")
    print("=" * 60)
    
    # API 클라이언트 초기화
    api = NaverCommerceAPI(NAVER_COMMERCE_CLIENT_ID, NAVER_COMMERCE_CLIENT_SECRET)
    
    # 토큰 발급
    print("\n1️⃣ 토큰 발급...")
    token_result = api.get_access_token()
    
    if "error" in token_result:
        print(f"❌ 토큰 발급 실패: {token_result['error']}")
        return
    
    print(f"✅ 토큰 발급 성공!")
    
    # 테스트할 검색어들
    test_keywords = [
        "삼성 갤럭시",
        "iPhone 16",
        "맥북",
        "없는상품1234567890"  # 존재하지 않을 것 같은 상품
    ]
    
    results = {}
    
    for keyword in test_keywords:
        print(f"\n" + "─" * 50)
        print(f"🔎 검색어: '{keyword}'")
        print("─" * 50)
        
        try:
            # 첫 번째 카탈로그 상세 정보 조회
            catalog_detail = api.get_first_catalog_details(keyword)
            results[keyword] = catalog_detail
            
            # 결과 출력
            if catalog_detail.get("result") == "조회 성공":
                catalog_info = catalog_detail.get("catalog_info", {})
                print(f"✅ 결과: {catalog_detail.get('result')}")
                print(f"📋 카탈로그 상세 정보:")
                print(f"   🆔 ID: {catalog_info.get('id')}")
                print(f"   📦 상품명: {catalog_info.get('name')}")
                print(f"   🏷️ 카테고리: {catalog_info.get('category')}")
                print(f"   🏭 브랜드: {catalog_info.get('brand')}")
                print(f"   🏭 제조사: {catalog_info.get('manufacturer')}")
                print(f"   ⭐ 리뷰 개수: {catalog_info.get('reviews_count')}")
                print(f"   🏪 판매처: {catalog_info.get('sellers')}")
                print(f"   💰 가격: {catalog_info.get('prices')}")
                
                # API 제한사항 안내
                if catalog_detail.get("note"):
                    print(f"\n📝 참고사항:")
                    print(f"   {catalog_detail.get('note')}")
                    
            elif catalog_detail.get("result") == "카탈로그 없음":
                print(f"❌ 결과: {catalog_detail.get('result')}")
                print(f"📝 메시지: {catalog_detail.get('message')}")
                
            else:
                print(f"⚠️ 결과: {catalog_detail.get('result')}")
                if "catalog_info" in catalog_detail:
                    catalog_info = catalog_detail["catalog_info"]
                    print(f"📋 기본 정보:")
                    print(f"   📦 상품명: {catalog_info.get('name', 'N/A')}")
                    print(f"   🏷️ 카테고리: {catalog_info.get('category', 'N/A')}")
                
                if catalog_detail.get("note"):
                    print(f"📝 참고사항: {catalog_detail.get('note')}")
            
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            results[keyword] = {"error": str(e)}
    
    # 전체 결과 요약
    print(f"\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    success_count = 0
    no_result_count = 0
    error_count = 0
    
    for keyword, result in results.items():
        if isinstance(result, dict):
            if result.get("result") == "조회 성공":
                success_count += 1
                status = "✅ 성공"
            elif result.get("result") == "카탈로그 없음":
                no_result_count += 1
                status = "❌ 결과 없음"
            elif "error" in result:
                error_count += 1
                status = "🚫 오류"
            else:
                status = "⚠️ 부분 성공"
        else:
            error_count += 1
            status = "🚫 오류"
            
        print(f"  {keyword:<15}: {status}")
    
    print(f"\n📈 통계:")
    print(f"  성공: {success_count}개")
    print(f"  결과 없음: {no_result_count}개") 
    print(f"  오류: {error_count}개")
    print(f"  전체: {len(test_keywords)}개")
    
    return results

def save_results_to_file(results):
    """결과를 파일로 저장"""
    try:
        with open('catalog_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과가 'catalog_test_results.json' 파일로 저장되었습니다.")
    except Exception as e:
        print(f"\n❌ 파일 저장 실패: {str(e)}")

def main():
    """메인 실행 함수"""
    if (NAVER_COMMERCE_CLIENT_ID == "YOUR_CLIENT_ID_HERE" or 
        NAVER_COMMERCE_CLIENT_SECRET == "YOUR_CLIENT_SECRET_HERE"):
        print("❌ config.py에서 실제 API 키를 설정해주세요!")
        return
    
    try:
        # 테스트 실행
        results = test_first_catalog_details()
        
        # 결과 저장
        save_results_to_file(results)
        
        print(f"\n🎉 테스트 완료!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 