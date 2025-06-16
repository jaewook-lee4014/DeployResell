"""
네이버 쇼핑 크롤러 향상된 테스트 스크립트 - 성공 사례 적용
"""
import logging
import sys
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from naver_shopping_crawler import NaverShoppingCrawler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def setup_enhanced_chrome_driver():
    """향상된 Chrome 드라이버 설정 - 네이버 크롤링 성공 사례 적용"""
    chrome_options = Options()
    
    # 헤드리스 모드 해제 (사용자 요청)
    # chrome_options.add_argument('--headless')
    
    # 기본 Chrome 옵션들
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    
    # 자동화 감지 방지 (성공 사례에서 가져온 설정)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    
    # 더 자연스러운 User-Agent (최신 Chrome 버전)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 자동화 관련 설정 제거
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("detach", True)
    
    # 언어 설정
    chrome_options.add_argument('--lang=ko-KR')
    
    # 추가 프라이버시 설정
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 자동화 감지 방지 스크립트들 (성공 사례에서 가져온 것들)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']})")
        
        # 추가 자연스러운 속성들
        driver.execute_script("""
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                })
            });
        """)
        
        return driver
    except Exception as e:
        print(f"Chrome 드라이버 설정 실패: {e}")
        return None

def test_direct_link_access():
    """직접 링크 접근 테스트"""
    print("=== 네이버 쇼핑 직접 링크 접근 테스트 ===")
    
    driver = None
    try:
        driver = setup_enhanced_chrome_driver()
        if not driver:
            print("❌ 드라이버 설정 실패")
            return
        
        print("✅ 향상된 Chrome 드라이버 설정 완료")
        
        # 자연스러운 접근 패턴 시뮬레이션
        print("1. 네이버 메인 페이지 접근...")
        driver.get("https://www.naver.com")
        time.sleep(random.uniform(3, 5))
        print(f"네이버 메인 페이지 제목: {driver.title}")
        
        print("2. 네이버 쇼핑 메인 페이지 접근...")
        driver.get("https://shopping.naver.com")
        time.sleep(random.uniform(3, 5))
        print(f"네이버 쇼핑 제목: {driver.title}")
        
        print("3. 검색 페이지로 이동...")
        # 테스트 URL (신라면 검색)
        test_url = "https://search.shopping.naver.com/search/all?productSet=model&query=%EC%8B%A0%EB%9D%BC%EB%A9%B4"
        
        # 더 자연스러운 이동
        driver.get(test_url)
        time.sleep(random.uniform(5, 8))
        
        print(f"최종 URL: {driver.current_url}")
        print(f"페이지 제목: {driver.title}")
        
        # 페이지 상태 확인
        page_source = driver.page_source
        
        if "접속이 일시적으로 제한" in page_source:
            print("❌ 접속 제한 감지")
            print("페이지 소스 일부:")
            print(page_source[:1000])
        else:
            print("✅ 접속 제한 없음!")
            
            # 크롤러 테스트
            print("\n4. 네이버 쇼핑 크롤러로 정보 추출 테스트...")
            crawler = NaverShoppingCrawler(driver)
            
            # 현재 페이지에서 정보 추출 시도
            result = crawler.get_price_comparison_info_v2()
            
            if result:
                print("📊 추출된 정보:")
                print(f"  • 상품명: {result.get('product_name', 'N/A')}")
                print(f"  • 가격: {result.get('price', 'N/A')}")
                print(f"  • 리뷰 수: {result.get('review_count', 'N/A')}")
                print(f"  • 링크: {result.get('naver_link', 'N/A')}")
                print(f"  • 카탈로그 ID: {result.get('catalog_id', 'N/A')}")
                
                # 성공 여부 판단
                if (result.get('product_name') != '상품명 없음' and 
                    result.get('price') != '가격 정보 없음'):
                    print("🎉 크롤링 성공!")
                else:
                    print("⚠️ 일부 정보 누락")
            else:
                print("❌ 정보 추출 실패")
                
                # 페이지 요소 수동 확인
                print("\n5. 수동 요소 확인...")
                try:
                    # 상품 관련 요소들 찾기
                    product_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/catalog/"]')
                    print(f"상품 링크 수: {len(product_elements)}")
                    
                    if product_elements:
                        print(f"첫 번째 상품 링크: {product_elements[0].get_attribute('href')}")
                        print(f"첫 번째 상품 텍스트: {product_elements[0].text[:100]}")
                    
                    # 가격 요소들 찾기
                    price_elements = driver.find_elements(By.CSS_SELECTOR, 'em')
                    price_found = 0
                    for elem in price_elements:
                        text = elem.text.strip()
                        if text and ('원' in text or ',' in text):
                            price_found += 1
                            if price_found <= 3:
                                print(f"가격 요소 {price_found}: {text}")
                    
                    print(f"총 가격 관련 요소 수: {price_found}")
                    
                except Exception as e:
                    print(f"수동 요소 확인 실패: {e}")
        
        # 사용자 확인 시간 제공
        print("\n브라우저 상태를 확인하세요. 15초 후 종료됩니다...")
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("✅ 브라우저 종료 완료")

if __name__ == "__main__":
    test_direct_link_access() 