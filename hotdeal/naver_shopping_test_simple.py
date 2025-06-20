"""
네이버 쇼핑 크롤러 간단 테스트 - 단일 상품
"""
import asyncio
from naver_shopping_crawler import NaverShoppingCrawler


async def test_single_product():
    """단일 상품 검색 테스트"""
    print("🚀 네이버 쇼핑 단일 상품 테스트 시작")
    print("=" * 40)
    
    try:
        crawler = NaverShoppingCrawler()
        
        # 브라우저 설정 (헤드리스 모드 비활성화)
        if not await crawler.setup_browser():
            print("❌ 브라우저 설정 실패")
            return False
        
        print("✅ 브라우저 설정 완료")
        
        # 테스트 상품 검색
        test_product = "갤럭시 S24"
        print(f"🔍 검색 상품: {test_product}")
        
        # 상품 검색 실행
        if await crawler.search_product_direct_url(test_product):
            print("✅ 검색 성공")
            
            # 상품 정보 추출
            result = await crawler.get_price_comparison_info_v2()
            
            if result:
                print(f"\n📱 상품명: {result['product_name']}")
                print(f"💰 최저가: {result['price']}")
                print(f"⭐ 리뷰수: {result['review_count']}")
                print(f"ℹ️  정보: {result['delivery_info']}")
                
                # 쇼핑몰별 가격 정보
                mall_prices = result.get('mall_prices', [])
                print(f"ℹ️  정보: 가격비교 상세 (총 {len(mall_prices)}개 쇼핑몰)")
                
                if mall_prices:
                    print("\n🏪 쇼핑몰별 가격 정보:")
                    for i, mall_info in enumerate(mall_prices[:5], 1):  # 상위 5개만 표시
                        print(f"  {i}. {mall_info['mall_name']}: {mall_info['price']} (배송: {mall_info['delivery']})")
                else:
                    print("\n❌ 쇼핑몰별 가격 정보 없음")
                    
            else:
                print("❌ 상품 정보 추출 실패")
                
        else:
            print("❌ 검색 실패")
            
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            if 'crawler' in locals():
                await crawler.close()
        except:
            pass
    
    print("\n✅ 테스트 완료")
    return True


def main():
    """메인 실행"""
    asyncio.run(test_single_product())


if __name__ == "__main__":
    main() 