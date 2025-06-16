"""
네이버 쇼핑 접근 대안 방법 테스트
"""
import logging
import sys
import time
import random
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def setup_chrome_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    
    # 임시 프로필 디렉토리 생성
    temp_profile = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={temp_profile}")
    
    # 기본 설정들
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1366,768')
    chrome_options.add_argument('--start-maximized')
    
    # 자동화 감지 방지
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 실제 사용자 User-Agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 언어 설정
    chrome_options.add_argument('--lang=ko-KR')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 자동화 감지 방지
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        
        return driver
    except Exception as e:
        print(f"Chrome 드라이버 설정 실패: {e}")
        return None

def test_access_method(driver, method_name, url, description):
    """접근 방법 테스트"""
    print(f"\n=== {method_name} ===")
    print(f"설명: {description}")
    print(f"URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        
        print(f"   현재 URL: {driver.current_url}")
        print(f"   페이지 제목: {driver.title}")
        
        # 페이지 상태 확인
        page_source = driver.page_source
        
        if "잠시 후 다시 확인" in page_source or "일시적으로 제한" in page_source:
            print("❌ 접근 제한 감지")
            return False
        elif "네이버" in driver.title or "NAVER" in driver.title:
            print("✅ 접근 성공!")
            
            # 검색창 찾기 시도
            search_selectors = [
                '//*[@id="input_text"]',  # 사용자 제공 xpath
                'input[name="query"]',
                'input[placeholder*="검색"]',
                'input[type="search"]',
                '.search_input input',
                'input.search',
                '#query'
            ]
            
            search_found = False
            for selector in search_selectors:
                try:
                    if selector.startswith('/'):  # xpath
                        element = driver.find_element(By.XPATH, selector)
                    else:  # css selector
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if element.is_displayed():
                        print(f"   ✅ 검색창 발견: {selector}")
                        search_found = True
                        break
                except:
                    continue
            
            if not search_found:
                print("   ⚠️ 검색창을 찾을 수 없음")
            
            return True
        else:
            print("⚠️ 예상과 다른 페이지")
            return False
            
    except Exception as e:
        print(f"❌ 접근 실패: {e}")
        return False

def test_all_alternatives():
    """모든 대안 방법 테스트"""
    print("=== 네이버 쇼핑 접근 대안 방법 테스트 ===")
    
    driver = None
    try:
        driver = setup_chrome_driver()
        if not driver:
            print("❌ 드라이버 설정 실패")
            return
        
        print("✅ Chrome 드라이버 설정 완료")
        
        # 테스트할 방법들
        test_methods = [
            {
                "name": "방법 1: 네이버 메인 → 쇼핑",
                "url": "https://www.naver.com",
                "description": "네이버 메인에서 쇼핑 메뉴 클릭"
            },
            {
                "name": "방법 2: 네이버 쇼핑 메인",
                "url": "https://shopping.naver.com",
                "description": "네이버 쇼핑 메인 페이지 직접 접근"
            },
            {
                "name": "방법 3: 네이버 쇼핑 홈",
                "url": "https://search.shopping.naver.com/home",
                "description": "사용자 제공 URL"
            },
            {
                "name": "방법 4: 네이버 쇼핑 검색",
                "url": "https://search.shopping.naver.com",
                "description": "네이버 쇼핑 검색 페이지"
            },
            {
                "name": "방법 5: 네이버 통합검색",
                "url": "https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=쇼핑",
                "description": "네이버 통합검색에서 쇼핑 검색"
            }
        ]
        
        successful_methods = []
        
        for method in test_methods:
            success = test_access_method(
                driver, 
                method["name"], 
                method["url"], 
                method["description"]
            )
            
            if success:
                successful_methods.append(method)
            
            # 각 테스트 사이 대기
            time.sleep(2)
        
        # 결과 요약
        print("\n" + "="*50)
        print("테스트 결과 요약")
        print("="*50)
        
        if successful_methods:
            print("✅ 성공한 방법들:")
            for i, method in enumerate(successful_methods, 1):
                print(f"   {i}. {method['name']}")
                print(f"      URL: {method['url']}")
            
            # 첫 번째 성공한 방법으로 검색 테스트
            print(f"\n🔍 '{successful_methods[0]['name']}'로 검색 테스트...")
            test_search_with_method(driver, successful_methods[0])
            
        else:
            print("❌ 모든 방법이 실패했습니다.")
            print("   가능한 해결책:")
            print("   1. VPN 사용")
            print("   2. 다른 네트워크 환경에서 시도")
            print("   3. 수동으로 브라우저에서 네이버 쇼핑 접근 후 쿠키 복사")
            print("   4. 네이버 API 사용 (공식 API)")
        
        print("\n브라우저를 20초간 유지합니다...")
        time.sleep(20)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("✅ 브라우저 종료 완료")

def test_search_with_method(driver, method):
    """성공한 방법으로 검색 테스트"""
    try:
        # 검색창 찾기
        search_selectors = [
            '//*[@id="input_text"]',  # 사용자 제공 xpath
            'input[name="query"]',
            'input[placeholder*="검색"]',
            'input[type="search"]',
            '.search_input input',
            'input.search',
            '#query'
        ]
        
        search_box = None
        for selector in search_selectors:
            try:
                if selector.startswith('/'):  # xpath
                    search_box = driver.find_element(By.XPATH, selector)
                else:  # css selector
                    search_box = driver.find_element(By.CSS_SELECTOR, selector)
                
                if search_box.is_displayed():
                    print(f"   검색창 사용: {selector}")
                    break
            except:
                continue
        
        if not search_box:
            print("   ❌ 검색창을 찾을 수 없음")
            return
        
        # 검색 실행
        search_term = "신라면"
        print(f"   '{search_term}' 검색 중...")
        
        search_box.click()
        time.sleep(0.5)
        search_box.clear()
        time.sleep(0.3)
        
        # 자연스러운 타이핑
        for char in search_term:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.1, 0.2))
        
        time.sleep(1)
        search_box.send_keys(Keys.RETURN)
        
        # 결과 대기
        time.sleep(5)
        
        print(f"   검색 결과 URL: {driver.current_url}")
        
        # 결과 페이지 분석
        if "search" in driver.current_url and "query" in driver.current_url:
            print("   ✅ 검색 성공!")
            
            # 상품 요소 확인
            product_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="catalog"], a[href*="product"]')
            price_elements = driver.find_elements(By.CSS_SELECTOR, 'em, .price, [class*="price"]')
            
            print(f"   상품 링크 수: {len(product_elements)}")
            print(f"   가격 요소 수: {len(price_elements)}")
            
            if product_elements and price_elements:
                print("   🎉 크롤링 가능한 페이지!")
            else:
                print("   ⚠️ 크롤링하기 어려운 구조")
        else:
            print("   ⚠️ 예상과 다른 검색 결과")
            
    except Exception as e:
        print(f"   ❌ 검색 테스트 실패: {e}")

if __name__ == "__main__":
    test_all_alternatives() 