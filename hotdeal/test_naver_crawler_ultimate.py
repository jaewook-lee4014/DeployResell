"""
네이버 쇼핑 크롤러 최종 우회 테스트 스크립트
"""
import logging
import sys
import time
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from naver_shopping_crawler import NaverShoppingCrawler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def setup_ultimate_chrome_driver():
    """최종 Chrome 드라이버 설정 - 모든 우회 기법 적용"""
    chrome_options = Options()
    
    # 헤드리스 모드 해제 (사용자 요청)
    # chrome_options.add_argument('--headless')
    
    # 실제 사용자 프로필 사용
    user_profile = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data"
    chrome_options.add_argument(f"--user-data-dir={user_profile}")
    chrome_options.add_argument("--profile-directory=Default")
    
    # 기본 Chrome 옵션들
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    
    # 자동화 감지 방지 - 강화된 버전
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    
    # 추가 우회 옵션들
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    chrome_options.add_argument('--disable-background-networking')
    
    # 최신 실제 User-Agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 자동화 관련 설정 완전 제거
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("detach", True)
    
    # 언어 및 지역 설정
    chrome_options.add_argument('--lang=ko-KR')
    chrome_options.add_argument('--accept-lang=ko-KR,ko,en-US,en')
    
    # 보안 관련 설정들
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_argument('--ignore-certificate-errors-cert-list')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 완전한 자동화 감지 방지 스크립트들
        stealth_script = """
        // webdriver 속성 완전 제거
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        
        // plugins 배열 실제화
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: "Chrome PDF Plugin", description: "Portable Document Format", filename: "internal-pdf-viewer"},
                {name: "Chrome PDF Viewer", description: "", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai"},
                {name: "Native Client", description: "", filename: "internal-nacl-plugin"}
            ]
        });
        
        // languages 설정
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ko-KR', 'ko', 'en-US', 'en']
        });
        
        // permissions API 모킹
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({ state: 'granted' })
            })
        });
        
        // chrome 객체 생성
        if (!window.chrome) {
            window.chrome = {};
        }
        if (!window.chrome.runtime) {
            window.chrome.runtime = {
                onConnect: null,
                onMessage: null
            };
        }
        
        // notification API 모킹
        Object.defineProperty(navigator, 'notification', {
            get: () => ({
                permission: 'default'
            })
        });
        
        // 마우스 이벤트 리스너 추가 (자연스러운 동작)
        document.addEventListener('mousemove', function(e) {
            // 아무 동작 안함 - 단순히 이벤트 리스너 존재만으로도 자연스러움
        });
        """
        
        driver.execute_script(stealth_script)
        
        return driver
    except Exception as e:
        print(f"Chrome 드라이버 설정 실패: {e}")
        return None

def save_cookies(driver, filename="naver_cookies.json"):
    """쿠키 저장"""
    try:
        cookies = driver.get_cookies()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"✅ 쿠키 저장 완료: {filename}")
        return True
    except Exception as e:
        print(f"❌ 쿠키 저장 실패: {e}")
        return False

def load_cookies(driver, filename="naver_cookies.json"):
    """쿠키 로드"""
    try:
        if not os.path.exists(filename):
            print(f"❌ 쿠키 파일 없음: {filename}")
            return False
        
        with open(filename, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        for cookie in cookies:
            try:
                # sameSite 속성 처리
                if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                    cookie['sameSite'] = 'Lax'
                
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"개별 쿠키 로드 실패: {e}")
                continue
        
        print(f"✅ 쿠키 로드 완료: {filename}")
        return True
    except Exception as e:
        print(f"❌ 쿠키 로드 실패: {e}")
        return False

def human_like_behavior(driver):
    """인간과 같은 행동 시뮬레이션"""
    # 랜덤 마우스 움직임
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
    
    # 스크롤 시뮬레이션
    scroll_amount = random.randint(100, 500)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    time.sleep(random.uniform(0.5, 1.5))
    
    # 다시 위로 스크롤
    driver.execute_script(f"window.scrollBy(0, -{scroll_amount//2});")
    time.sleep(random.uniform(0.3, 0.8))

