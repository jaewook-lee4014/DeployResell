"""
네이버 쇼핑 자연스러운 사용자 플로우 테스트
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

def setup_natural_chrome_driver():
    """자연스러운 사용자 행동을 위한 Chrome 드라이버 설정"""
    chrome_options = Options()
    
    # 임시 프로필 디렉토리 생성
    temp_profile = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={temp_profile}")
    
    # 기본 설정들
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1366,768')
    chrome_options.add_argument('--start-maximized')
    
    # 자동화 감지 방지 (최소한으로)
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
        
        # 최소한의 자동화 감지 방지
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        
        return driver
    except Exception as e:
        print(f"Chrome 드라이버 설정 실패: {e}")
        return None

def human_typing(element, text, typing_speed=0.1):
    """사람처럼 타이핑하기"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, typing_speed))

def random_mouse_movement(driver):
    """랜덤 마우스 움직임"""
    driver.execute_script("""
        var event = new MouseEvent('mousemove', {
            'view': window,
            'bubbles': true,
            'cancelable': true,
            'clientX': Math.random() * window.innerWidth,
            'clientY': Math.random() * window.innerHeight
        });
        document.dispatchEvent(event);
    """)

def natural_scroll(driver):
    """자연스러운 스크롤"""
    # 아래로 스크롤
    scroll_amount = random.randint(200, 600)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    time.sleep(random.uniform(1, 2))
    
    # 다시 위로 조금 스크롤
    driver.execute_script(f"window.scrollBy(0, -{scroll_amount//3});")
    time.sleep(random.uniform(0.5, 1))

def wait_with_activity(driver, seconds):
    """대기하면서 자연스러운 활동"""
    end_time = time.time() + seconds
    while time.time() < end_time:
        random_mouse_movement(driver)
        time.sleep(random.uniform(0.5, 1.5))

