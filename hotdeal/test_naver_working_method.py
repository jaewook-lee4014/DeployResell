"""
성공한 네이버 접근 방법으로 검색 및 크롤링 테스트
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

from naver_shopping_crawler import NaverShoppingCrawler

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

def human_typing(element, text, typing_speed=0.15):
    """사람처럼 타이핑하기"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, typing_speed))

def random_delay(min_sec=1, max_sec=3):
    """랜덤 지연"""
    time.sleep(random.uniform(min_sec, max_sec))

def test_naver_main_to_shopping():
    """네이버 메인에서 쇼핑으로 이동하는 방법 테스트"""
    print("=== 네이버 메인 → 쇼핑 방법 테스트 ===")
    
    driver = None
    try:
        driver = setup_chrome_driver()
        if not driver:
            print("❌ 드라이버 설정 실패")
            return
        
        print("✅ Chrome 드라이버 설정 완료")
        
        # 1단계: 네이버 메인 페이지 접근
        print("\n1. 네이버 메인 페이지 접근...")
        driver.get("https://www.naver.com")
        random_delay(3, 5)
        
        print(f"   현재 URL: {driver.current_url}")
        print(f"   페이지 제목: {driver.title}")
        
        # 2단계: 쇼핑 메뉴 찾기 및 클릭
        print("\n2. 쇼핑 메뉴 찾기...")
        shopping_selectors = [
            'a[href*="shopping.naver.com"]',
            'a[data-clk*="sho"]',
            'a:contains("쇼핑")',
            '.service_area a[href*="shopping"]',
            '.gnb_service a[href*="shopping"]'
        ]
        
        shopping_link = None
        for selector in shopping_selectors:
            try:
                if ':contains(' in selector:
                    # JavaScript로 텍스트 포함 요소 찾기
                    shopping_link = driver.execute_script("""
                        var links = document.querySelectorAll('a');
                        for (var i = 0; i < links.length; i++) {
                            if (links[i].textContent.includes('쇼핑')) {
                                return links[i];
                            }
                        }
                        return null;
                    """)
                else:
                    shopping_link = driver.find_element(By.CSS_SELECTOR, selector)
                
                if shopping_link and shopping_link.is_displayed():
                    print(f"   ✅ 쇼핑 링크 발견: {selector}")
                    break
            except:
                continue
        
        if shopping_link:
            print("   쇼핑 메뉴 클릭...")
            shopping_link.click()
            random_delay(3, 5)
            
            print(f"   이동 후 URL: {driver.current_url}")
            print(f"   이동 후 제목: {driver.title}")
        else:
            print("   ❌ 쇼핑 메뉴를 찾을 수 없음, 직접 이동...")
            driver.get("https://shopping.naver.com")
            random_delay(3, 5)
        
        # 3단계: 쇼핑 페이지에서 검색창 찾기
        print("\n3. 쇼핑 페이지에서 검색창 찾기...")
        search_selectors = [
            '//*[@id="input_text"]',  # 사용자 제공 xpath
            'input[name="query"]',
            'input[placeholder*="검색"]',
            'input[type="search"]',
            '.search_input input',
            'input.search',
            '#query',
            'input[id*="search"]',
            'input[class*="search"]'
        ]
        
        search_box = None
        for selector in search_selectors:
            try:
                if selector.startswith('/'):  # xpath
                    search_box = driver.find_element(By.XPATH, selector)
                else:  # css selector
                    search_box = driver.find_element(By.CSS_SELECTOR, selector)
                
                if search_box.is_displayed():
                    print(f"   ✅ 검색창 발견: {selector}")
                    break
            except:
                continue
        
        if not search_box:
            print("   ❌ 검색창을 찾을 수 없음")
            print("   페이지의 모든 input 요소 확인...")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for i, inp in enumerate(inputs[:10]):  # 처음 10개만
                try:
                    print(f"     {i+1}: id={inp.get_attribute('id')}, name={inp.get_attribute('name')}, placeholder={inp.get_attribute('placeholder')}")
                except:
                    pass
            return
        
        # 4단계: 검색 실행
        print("\n4. 검색 실행...")
        search_term = "신라면"
        
        try:
            # 검색창 클릭
            search_box.click()
            random_delay(0.5, 1)
            
            # 기존 텍스트 클리어
            search_box.clear()
            random_delay(0.3, 0.5)
            
            # 자연스러운 타이핑
            print(f"   '{search_term}' 입력 중...")
            human_typing(search_box, search_term, 0.15)
            
            # 입력 완료 후 잠시 대기
            random_delay(1, 2)
            
            # 엔터 키 입력
            search_box.send_keys(Keys.RETURN)
            print("   검색 실행 완료")
            
            # 검색 결과 로딩 대기
            random_delay(5, 8)
            
        except Exception as e:
            print(f"❌ 검색 실행 실패: {e}")
            return
        
        # 5단계: 검색 결과 확인
        print("\n5. 검색 결과 확인...")
        print(f"   최종 URL: {driver.current_url}")
        print(f"   페이지 제목: {driver.title}")
        
        # 페이지 상태 분석
        page_source = driver.page_source
        
        if "접속이 일시적으로 제한" in page_source or "잠시 후 다시 확인" in page_source:
            print("❌ 검색 결과 페이지에서 접속 제한 감지")
        else:
            print("✅ 검색 결과 페이지 접근 성공!")
            
            # 6단계: 크롤링 테스트
            print("\n6. 크롤링 테스트...")
            try:
                # 상품 요소 확인
                product_selectors = [
                    'a[href*="/catalog/"]',
                    'a[href*="/product/"]',
                    'a[href*="shopping.naver.com"]',
                    '.product_item a',
                    '.item a'
                ]
                
                product_links = []
                for selector in product_selectors:
                    try:
                        links = driver.find_elements(By.CSS_SELECTOR, selector)
                        product_links.extend(links)
                    except:
                        continue
                
                print(f"   상품 링크 수: {len(product_links)}")
                
                # 가격 요소 확인
                price_selectors = [
                    'em',
                    '.price',
                    '[class*="price"]',
                    'strong',
                    'span[class*="price"]'
                ]
                
                price_elements = []
                for selector in price_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        price_elements.extend(elements)
                    except:
                        continue
                
                price_count = 0
                for elem in price_elements:
                    try:
                        text = elem.text.strip()
                        if text and ('원' in text or ',' in text) and any(c.isdigit() for c in text):
                            price_count += 1
                            if price_count <= 5:
                                print(f"   가격 요소 {price_count}: {text}")
                    except:
                        continue
                
                print(f"   총 가격 요소 수: {price_count}")
                
                # 크롤러 테스트
                if product_links and price_count > 0:
                    print("\n   크롤러로 정보 추출 시도...")
                    crawler = NaverShoppingCrawler(driver)
                    result = crawler.get_price_comparison_info_v2()
                    
                    if result:
                        print("📊 크롤링 결과:")
                        print(f"   상품명: {result.get('product_name', 'N/A')}")
                        print(f"   가격: {result.get('price', 'N/A')}")
                        print(f"   리뷰수: {result.get('review_count', 'N/A')}")
                        print(f"   링크: {result.get('naver_link', 'N/A')}")
                        
                        if (result.get('product_name') not in ['상품명 없음', 'N/A'] and 
                            result.get('price') not in ['가격 정보 없음', 'N/A']):
                            print("🎉 크롤링 완전 성공!")
                        else:
                            print("⚠️ 크롤링 부분 성공")
                    else:
                        print("❌ 크롤링 실패")
                else:
                    print("   상품 정보가 충분하지 않음")
                        
            except Exception as e:
                print(f"   크롤링 테스트 중 오류: {e}")
        
        # 최종 확인 시간
        print("\n=== 테스트 완료 ===")
        print("브라우저 상태를 확인하세요.")
        print("30초 후 자동 종료됩니다...")
        time.sleep(30)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("✅ 브라우저 종료 완료")

if __name__ == "__main__":
    test_naver_main_to_shopping() 