def test_ultimate_access():
    """최종 접근 테스트"""
    print("=== 네이버 쇼핑 최종 우회 테스트 ===")
    
    driver = None
    try:
        driver = setup_ultimate_chrome_driver()
        if not driver:
            print("❌ 드라이버 설정 실패")
            return
        
        print("✅ 최종 Chrome 드라이버 설정 완료")
        
        # 1단계: 네이버 메인으로 자연스럽게 접근
        print("1. 네이버 메인 페이지 접근...")
        driver.get("https://www.naver.com")
        time.sleep(random.uniform(3, 5))
        
        # 인간 행동 시뮬레이션
        human_like_behavior(driver)
        
        print(f"네이버 메인 페이지 제목: {driver.title}")
        
        # 2단계: 쿠키 로드 시도
        print("2. 기존 쿠키 로드 시도...")
        load_cookies(driver, "naver_cookies.json")
        
        # 3단계: 네이버 쇼핑으로 이동
        print("3. 네이버 쇼핑 페이지 접근...")
        driver.get("https://shopping.naver.com")
        time.sleep(random.uniform(4, 6))
        
        human_like_behavior(driver)
        print(f"네이버 쇼핑 제목: {driver.title}")
        
        # 쿠키 저장
        save_cookies(driver, "naver_cookies.json")
        
        # 4단계: 검색 시뮬레이션 (더 자연스럽게)
        print("4. 검색창을 통한 자연스러운 검색...")
        
        try:
            # 검색창 찾기
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='검색']"))
            )
            
            # 자연스러운 타이핑
            search_term = "신라면"
            for char in search_term:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            
            # 엔터 키 또는 검색 버튼 클릭
            search_box.send_keys("\n")
            
        except Exception as e:
            print(f"검색창 사용 실패, 직접 링크로 이동: {e}")
            # 직접 링크로 이동
            test_url = "https://search.shopping.naver.com/search/all?productSet=model&query=%EC%8B%A0%EB%9D%BC%EB%A9%B4"
            driver.get(test_url)
        
        time.sleep(random.uniform(5, 8))
        
        print(f"최종 URL: {driver.current_url}")
        print(f"페이지 제목: {driver.title}")
        
        # 5단계: 결과 확인
        page_source = driver.page_source
        
        if "접속이 일시적으로 제한" in page_source:
            print("❌ 여전히 접속 제한 감지")
            print("페이지 소스 일부:")
            print(page_source[:1000])
        else:
            print("🎉 접속 제한 없음! 크롤링 가능!")
            
            # 크롤러 테스트
            print("\n6. 네이버 쇼핑 크롤러로 정보 추출...")
            crawler = NaverShoppingCrawler(driver)
            
            result = crawler.get_price_comparison_info_v2()
            
            if result:
                print("📊 추출된 정보:")
                print(f"  • 상품명: {result.get('product_name', 'N/A')}")
                print(f"  • 가격: {result.get('price', 'N/A')}")
                print(f"  • 리뷰 수: {result.get('review_count', 'N/A')}")
                print(f"  • 링크: {result.get('naver_link', 'N/A')}")
                
                if (result.get('product_name') != '상품명 없음' and 
                    result.get('price') != '가격 정보 없음'):
                    print("🎉🎉 크롤링 완전 성공!")
                else:
                    print("⚠️ 일부 정보 누락")
            else:
                print("❌ 정보 추출 실패")
        
        # 사용자 확인 시간
        print("\n브라우저 상태를 확인하세요.")
        print("성공했다면 지금 상태를 저장해두세요!")
        print("20초 후 자동 종료됩니다...")
        time.sleep(20)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            # 종료 전 쿠키 저장
            try:
                save_cookies(driver, "final_naver_cookies.json")
            except:
                pass
            
            driver.quit()
            print("✅ 브라우저 종료 완료")

if __name__ == "__main__":
    test_ultimate_access() 