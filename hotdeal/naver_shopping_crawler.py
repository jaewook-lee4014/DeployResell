"""
네이버쇼핑 크롤러 - 개선된 버전
"""
import logging
import time
import random
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from urllib3.exceptions import MaxRetryError, NewConnectionError
import urllib.parse

from config import NAVER_SHOPPING_CONFIG, CRAWLING_CONFIG
from utils import safe_sleep, retry_on_failure


class NaverShoppingCrawler:
    """네이버쇼핑 크롤러 - 개선된 버전"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.wait = WebDriverWait(driver, CRAWLING_CONFIG['implicit_wait'])
        
        # 더 자연스러운 브라우저 동작을 위한 설정 (안전한 방식)
        try:
            self.driver.execute_script("""
                if (navigator.webdriver) {
                    delete navigator.webdriver;
                }
            """)
        except:
            pass  # 이미 정의되어 있거나 삭제할 수 없는 경우 무시
    
    def _random_delay(self, min_seconds=2, max_seconds=5):
        """랜덤 지연"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _simulate_human_behavior(self):
        """인간의 행동 모방"""
        # 랜덤 마우스 움직임 시뮬레이션
        self.driver.execute_script("""
            var event = new MouseEvent('mousemove', {
                'view': window,
                'bubbles': true,
                'cancelable': true,
                'clientX': Math.random() * window.innerWidth,
                'clientY': Math.random() * window.innerHeight
            });
            document.dispatchEvent(event);
        """)
        self._random_delay(0.5, 1.5)
    
    @retry_on_failure(max_retries=CRAWLING_CONFIG['max_retries'])
    def search_product_direct_url(self, product_name: str) -> bool:
        """가격비교 페이지로 직접 이동하여 상품 검색"""
        try:
            self.logger.info(f"네이버쇼핑 가격비교 페이지 검색: {product_name}")
            
            # URL 인코딩
            encoded_query = urllib.parse.quote(product_name)
            # 가격비교 페이지로 바로 이동
            search_url = f"https://search.shopping.naver.com/search/all?productSet=model&query={encoded_query}"
            
            # 드라이버 상태 확인
            try:
                self.driver.current_url
            except WebDriverException:
                self.logger.error("Chrome 드라이버 연결이 끊어졌습니다.")
                return False
            
            # 자연스러운 페이지 이동
            self._simulate_human_behavior()
            
            try:
                self.driver.get(search_url)
                self._random_delay(3, 6)  # 페이지 로딩 대기
            except WebDriverException as e:
                self.logger.error(f"페이지 로드 실패: {e}")
                return False
            
            # 페이지 로드 확인
            if "접속이 일시적으로 제한" in self.driver.page_source:
                self.logger.error("네이버 쇼핑 접속 제한 감지")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"상품 검색 실패 ({product_name}): {str(e)}")
            return False
    
    @retry_on_failure(max_retries=CRAWLING_CONFIG['max_retries'])
    def get_price_comparison_info_v2(self) -> Optional[Dict]:
        """가격비교 페이지에서 xpath를 사용한 정보 추출"""
        try:
            self._simulate_human_behavior()
            
            # 접속 제한 확인
            if "접속이 일시적으로 제한" in self.driver.page_source:
                self.logger.error("네이버 쇼핑 접속 제한 감지")
                return self._create_no_data_result("접속 제한")
            
            # 현재 URL 저장
            current_url = self.driver.current_url
            
            # 제품명 추출 (xpath 사용)
            product_name = self._extract_product_name_xpath()
            
            # 가격 정보 추출 (xpath 사용)
            price = self._extract_price_xpath()
            
            # 리뷰 수 추출 (xpath 사용)
            review_count = self._extract_review_count_xpath()
            
            # 배송 정보는 기본값으로 설정 (가격비교 페이지에서는 일반적으로 표시되지 않음)
            delivery_info = "배송비 별도 확인 필요"
            
            return {
                'naver_link': current_url,
                'catalog_id': self._extract_catalog_id_from_url(current_url),
                'product_name': product_name,
                'price': price,
                'delivery_info': delivery_info,
                'review_count': review_count
            }
                
        except Exception as e:
            self.logger.error(f"가격비교 정보 추출 실패: {str(e)}")
            return self._create_no_data_result("에러 발생")
    
    def _extract_product_name_xpath(self) -> str:
        """xpath를 사용한 상품명 추출"""
        # 기본 xpath 패턴들
        xpath_patterns = [
            '//*[@id="content"]/div[1]/div[3]/div/div[1]/div[1]/div[2]/div[1]/a',
            '//*[@id="content"]/div[1]/div[3]/div/div[*]/div[1]/div[2]/div[1]/a',  # div 인덱스 변동 대응
            '//*[@id="content"]/div[1]/div[3]/div/div[1]/div[*]/div[2]/div[1]/a',  # div 인덱스 변동 대응
            '//div[contains(@class, "product")]//a[contains(@class, "title") or contains(@href, "/catalog/")]',
            '//a[contains(@href, "/catalog/")]'
        ]
        
        for xpath in xpath_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 1:  # 의미있는 텍스트인지 확인
                            self.logger.info(f"상품명 추출 성공: {xpath}")
                            return text
            except Exception as e:
                self.logger.debug(f"xpath 시도 실패 ({xpath}): {e}")
                continue
        
        # 백업 셀렉터들
        backup_selectors = [
            'a[href*="/catalog/"]',
            '.product_title',
            'h1', 'h2', 'h3'
        ]
        
        for selector in backup_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 1:
                            self.logger.info(f"상품명 추출 성공(백업): {selector}")
                            return text
            except Exception:
                continue
        
        return "상품명 없음"
    
    def _extract_price_xpath(self) -> str:
        """xpath를 사용한 가격 추출"""
        # 기본 xpath 패턴들
        xpath_patterns = [
            '//*[@id="content"]/div[1]/div[3]/div/div[1]/div[1]/div[2]/div[2]/strong/span/span[1]/span[2]/em',
            '//*[@id="content"]/div[1]/div[3]/div/div[*]/div[1]/div[2]/div[2]/strong/span/span[1]/span[2]/em',  # div 인덱스 변동 대응
            '//*[@id="content"]/div[1]/div[3]/div/div[1]/div[*]/div[2]/div[2]/strong/span/span[1]/span[2]/em',  # div 인덱스 변동 대응
            '//strong//em[contains(text(), "원") or contains(text(), ",")]',
            '//span[@class="price"]//em',
            '//em[contains(@class, "price")]',
            '//div[contains(@class, "price")]//em'
        ]
        
        for xpath in xpath_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    for element in elements:
                        text = element.text.strip()
                        if text and ('원' in text or ',' in text or text.replace(',', '').replace('원', '').isdigit()):
                            # 가격 정리 (쉼표 제거, 원 제거)
                            clean_price = text.replace(',', '').replace('원', '').strip()
                            if clean_price.isdigit():
                                self.logger.info(f"가격 추출 성공: {xpath}")
                                return clean_price
            except Exception as e:
                self.logger.debug(f"xpath 시도 실패 ({xpath}): {e}")
                continue
        
        # 백업 셀렉터들
        backup_selectors = [
            'em[class*="price"]',
            'span[class*="price"]',
            '.price em',
            'strong em'
        ]
        
        for selector in backup_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for element in elements:
                        text = element.text.strip()
                        if text and ('원' in text or ',' in text or text.replace(',', '').replace('원', '').isdigit()):
                            clean_price = text.replace(',', '').replace('원', '').strip()
                            if clean_price.isdigit():
                                self.logger.info(f"가격 추출 성공(백업): {selector}")
                                return clean_price
            except Exception:
                continue
        
        return "가격 정보 없음"
    
    def _extract_review_count_xpath(self) -> str:
        """xpath를 사용한 리뷰 수 추출"""
        # 기본 xpath 패턴들
        xpath_patterns = [
            '//*[@id="content"]/div[1]/div[3]/div/div[1]/div[1]/div[2]/div[5]/a/em',
            '//*[@id="content"]/div[1]/div[3]/div/div[*]/div[1]/div[2]/div[5]/a/em',  # div 인덱스 변동 대응
            '//*[@id="content"]/div[1]/div[3]/div/div[1]/div[*]/div[2]/div[5]/a/em',  # div 인덱스 변동 대응
            '//*[@id="content"]/div[1]/div[3]/div/div[1]/div[1]/div[2]/div[*]/a/em',  # div 인덱스 변동 대응 (div[5] 부분)
            '//a[contains(@href, "review")]//em',
            '//em[contains(text(), "리뷰") or contains(text(), "후기")]',
            '//span[contains(text(), "리뷰") or contains(text(), "후기")]'
        ]
        
        for xpath in xpath_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    for element in elements:
                        text = element.text.strip()
                        if text and (text.isdigit() or '리뷰' in text or '후기' in text):
                            self.logger.info(f"리뷰 수 추출 성공: {xpath}")
                            return text
            except Exception as e:
                self.logger.debug(f"xpath 시도 실패 ({xpath}): {e}")
                continue
        
        # 백업 셀렉터들
        backup_selectors = [
            'a[href*="review"] em',
            'em[class*="review"]',
            'span[class*="review"]',
            '.review_count'
        ]
        
        for selector in backup_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for element in elements:
                        text = element.text.strip()
                        if text and (text.isdigit() or '리뷰' in text or '후기' in text):
                            self.logger.info(f"리뷰 수 추출 성공(백업): {selector}")
                            return text
            except Exception:
                continue
        
        return "리뷰 없음"
    
    def _extract_catalog_id_from_url(self, url: str) -> str:
        """URL에서 카탈로그 ID 추출"""
        try:
            if '/catalog/' in url:
                parts = url.split('/catalog/')
                if len(parts) > 1:
                    catalog_id = parts[1].split('?')[0].split('/')[0]
                    return catalog_id
        except:
            pass
        return "카탈로그 ID 없음"
    
    def search_products_batch(self, product_names: List[str]) -> List[Dict]:
        """여러 상품 일괄 검색 - 임시 비활성화"""
        self.logger.info(f"네이버쇼핑 크롤링 임시 비활성화: {len(product_names)}개")
        
        results = []
        
        for i, product_name in enumerate(product_names):
            self.logger.info(f"진행률: {i+1}/{len(product_names)} - {product_name}")
            
            # 임시로 수동 검색 링크 제공
            search_query = urllib.parse.quote(product_name)
            manual_search_url = f"https://search.shopping.naver.com/search/all?query={search_query}"
            
            result = {
                'naver_link': manual_search_url,
                'catalog_id': '수동 검색 필요',
                'product_name': product_name,
                'price': '수동 확인 필요',
                'delivery_info': '수동 확인 필요',
                'review_count': '수동 확인 필요'
            }
            results.append(result)
        
        self.logger.info("네이버쇼핑 수동 검색 링크 생성 완료")
        return results
    
    def _extract_catalog_id(self, data_nclick: str) -> Optional[str]:
        """data-nclick 속성에서 카탈로그 ID 추출"""
        try:
            entries = data_nclick.split(",")
            for entry in entries:
                if entry.strip().startswith("i:"):
                    return entry.strip().replace("i:", "")
            return None
        except Exception:
            return None
    
    def _create_no_data_result(self, reason: str) -> Dict:
        """데이터 없음 결과 생성"""
        return {
            'naver_link': reason,
            'catalog_id': reason,
            'product_name': reason,
            'price': reason,
            'delivery_info': reason,
            'review_count': reason
        } 