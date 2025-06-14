"""
네이버쇼핑 크롤러
"""
import logging
import time
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import NAVER_SHOPPING_CONFIG, CRAWLING_CONFIG
from utils import safe_sleep, retry_on_failure


class NaverShoppingCrawler:
    """네이버쇼핑 크롤러"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.wait = WebDriverWait(driver, CRAWLING_CONFIG['implicit_wait'])
    
    @retry_on_failure(max_retries=CRAWLING_CONFIG['max_retries'])
    def search_product(self, product_name: str) -> bool:
        """네이버쇼핑에서 상품 검색"""
        try:
            self.logger.info(f"네이버쇼핑 검색: {product_name}")
            self.driver.get(NAVER_SHOPPING_CONFIG['base_url'])
            safe_sleep(CRAWLING_CONFIG['sleep_between_requests'])
            
            # 검색창 찾기 및 입력
            search_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, NAVER_SHOPPING_CONFIG['search_input_xpath']))
            )
            search_input.clear()
            search_input.send_keys(product_name)
            
            # 검색 버튼 클릭
            search_button = self.driver.find_element(By.XPATH, NAVER_SHOPPING_CONFIG['search_button_xpath'])
            search_button.click()
            
            safe_sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"상품 검색 실패 ({product_name}): {e}")
            return False
    
    @retry_on_failure(max_retries=CRAWLING_CONFIG['max_retries'])
    def get_price_comparison_info(self) -> Optional[Dict]:
        """가격비교 정보 추출"""
        try:
            # 가격비교 탭 클릭
            try:
                price_compare_tab = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, NAVER_SHOPPING_CONFIG['price_compare_xpath']))
                )
                price_compare_tab.click()
                safe_sleep(1)
            except TimeoutException:
                self.logger.warning("가격비교 탭 없음")
                return self._create_no_data_result("네이버 가격비교 없음")
            
            # 첫 번째 상품 정보 추출
            try:
                # 상품명
                product_name_element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/div/div/div[2]/div[2]/div[1]/h2'))
                )
                product_name = product_name_element.text.strip()
                
                # 리뷰 수
                try:
                    review_element = self.driver.find_element(
                        By.XPATH, '/html/body/div/div/div[2]/div/div[3]/div[1]/ul/div/div[1]/li/div/div[2]/div[5]/a/em'
                    )
                    review_count = review_element.text.strip()
                except NoSuchElementException:
                    review_count = "리뷰 없음"
                
                # 첫 번째 상품 링크 정보 추출
                first_item = self.driver.find_element(
                    By.XPATH, '//*[@id="__next"]/div/div[2]/div/div[3]/div[1]/ul/div/div[1]/li/div/div[2]/div[1]/a'
                )
                
                # data-nclick 속성에서 카탈로그 ID 추출
                data_nclick = first_item.get_attribute("data-nclick")
                if not data_nclick:
                    return self._create_no_data_result("네이버 가격비교 없음")
                
                # 카탈로그 ID 파싱
                catalog_id = self._extract_catalog_id(data_nclick)
                if not catalog_id:
                    return self._create_no_data_result("네이버 가격비교 없음")
                
                # 상세 페이지로 이동
                catalog_url = f'https://search.shopping.naver.com/catalog/{catalog_id}'
                self.driver.get(catalog_url)
                safe_sleep(1)
                
                # 배송료 포함 버튼 클릭
                try:
                    delivery_button = self.wait.until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            '//*[@id="__next"]/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/span[1]/a'
                        ))
                    )
                    delivery_button.click()
                    safe_sleep(1)
                except TimeoutException:
                    self.logger.warning("배송료 포함 버튼 클릭 실패")
                
                # 최저가 정보 추출
                price_element = self.wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '//*[@id="__next"]/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[2]/table/tbody/tr[1]/td[2]/a/em'
                    ))
                )
                price = price_element.text.replace(",", "").strip()
                
                # 배송비 정보
                try:
                    delivery_element = self.driver.find_element(
                        By.XPATH,
                        '/html/body/div/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[2]/table/tbody/tr[1]/td[3]'
                    )
                    delivery_info = delivery_element.text.strip()
                except NoSuchElementException:
                    delivery_info = "배송비 정보 없음"
                
                return {
                    'naver_link': catalog_url,
                    'catalog_id': catalog_id,
                    'product_name': product_name,
                    'price': price,
                    'delivery_info': delivery_info,
                    'review_count': review_count
                }
                
            except TimeoutException:
                return self._create_no_data_result("네이버 가격비교 없음")
                
        except Exception as e:
            self.logger.error(f"가격비교 정보 추출 실패: {e}")
            return self._create_no_data_result("에러 발생")
    
    def search_products_batch(self, product_names: List[str]) -> List[Dict]:
        """여러 상품 일괄 검색"""
        self.logger.info(f"네이버쇼핑 일괄 검색 시작: {len(product_names)}개")
        
        results = []
        
        for i, product_name in enumerate(product_names):
            if not product_name or product_name.strip() == "":
                results.append(self._create_no_data_result("상품명 없음"))
                continue
            
            self.logger.info(f"진행률: {i+1}/{len(product_names)} - {product_name}")
            
            # 특수 케이스 처리
            if product_name in ["설정된 사이트, 설정안된 태그", "모르는 사이트", "링크 접속불가"]:
                results.append(self._create_no_data_result("상품명 부적절"))
                continue
            
            # 상품 검색
            if self.search_product(product_name):
                # 가격비교 정보 추출
                result = self.get_price_comparison_info()
                results.append(result or self._create_no_data_result("정보 추출 실패"))
            else:
                results.append(self._create_no_data_result("검색 실패"))
            
            # 요청 간 지연
            if i < len(product_names) - 1:
                safe_sleep(CRAWLING_CONFIG['sleep_between_requests'])
        
        self.logger.info("네이버쇼핑 일괄 검색 완료")
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