"""
네이버 쇼핑 크롤러 테스트 스크립트
"""
import logging
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from naver_shopping_crawler import NaverShoppingCrawler
from config import CRAWLING_CONFIG

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def setup_chrome_driver():
    """Chrome 드라이버 설정 - 접속 제한 우회 개선"""
    chrome_options = Options()
    
    # 헤드리스 모드 비활성화 (테스트시 브라우저 창 보기)
    # chrome_options.add_argument('--headless')
    
    # 기본 옵션들
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    
    # 자동화 감지 방지 강화
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # 이미지 로딩 비활성화로 속도 향상
    chrome_options.add_argument('--disable-javascript')  # JavaScript 비활성화 (일부 감지 방지)
    
    # 더 자연스러운 User-Agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 자동화 관련 옵션들 제거
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("detach", True)
    
    # 프로필 관련 설정
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--ignore-certificate-errors')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 자동화 감지 방지 스크립트들
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']})")
        
        return driver
    except Exception as e:
        print(f"Chrome 드라이버 설정 실패: {e}")
        return None

def test_naver_shopping_crawler():
    """네이버 쇼핑 크롤러 테스트 - 단계별 확인"""
    print("=== 네이버 쇼핑 크롤러 테스트 시작 ===")
    
    # 테스트할 상품 (일단 하나만)
    test_products = [
        "신라면"
    ]
    
    driver = None
    try:
        # 드라이버 설정
        driver = setup_chrome_driver()
        if not driver:
            print("❌ Chrome 드라이버 설정 실패")
            return
        
        print("✅ Chrome 드라이버 설정 완료")
        
        # 크롤러 생성
        crawler = NaverShoppingCrawler(driver)
        print("✅ 네이버 쇼핑 크롤러 생성 완료")
        
        # 각 상품 테스트
        for i, product_name in enumerate(test_products, 1):
            print(f"\n--- 테스트 {i}: {product_name} ---")
            
            # 단계별 진행
            print("1. 상품 검색 중...")
            search_success = crawler.search_product_direct_url(product_name)
            
            if not search_success:
                print(f"❌ 상품 검색 실패: {product_name}")
                
                # 현재 페이지 상태 확인
                try:
                    current_url = driver.current_url
                    page_title = driver.title
                    print(f"현재 URL: {current_url}")
                    print(f"페이지 제목: {page_title}")
                    
                    # 페이지 소스 일부 확인
                    page_source = driver.page_source[:500]
                    print(f"페이지 소스 (처음 500자): {page_source}")
                    
                except Exception as e:
                    print(f"페이지 상태 확인 실패: {e}")
                
                continue
            
            print(f"✅ 상품 검색 성공: {product_name}")
            
            # 페이지 상태 확인
            try:
                current_url = driver.current_url
                page_title = driver.title
                print(f"검색 성공 후 URL: {current_url}")
                print(f"페이지 제목: {page_title}")
            except Exception as e:
                print(f"페이지 상태 확인 실패: {e}")
            
            print("2. 정보 추출 중...")
            result = crawler.get_price_comparison_info_v2()
            
            if not result:
                print(f"❌ 정보 추출 실패: {product_name}")
                continue
            
            # 결과 출력
            print("📊 추출된 정보:")
            print(f"  • 상품명: {result.get('product_name', 'N/A')}")
            print(f"  • 가격: {result.get('price', 'N/A')}")
            print(f"  • 리뷰 수: {result.get('review_count', 'N/A')}")
            print(f"  • 링크: {result.get('naver_link', 'N/A')}")
            print(f"  • 카탈로그 ID: {result.get('catalog_id', 'N/A')}")
            
            # 성공 여부 판단
            if (result.get('product_name') != '상품명 없음' and 
                result.get('price') != '가격 정보 없음'):
                print(f"✅ {product_name} 정보 추출 성공!")
            else:
                print(f"⚠️  {product_name} 일부 정보 누락")
            
            print("-" * 50)
            
            # 추가 대기 시간
            print("3초 대기 중...")
            import time
            time.sleep(3)
        
        print("\n=== 테스트 완료 ===")
        print("브라우저를 수동으로 확인하고 싶다면 10초 후 자동 종료됩니다...")
        
        # 브라우저 확인 시간 제공
        import time
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 테스트 중단됨")
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("브라우저 종료 중...")
            driver.quit()
            print("✅ 브라우저 종료 완료")

if __name__ == "__main__":
    test_naver_shopping_crawler() 