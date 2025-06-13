"""
쇼핑몰 크롤러
"""
import logging
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import SHOPPING_MALL_SELECTORS, CRAWLING_CONFIG
from utils import safe_sleep, retry_on_failure, validate_url, detect_shopping_mall


class ShoppingMallCrawler:
    """쇼핑몰 크롤러"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.wait = WebDriverWait(driver, CRAWLING_CONFIG['implicit_wait'])
    
    @retry_on_failure(max_retries=CRAWLING_CONFIG['max_retries'])
    def extract_product_title(self, url: str) -> str:
        """쇼핑몰에서 상품명 추출"""
        if not validate_url(url):
            return "링크 접속불가"
        
        try:
            self.logger.info(f"쇼핑몰 접속: {url}")
            self.driver.get(url)
            safe_sleep(10)  # 페이지 로딩 대기
            
            # 쇼핑몰 종류 감지
            mall_type = detect_shopping_mall(url)
            if not mall_type:
                return "모르는 사이트"
            
            # 해당 쇼핑몰의 XPath들로 상품명 추출 시도
            selectors = SHOPPING_MALL_SELECTORS.get(mall_type, [])
            
            for xpath in selectors:
                try:
                    element = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    title = element.text.strip()
                    if title:
                        self.logger.info(f"상품명 추출 성공: {title}")
                        return title
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # 모든 XPath 실패시
            return "설정된 사이트, 설정안된 태그"
            
        except Exception as e:
            self.logger.error(f"상품명 추출 실패 ({url}): {e}")
            return "링크 접속불가"
    
    def extract_titles_from_urls(self, urls: List[str], fallback_titles: List[str]) -> List[str]:
        """URL 리스트에서 상품명들 추출"""
        self.logger.info(f"쇼핑몰 상품명 추출 시작: {len(urls)}개")
        
        if not urls:
            return []
        
        extracted_titles = []
        
        for i, (url, fallback_title) in enumerate(zip(urls, fallback_titles)):
            self.logger.info(f"진행률: {i+1}/{len(urls)}")
            
            title = self.extract_product_title(url)
            
            # 실패한 경우 대체 제목 사용
            if title in ["설정된 사이트, 설정안된 태그", "모르는 사이트", "링크 접속불가"]:
                title = fallback_title
                self.logger.info(f"대체 제목 사용: {title}")
            
            extracted_titles.append(title)
            
            # 요청 간 지연
            if i < len(urls) - 1:
                safe_sleep(CRAWLING_CONFIG['sleep_between_requests'])
        
        self.logger.info("쇼핑몰 상품명 추출 완료")
        return extracted_titles
    
    def get_mall_info(self, url: str) -> Dict[str, str]:
        """쇼핑몰 정보 반환"""
        mall_type = detect_shopping_mall(url)
        return {
            'mall_type': mall_type or 'unknown',
            'mall_name': self._get_mall_display_name(mall_type),
            'selectors_count': len(SHOPPING_MALL_SELECTORS.get(mall_type, []))
        }
    
    def _get_mall_display_name(self, mall_type: Optional[str]) -> str:
        """쇼핑몰 표시명 반환"""
        mall_names = {
            'auction': '옥션',
            'lotteon': '롯데온',
            'wemakeprice': '위메프',
            'gmarket': 'G마켓',
            'gs': 'GS샵',
            'tmon': '티몬',
            '11st': '11번가',
            'interpark': '인터파크',
            'coupang': '쿠팡',
            'naver': '네이버쇼핑',
            'brand.naver': '네이버브랜드스토어',
            'kakao': '카카오톡스토어',
            'yes24': 'YES24',
            'nsmall': 'NS홈쇼핑',
            'ssg': 'SSG'
        }
        return mall_names.get(mall_type, '알 수 없음') 