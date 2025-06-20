"""
네이버 쇼핑 크롤러 테스트 - 쇼핑몰별 가격비교 버전
"""
import asyncio
from naver_shopping_crawler import NaverShoppingCrawler


async def test_naver_shopping():
    """네이버 쇼핑 크롤러 테스트 - 쇼핑몰별 가격 정보"""
    crawler = NaverShoppingCrawler()
    
    try:
        print("🚀 네이버 쇼핑 가격비교 크롤러 테스트 시작")
        print("=" * 60)
        
        # 테스트 상품들
        test_products = [
            "갤럭시 S24",
            "아이폰 15"
        ]
        
        # 일괄 검색 테스트 (직접 비동기 메서드 호출)
        results = await crawler._search_products_batch_async(test_products)
        
        print(f"\n📊 테스트 결과:")
        print(f"검색 상품 수: {len(test_products)}")
        print(f"결과 수: {len(results)}")
        
        for i, (product, result) in enumerate(zip(test_products, results)):
            print(f"\n{'='*50}")
            print(f"🔍 상품 {i+1}: {product}")
            print(f"{'='*50}")
            print(f"📱 상품명: {result['product_name']}")
            print(f"💰 최저가: {result['price']}")
            print(f"⭐ 리뷰수: {result['review_count']}")
            print(f"ℹ️  정보: {result['delivery_info']}")
            print(f"🔗 링크: {result['naver_link'][:80]}...")
            
            # 쇼핑몰별 가격 정보 출력
            mall_prices = result.get('mall_prices', [])
            if mall_prices:
                print(f"\n🏪 쇼핑몰별 가격 정보 ({len(mall_prices)}개):")
                print("-" * 60)
                print(f"{'순위':<4} {'쇼핑몰':<15} {'가격':<12} {'배송비':<15}")
                print("-" * 60)
                
                for idx, mall_info in enumerate(mall_prices[:10], 1):  # 상위 10개만 출력
                    mall_name = mall_info['mall_name'][:13] + "..." if len(mall_info['mall_name']) > 13 else mall_info['mall_name']
                    price = mall_info['price']
                    delivery = mall_info['delivery'][:13] + "..." if len(mall_info['delivery']) > 13 else mall_info['delivery']
                    
                    print(f"{idx:<4} {mall_name:<15} {price:<12} {delivery:<15}")
            else:
                print("\n❌ 쇼핑몰별 가격 정보 없음")
        
        print(f"\n✅ 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 실행"""
    # 새로운 이벤트 루프에서 실행
    try:
        asyncio.run(test_naver_shopping())
    except RuntimeError as e:
        if "asyncio.run() cannot be called" in str(e):
            # 이미 실행 중인 이벤트 루프가 있는 경우
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(test_naver_shopping())
            finally:
                loop.close()
        else:
            raise


if __name__ == "__main__":
    main() 