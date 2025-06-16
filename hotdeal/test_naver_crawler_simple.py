"""
네이버 쇼핑 크롤러 간단 테스트 스크립트 - 헤드리스 모드
"""
import logging
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from naver_shopping_crawler import NaverShoppingCrawler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def setup_headless_chrome_driver():
    """헤드리스 Chrome 드라이버 설정"""
    chrome_options = Options()
    
    # 헤드리스 모드 활성화
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # 자동화 감지 방지
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 자동화 감지 방지
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Chrome 드라이버 설정 실패: {e}")
        return None

def manual_test():
    """수동으로 URL 접근 테스트"""
    print("=== 수동 URL 접근 테스트 ===")
    
    driver = None
    try:
        driver = setup_headless_chrome_driver()
        if not driver:
            print("❌ 드라이버 설정 실패")
            return
        
        print("✅ 헤드리스 Chrome 드라이버 설정 완료")
        
        # 테스트 URL
        test_url = "https://search.shopping.naver.com/search/all?productSet=model&query=%EC%8B%A0%EB%9D%BC%EB%A9%B4"
        
        print("1. 네이버 메인 페이지부터 접근...")
        driver.get("https://www.naver.com")
        time.sleep(5)
        print(f"네이버 메인 페이지 제목: {driver.title}")
        
        print("2. 네이버 쇼핑으로 이동...")
        driver.get("https://shopping.naver.com")
        time.sleep(5)
        print(f"네이버 쇼핑 페이지 제목: {driver.title}")
        
        print("3. 검색 페이지로 이동...")
        driver.get(test_url)
        time.sleep(10)  # 더 긴 대기시간
        
        print(f"최종 URL: {driver.current_url}")
        print(f"페이지 제목: {driver.title}")
        
        # 페이지 소스 확인
        page_source = driver.page_source
        
        if "접속이 일시적으로 제한" in page_source:
            print("❌ 여전히 접속 제한 감지")
            print("페이지 소스 일부:")
            print(page_source[:1000])
        else:
            print("✅ 접속 제한 없음 - 크롤링 시도")
            
            # 간단한 요소 찾기 테스트
            from selenium.webdriver.common.by import By
            
            try:
                # 상품 링크 찾기
                product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/catalog/"]')
                print(f"발견된 상품 링크 수: {len(product_links)}")
                
                if product_links:
                    print("첫 번째 상품 링크 텍스트:", product_links[0].text[:50])
                
                # 가격 요소 찾기
                price_elements = driver.find_elements(By.CSS_SELECTOR, 'em')
                price_count = 0
                for elem in price_elements:
                    text = elem.text.strip()
                    if text and ('원' in text or ',' in text):
                        price_count += 1
                        if price_count <= 3:  # 처음 3개만 출력
                            print(f"가격 요소 {price_count}: {text}")
                
                print(f"총 가격 관련 요소 수: {price_count}")
                
            except Exception as e:
                print(f"요소 찾기 실패: {e}")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("✅ 브라우저 종료 완료")

if __name__ == "__main__":
    manual_test() 