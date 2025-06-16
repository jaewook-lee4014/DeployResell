"""
네이버 쇼핑 직접 접근 및 검색창 사용 테스트
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

def human_typing(element, text, typing_speed=0.1):
    """사람처럼 타이핑하기"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, typing_speed))

def random_delay(min_sec=1, max_sec=3):
    """랜덤 지연"""
    time.sleep(random.uniform(min_sec, max_sec))

def test_shopping_search():
    """네이버 쇼핑 직접 검색 테스트"""
    print("=== 네이버 쇼핑 직접 검색 테스트 ===")
    
    driver = None
    try:
        driver = setup_chrome_driver()
        if not driver:
            print("❌ 드라이버 설정 실패")
            return
        
        print("✅ Chrome 드라이버 설정 완료")
        
        # 1단계: 네이버 쇼핑 홈페이지로 직접 이동
        print("\n1. 네이버 쇼핑 홈페이지 접근...")
        shopping_home_url = "https://search.shopping.naver.com/home"
        
        driver.get(shopping_home_url)
        random_delay(3, 5)
        
        print(f"   현재 URL: {driver.current_url}")
        print(f"   페이지 제목: {driver.title}")
        
        # 2단계: 페이지 상태 확인
        print("\n2. 페이지 상태 확인...")
        page_source = driver.page_source
        
        if "잠시 후 다시 확인" in page_source or "일시적으로 제한" in page_source:
            print("❌ 네이버 쇼핑 접근 제한 감지")
            print("   브라우저에서 수동으로 확인하세요...")
            time.sleep(30)
            return
        else:
            print("✅ 네이버 쇼핑 홈페이지 접근 성공!")
        
        # 3단계: 검색창 찾기 (제공된 xpath 사용)
        print("\n3. 검색창 찾기...")
        search_xpath = '//*[@id="input_text"]'
        
        try:
            # xpath로 검색창 찾기
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, search_xpath))
            )
            print("✅ 검색창 발견! (xpath 사용)")
            
            # 검색창이 화면에 보이는지 확인
            if not search_box.is_displayed():
                print("⚠️ 검색창이 화면에 보이지 않음, 스크롤 시도...")
                driver.execute_script("arguments[0].scrollIntoView();", search_box)
                random_delay(1, 2)
            
        except TimeoutException:
            print("❌ 제공된 xpath로 검색창을 찾을 수 없음")
            
            # 백업 셀렉터들 시도
            backup_selectors = [
                'input[id="input_text"]',
                'input[placeholder*="검색"]',
                'input[name="query"]',
                'input[type="search"]',
                '.search_input input',
                'input.search'
            ]
            
            search_box = None
            for selector in backup_selectors:
                try:
                    search_box = driver.find_element(By.CSS_SELECTOR, selector)
                    if search_box.is_displayed():
                        print(f"✅ 백업 셀렉터로 검색창 발견: {selector}")
                        break
                except:
                    continue
            
            if not search_box:
                print("❌ 모든 방법으로 검색창을 찾을 수 없음")
                print("   페이지 소스 확인...")
                print("   input 태그들:")
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for i, inp in enumerate(inputs[:5]):  # 처음 5개만
                    try:
                        print(f"     {i+1}: id={inp.get_attribute('id')}, class={inp.get_attribute('class')}, placeholder={inp.get_attribute('placeholder')}")
                    except:
                        pass
                return
        
        # 4단계: 검색어 입력
        print("\n4. 검색어 입력...")
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
            
        except Exception as e:
            print(f"❌ 검색어 입력 실패: {e}")
            return
        
        # 5단계: 검색 실행
        print("\n5. 검색 실행...")
        try:
            # 엔터 키 입력
            search_box.send_keys(Keys.RETURN)
            print("   엔터 키 입력 완료")
            
            # 검색 결과 로딩 대기
            random_delay(3, 6)
            
        except Exception as e:
            print(f"❌ 검색 실행 실패: {e}")
            return
        
        # 6단계: 검색 결과 확인
        print("\n6. 검색 결과 확인...")
        print(f"   최종 URL: {driver.current_url}")
        print(f"   페이지 제목: {driver.title}")
        
        # 페이지 상태 분석
        page_source = driver.page_source
        
        if "접속이 일시적으로 제한" in page_source or "잠시 후 다시 확인" in page_source:
            print("❌ 검색 결과 페이지에서 접속 제한 감지")
            print("   그래도 검색까지는 성공!")
        else:
            print("✅ 검색 결과 페이지 접근 성공!")
            
            # 7단계: 크롤링 테스트
            print("\n7. 크롤링 테스트...")
            try:
                # 상품 링크 확인
                product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/catalog/"]')
                print(f"   상품 링크 수: {len(product_links)}")
                
                # 가격 요소 확인
                price_elements = driver.find_elements(By.CSS_SELECTOR, 'em')
                price_count = 0
                for elem in price_elements:
                    text = elem.text.strip()
                    if text and ('원' in text or ',' in text) and text.replace(',', '').replace('원', '').isdigit():
                        price_count += 1
                        if price_count <= 3:
                            print(f"   가격 요소 {price_count}: {text}")
                
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
        print("20초 후 자동 종료됩니다...")
        time.sleep(20)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("✅ 브라우저 종료 완료")

if __name__ == "__main__":
    test_shopping_search() 