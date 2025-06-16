"""
네이버 쇼핑 크롤러 최종 테스트 스크립트 - 프로필 문제 해결
"""
import logging
import sys
import time
import random
import tempfile
import os
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

def setup_final_chrome_driver():
    """최종 Chrome 드라이버 설정 - 프로필 문제 해결"""
    chrome_options = Options()
    
    # 헤드리스 모드 해제 (사용자 요청)
    # chrome_options.add_argument('--headless')
    
    # 임시 프로필 디렉토리 생성
    temp_profile = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={temp_profile}")
    
    # 기본 Chrome 옵션들
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1366,768')  # 일반적인 해상도
    chrome_options.add_argument('--start-maximized')
    
    # 자동화 감지 방지 핵심 설정들
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 실제 사용자와 유사한 User-Agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 언어 설정
    chrome_options.add_argument('--lang=ko-KR')
    
    # 추가 자연스러운 설정들
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # 빠른 로딩
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 자동화 감지 방지 핵심 스크립트
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
        """)
        
        print(f"✅ 임시 프로필 생성: {temp_profile}")
        return driver
    except Exception as e:
        print(f"Chrome 드라이버 설정 실패: {e}")
        return None

def natural_delay():
    """자연스러운 지연"""
    time.sleep(random.uniform(2, 4))

def test_final_approach():
    """최종 접근 테스트"""
    print("=== 네이버 쇼핑 최종 테스트 (단계별 접근) ===")
    
    driver = None
    try:
        driver = setup_final_chrome_driver()
        if not driver:
            print("❌ 드라이버 설정 실패")
            return
        
        print("✅ Chrome 드라이버 설정 완료")
        
        # 1단계: 네이버 메인 접근
        print("\n1. 네이버 메인 페이지 접근...")
        driver.get("https://www.naver.com")
        natural_delay()
        print(f"   제목: {driver.title}")
        
        # 2단계: 네이버 쇼핑 메인으로 이동
        print("\n2. 네이버 쇼핑 메인 페이지 이동...")
        driver.get("https://shopping.naver.com")
        natural_delay()
        print(f"   제목: {driver.title}")
        
        # 3단계: 직접 검색 URL로 이동
        print("\n3. 검색 결과 페이지 이동...")
        search_url = "https://search.shopping.naver.com/search/all?productSet=model&query=%EC%8B%A0%EB%9D%BC%EB%A9%B4"
        
        driver.get(search_url)
        natural_delay()
        
        print(f"   최종 URL: {driver.current_url}")
        print(f"   페이지 제목: {driver.title}")
        
        # 4단계: 페이지 상태 분석
        print("\n4. 페이지 상태 분석...")
        page_source = driver.page_source
        
        # 접속 제한 확인
        if "접속이 일시적으로 제한" in page_source:
            print("❌ 접속 제한 감지됨")
            print("   접속 제한 메시지가 있는 페이지입니다.")
            
            # 브라우저에서 직접 확인할 수 있도록 대기
            print("\n브라우저에서 수동으로 확인해보세요...")
            print("30초 후 자동 종료됩니다.")
            time.sleep(30)
            
        elif "상품이 없습니다" in page_source:
            print("⚠️  검색 결과 없음")
            
        else:
            print("✅ 페이지 로딩 성공!")
            
            # 기본 요소들 확인
            print("\n5. 페이지 요소 확인...")
            
            try:
                # 상품 링크 찾기
                product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/catalog/"]')
                print(f"   상품 링크 수: {len(product_links)}")
                
                # 가격 요소 찾기 
                price_elements = driver.find_elements(By.CSS_SELECTOR, 'em')
                price_count = 0
                for elem in price_elements:
                    text = elem.text.strip()
                    if text and ('원' in text or ',' in text) and text.replace(',', '').replace('원', '').isdigit():
                        price_count += 1
                        if price_count <= 3:
                            print(f"   가격 {price_count}: {text}")
                
                print(f"   총 가격 요소 수: {price_count}")
                
                # 크롤러 테스트
                if product_links and price_count > 0:
                    print("\n6. 크롤러 테스트...")
                    crawler = NaverShoppingCrawler(driver)
                    result = crawler.get_price_comparison_info_v2()
                    
                    if result:
                        print("📊 크롤링 결과:")
                        print(f"   상품명: {result.get('product_name', 'N/A')}")
                        print(f"   가격: {result.get('price', 'N/A')}")
                        print(f"   리뷰수: {result.get('review_count', 'N/A')}")
                        
                        # 성공 여부 판단
                        if (result.get('product_name') not in ['상품명 없음', 'N/A'] and 
                            result.get('price') not in ['가격 정보 없음', 'N/A']):
                            print("🎉 크롤링 성공!")
                        else:
                            print("⚠️ 크롤링 부분 성공")
                    else:
                        print("❌ 크롤링 실패")
                
            except Exception as e:
                print(f"❌ 요소 확인 중 오류: {e}")
        
        # 최종 대기
        print("\n=== 테스트 완료 ===")
        print("브라우저에서 최종 상태를 확인하세요.")
        print("10초 후 자동 종료됩니다...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("✅ 브라우저 종료 완료")

if __name__ == "__main__":
    test_final_approach() 