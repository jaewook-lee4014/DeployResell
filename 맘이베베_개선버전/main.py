"""
맘이베베 크롤러 메인 실행 파일
"""
import logging
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import pandas as pd

# 로컬 모듈 import
from config import FILES, CRAWLING_CONFIG, CHROME_OPTIONS
from utils import (
    setup_logging, load_search_info, save_search_info, save_results,
    safe_sleep, get_current_timestamp
)
from cafe_crawler import CafeCrawler
from shopping_mall_crawler import ShoppingMallCrawler
from naver_shopping_crawler import NaverShoppingCrawler


class MomiBebeCrawler:
    """맘이베베 통합 크롤러"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.driver = None
        self.cafe_crawler = None
        self.mall_crawler = None
        self.naver_crawler = None
    
    def setup_driver(self) -> bool:
        """Chrome 드라이버 설정"""
        try:
            chrome_options = Options()
            
            # 옵션 추가
            for option in CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # 알림 설정
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 1
            })
            
            # 드라이버 생성 (macOS의 경우 chromedriver 경로 확인)
            try:
                # Homebrew로 설치된 chromedriver 사용
                service = Service('/opt/homebrew/bin/chromedriver')
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception:
                # 시스템 PATH의 chromedriver 사용
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # 페이지 로드 타임아웃 설정
            self.driver.set_page_load_timeout(CRAWLING_CONFIG['page_load_timeout'])
            self.driver.implicitly_wait(CRAWLING_CONFIG['implicit_wait'])
            
            # 크롤러 인스턴스 생성
            self.cafe_crawler = CafeCrawler(self.driver)
            self.mall_crawler = ShoppingMallCrawler(self.driver)
            self.naver_crawler = NaverShoppingCrawler(self.driver)
            
            self.logger.info("Chrome 드라이버 설정 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"Chrome 드라이버 설정 실패: {e}")
            return False
    
    def cleanup_driver(self):
        """드라이버 정리"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome 드라이버 종료")
            except Exception as e:
                self.logger.error(f"드라이버 종료 실패: {e}")
    
    def run_single_cycle(self) -> bool:
        """단일 크롤링 사이클 실행"""
        try:
            # 1. 검색 정보 로드
            last_search_num = load_search_info(FILES['search_info'])
            if last_search_num is None:
                self.logger.error("검색 정보 로드 실패")
                return False
            
            self.logger.info(f"이전 검색 번호: {last_search_num}")
            
            # 2. 카페 크롤링
            self.logger.info("=== 네이버 카페 크롤링 시작 ===")
            new_articles, current_max_num = self.cafe_crawler.crawl_new_articles(last_search_num)
            
            if not new_articles:
                self.logger.info("새로운 게시글이 없습니다.")
                return True
            
            # 3. 검색 번호 업데이트
            save_search_info(FILES['search_info'], current_max_num)
            
            # 4. DataFrame 생성
            df = pd.DataFrame(new_articles)
            
            # 5. 쇼핑몰 상품명 추출
            self.logger.info("=== 쇼핑몰 상품명 추출 시작 ===")
            shopping_urls = df['쇼핑몰 주소'].tolist()
            fallback_titles = df['보정 제품명'].tolist()
            
            mall_titles = self.mall_crawler.extract_titles_from_urls(shopping_urls, fallback_titles)
            df['쇼핑몰 제목'] = mall_titles
            
            # 6. 네이버쇼핑 최저가 검색
            self.logger.info("=== 네이버쇼핑 최저가 검색 시작 ===")
            naver_results = self.naver_crawler.search_products_batch(mall_titles)
            
            # 네이버쇼핑 결과를 DataFrame에 추가
            df['네이버 주소'] = [result['naver_link'] for result in naver_results]
            df['네이버 번호'] = [result['catalog_id'] for result in naver_results]
            df['네이버 제목'] = [result['product_name'] for result in naver_results]
            df['네이버 가격'] = [result['price'] for result in naver_results]
            df['네이버 배송료'] = [result['delivery_info'] for result in naver_results]
            df['네이버 리뷰 개수'] = [result['review_count'] for result in naver_results]
            
            # 7. 결과 저장
            save_results(FILES['results'], df)
            
            self.logger.info(f"크롤링 사이클 완료: {len(new_articles)}개 새 상품 처리")
            return True
            
        except Exception as e:
            self.logger.error(f"크롤링 사이클 실패: {e}")
            return False
    
    def run_continuous(self):
        """지속적 크롤링 실행"""
        self.logger.info("맘이베베 지속적 크롤링 시작")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                self.logger.info(f"=== 크롤링 사이클 #{cycle_count} 시작 ===")
                
                # 드라이버 설정
                if not self.setup_driver():
                    self.logger.error("드라이버 설정 실패, 재시도")
                    safe_sleep(60)
                    continue
                
                # 크롤링 실행
                success = self.run_single_cycle()
                
                # 드라이버 정리
                self.cleanup_driver()
                
                if success:
                    self.logger.info(f"사이클 #{cycle_count} 성공 완료")
                else:
                    self.logger.error(f"사이클 #{cycle_count} 실패")
                
                # 다음 사이클까지 대기
                self.logger.info(f"{CRAWLING_CONFIG['sleep_after_cycle']}초 대기 중...")
                safe_sleep(CRAWLING_CONFIG['sleep_after_cycle'])
                
            except KeyboardInterrupt:
                self.logger.info("사용자에 의해 중단됨")
                break
            except Exception as e:
                self.logger.error(f"예상치 못한 오류: {e}")
                self.cleanup_driver()
                safe_sleep(60)  # 1분 대기 후 재시도
    
    def run_once(self):
        """단일 실행"""
        self.logger.info("맘이베베 단일 크롤링 시작")
        
        try:
            if not self.setup_driver():
                self.logger.error("드라이버 설정 실패")
                return False
            
            success = self.run_single_cycle()
            self.cleanup_driver()
            
            if success:
                self.logger.info("단일 크롤링 성공 완료")
            else:
                self.logger.error("단일 크롤링 실패")
            
            return success
            
        except Exception as e:
            self.logger.error(f"단일 크롤링 중 오류: {e}")
            self.cleanup_driver()
            return False


def main():
    """메인 함수"""
    crawler = MomiBebeCrawler()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # 단일 실행 모드
        success = crawler.run_once()
        sys.exit(0 if success else 1)
    else:
        # 지속적 실행 모드
        crawler.run_continuous()


if __name__ == "__main__":
    main() 