def test_natural_user_flow():
    """자연스러운 사용자 플로우 테스트"""
    print("=== 자연스러운 사용자 플로우 테스트 ===")
    
    driver = None
    try:
        driver = setup_natural_chrome_driver()
        if not driver:
            print("❌ 드라이버 설정 실패")
            return
        
        print("✅ Chrome 드라이버 설정 완료")
        
        # 1단계: 네이버 메인 페이지 방문
        print("\n1. 네이버 메인 페이지 방문...")
        driver.get("https://www.naver.com")
        wait_with_activity(driver, random.uniform(3, 5))
        print(f"   현재 페이지: {driver.title}")
        
        # 2단계: 쇼핑 메뉴 클릭 (자연스러운 네비게이션)
        print("\n2. 쇼핑 메뉴 찾기...")
        try:
            # 쇼핑 링크 찾기 (여러 셀렉터 시도)
            shopping_selectors = [
                'a[href*="shopping.naver.com"]',
                'a[data-clk*="sho"]',
                'a:contains("쇼핑")',
                '.service_shopping a',
                '.gnb_service a[href*="shopping"]'
            ]
            
            shopping_link = None
            for selector in shopping_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for elem in elements:
                            if '쇼핑' in elem.text or 'shopping' in elem.get_attribute('href'):
                                shopping_link = elem
                                break
                        if shopping_link:
                            break
                except:
                    continue
            
            if shopping_link:
                print("   쇼핑 메뉴 발견, 클릭...")
                random_mouse_movement(driver)
                time.sleep(random.uniform(1, 2))
                shopping_link.click()
                wait_with_activity(driver, random.uniform(3, 5))
            else:
                print("   쇼핑 메뉴 못 찾음, 직접 이동...")
                driver.get("https://shopping.naver.com")
                wait_with_activity(driver, random.uniform(3, 5))
                
        except Exception as e:
            print(f"   쇼핑 메뉴 클릭 실패: {e}")
            print("   직접 쇼핑 페이지로 이동...")
            driver.get("https://shopping.naver.com")
            wait_with_activity(driver, random.uniform(3, 5))
        
        print(f"   현재 페이지: {driver.title}")
        
        # 3단계: 페이지 상태 확인
        current_source = driver.page_source
        if "잠시 후 다시 확인" in current_source or "일시적으로 제한" in current_source:
            print("❌ 네이버 쇼핑 접근 제한 감지")
            print("   브라우저에서 수동으로 확인하세요...")
            time.sleep(30)
            return
        
        # 4단계: 자연스러운 페이지 탐색
        print("\n3. 페이지 자연스럽게 탐색...")
        natural_scroll(driver)
        wait_with_activity(driver, random.uniform(2, 4))
        
        # 5단계: 검색창 찾기 및 검색
        print("\n4. 검색창으로 자연스러운 검색...")
        try:
            # 검색창 찾기 (여러 셀렉터 시도)
            search_selectors = [
                'input[placeholder*="검색"]',
                'input[name="query"]',
                'input[type="search"]',
                '.search_input input',
                '#gnb-gnb_search input',
                '.autocomplete input'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = driver.find_element(By.CSS_SELECTOR, selector)
                    if search_box.is_displayed():
                        break
                except:
                    continue
            
            if search_box:
                print("   검색창 발견!")
                
                # 검색창 클릭 전 자연스러운 동작
                random_mouse_movement(driver)
                time.sleep(random.uniform(0.5, 1))
                
                # 검색창 클릭
                search_box.click()
                time.sleep(random.uniform(0.5, 1))
                
                # 검색어 입력 (자연스럽게 타이핑)
                search_term = "신라면"
                print(f"   '{search_term}' 입력 중...")
                
                # 기존 텍스트 클리어
                search_box.clear()
                time.sleep(random.uniform(0.2, 0.5))
                
                # 자연스러운 타이핑
                human_typing(search_box, search_term, 0.15)
                
                # 잠시 대기 (실제 사용자처럼)
                wait_with_activity(driver, random.uniform(1, 2))
                
                # 엔터 키 입력
                print("   검색 실행...")
                search_box.send_keys(Keys.RETURN)
                
                # 검색 결과 로딩 대기
                wait_with_activity(driver, random.uniform(3, 6))
                
            else:
                print("   검색창을 찾을 수 없음")
                # URL 파라미터로 검색 (최후의 수단)
                search_url = "https://search.shopping.naver.com/search/all?productSet=model&query=%EC%8B%A0%EB%9D%BC%EB%A9%B4"
                print("   직접 검색 URL로 이동...")
                driver.get(search_url)
                wait_with_activity(driver, random.uniform(3, 6))
                
        except Exception as e:
            print(f"   검색 과정 실패: {e}")
            return
        
        # 6단계: 검색 결과 확인
        print(f"\n5. 검색 결과 확인...")
        print(f"   최종 URL: {driver.current_url}")
        print(f"   페이지 제목: {driver.title}")
        
        # 페이지 상태 분석
        page_source = driver.page_source
        
        if "접속이 일시적으로 제한" in page_source or "잠시 후 다시 확인" in page_source:
            print("❌ 검색 페이지에서 접속 제한 감지")
            print("   하지만 여기까지 온 것은 진전!")
        else:
            print("✅ 검색 페이지 접근 성공!")
            
            # 크롤링 테스트
            print("\n6. 크롤링 테스트...")
            try:
                # 간단한 요소 확인
                product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/catalog/"]')
                print(f"   상품 링크 수: {len(product_links)}")
                
                if product_links:
                    print("   크롤러로 정보 추출 시도...")
                    crawler = NaverShoppingCrawler(driver)
                    result = crawler.get_price_comparison_info_v2()
                    
                    if result:
                        print("📊 추출 결과:")
                        print(f"   상품명: {result.get('product_name', 'N/A')}")
                        print(f"   가격: {result.get('price', 'N/A')}")
                        print(f"   리뷰수: {result.get('review_count', 'N/A')}")
                        
                        if (result.get('product_name') not in ['상품명 없음', 'N/A'] and 
                            result.get('price') not in ['가격 정보 없음', 'N/A']):
                            print("🎉 크롤링 완전 성공!")
                        else:
                            print("⚠️ 크롤링 부분 성공")
                    else:
                        print("❌ 크롤링 실패")
                        
            except Exception as e:
                print(f"   크롤링 테스트 중 오류: {e}")
        
        # 최종 확인 시간
        print("\n=== 테스트 완료 ===")
        print("브라우저 상태를 확인하세요.")
        print("15초 후 자동 종료됩니다...")
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
    test_natural_user_flow() 