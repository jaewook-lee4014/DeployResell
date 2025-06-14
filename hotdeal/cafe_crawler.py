"""
네이버 카페 크롤러
"""
import logging
import time
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd

from config import CAFE_CONFIG, CRAWLING_CONFIG, REGEX_PATTERNS
from utils import (
    extract_price_from_title, clean_product_title, get_current_timestamp,
    create_dataframe_row, safe_sleep, retry_on_failure, extract_urls_from_text
)


class CafeCrawler:
    """네이버 카페 크롤러"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.wait = WebDriverWait(driver, CRAWLING_CONFIG['implicit_wait'])
        
    @retry_on_failure(max_retries=CRAWLING_CONFIG['max_retries'])
    def get_link_from_comments(self) -> str:
        """댓글에서 링크 추출"""
        try:
            self.logger.debug("댓글에서 링크 추출 시작")
            
            # iframe 전환
            try:
                iframe = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "cafe_main"))
                )
                self.driver.switch_to.frame(iframe)
            except TimeoutException:
                self.driver.switch_to.frame("cafe_main")
            
            # 댓글 박스 찾기
            comment_boxes = self.driver.find_elements(By.CLASS_NAME, 'comment_box')
            
            for comment in comment_boxes:
                try:
                    # 작성자 여부 확인
                    try:
                        comment.find_element(By.CLASS_NAME, 'comment_badge_writer')
                        is_writer = True
                    except NoSuchElementException:
                        is_writer = False
                    
                    if is_writer:
                        comment_text_element = comment.find_element(By.CLASS_NAME, 'text_comment')
                        
                        # a 태그에서 링크 추출 시도
                        try:
                            link = comment_text_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                            if link:
                                self.logger.debug(f"댓글에서 링크 발견: {link}")
                                return link
                        except NoSuchElementException:
                            # 텍스트에서 정규식으로 링크 추출
                            urls = extract_urls_from_text(comment_text_element.text)
                            if urls:
                                self.logger.debug(f"정규식으로 링크 발견: {urls[0]}")
                                return urls[0]
                
                except Exception as e:
                    self.logger.warning(f"댓글 처리 중 오류: {e}")
                    continue
            
            return "NO_LINK"
            
        except Exception as e:
            self.logger.error(f"댓글 링크 추출 실패: {e}")
            return "NO_LINK"
    
    @retry_on_failure(max_retries=CRAWLING_CONFIG['max_retries'])
    def extract_article_info(self, article_element) -> Optional[Dict]:
        """게시글 정보 추출"""
        try:
            # 게시글 번호
            matching_number_element = article_element.find(class_='inner_number')
            if not matching_number_element:
                return None
            
            matching_number = int(matching_number_element.get_text().strip())
            
            # 게시글 제목
            article_element_title = article_element.find(class_='article')
            if not article_element_title:
                return None
            
            article_title = article_element_title.get_text().strip()
            product_title = clean_product_title(article_title)
            
            # 가격 추출
            price = extract_price_from_title(product_title)
            
            # 게시글 URL
            article_url = (f'https://cafe.naver.com/ArticleRead.nhn?clubid={CAFE_CONFIG["club_id"]}'
                          f'&page=1&menuid={CAFE_CONFIG["menu_id"]}&boardtype=L'
                          f'&articleid={matching_number}&referrerAllArticles=false')
            
            return {
                'matching_number': matching_number,
                'article_title': article_title,
                'product_title': product_title,
                'price': price,
                'article_url': article_url
            }
            
        except Exception as e:
            self.logger.error(f"게시글 정보 추출 실패: {e}")
            return None
    
    @retry_on_failure(max_retries=CRAWLING_CONFIG['max_retries'])
    def get_shopping_link(self, article_url: str) -> str:
        """게시글에서 쇼핑몰 링크 추출"""
        try:
            self.driver.get(article_url)
            safe_sleep(CRAWLING_CONFIG['sleep_between_requests'])
            
            # iframe 전환
            try:
                iframe = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "cafe_main"))
                )
                self.driver.switch_to.frame(iframe)
            except TimeoutException:
                try:
                    self.driver.switch_to.frame("cafe_main")
                except:
                    pass
            
            # 본문에서 링크 찾기
            try:
                link_element = self.driver.find_element(By.CLASS_NAME, 'se-link')
                link = link_element.text
                if link and link.startswith(('http://', 'https://')):
                    return link
            except NoSuchElementException:
                pass
            
            # 댓글에서 링크 찾기
            link = self.get_link_from_comments()
            return link if link != "NO_LINK" else "링크 없음"
            
        except Exception as e:
            self.logger.error(f"쇼핑몰 링크 추출 실패: {e}")
            return "링크 없음"
    
    def crawl_new_articles(self, last_search_num: int) -> Tuple[List[Dict], int]:
        """새로운 게시글 크롤링"""
        self.logger.info("맘이베베 크롤링 시작")
        
        new_articles = []
        current_max_num = last_search_num
        
        for page in range(CAFE_CONFIG['max_pages']):
            try:
                # 페이지 로드
                page_url = f"{CAFE_CONFIG['base_url']}&search.menuid={CAFE_CONFIG['menu_id']}&search.page={page + 1}"
                self.driver.get(page_url)
                safe_sleep(CRAWLING_CONFIG['sleep_between_requests'])
                
                # iframe 전환
                try:
                    iframe = self.wait.until(
                        EC.presence_of_element_located((By.NAME, "cafe_main"))
                    )
                    self.driver.switch_to.frame(iframe)
                except TimeoutException:
                    self.logger.warning(f"페이지 {page + 1} iframe 로드 실패")
                    continue
                
                # HTML 파싱
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                article_board = soup.find_all(class_='article-board m-tcol-c')
                
                if len(article_board) < 2:
                    self.logger.warning(f"페이지 {page + 1} 게시글 보드 찾기 실패")
                    continue
                
                articles = article_board[1].find_all(class_='td_article')
                
                stop_crawling = False
                
                for index, article in enumerate(articles):
                    article_info = self.extract_article_info(article)
                    if not article_info:
                        continue
                    
                    matching_number = article_info['matching_number']
                    
                    # 첫 번째 페이지의 첫 번째 게시글에서 현재 최신 번호 저장
                    if page == 0 and index == 0:
                        current_max_num = matching_number
                        self.logger.info(f"현재 최신 번호: {current_max_num}")
                    
                    # 이전 크롤링 번호와 비교
                    if matching_number <= last_search_num:
                        self.logger.info(f"이전 크롤링 지점 도달: {matching_number}")
                        stop_crawling = True
                        break
                    
                    # 새 게시글 처리
                    if matching_number < current_max_num or page > 0:
                        self.logger.info(f"새 게시글 처리: {matching_number}")
                        
                        # 쇼핑몰 링크 추출
                        shop_link = self.get_shopping_link(article_info['article_url'])
                        
                        # 데이터 생성
                        timestamp = get_current_timestamp()
                        article_data = create_dataframe_row(
                            timestamp=timestamp,
                            source="맘이베베",
                            article_id=matching_number,
                            article_url=article_info['article_url'],
                            original_title=article_info['article_title'],
                            cleaned_title=article_info['product_title'],
                            shop_url=shop_link,
                            price=article_info['price']
                        )
                        
                        new_articles.append(article_data)
                
                if stop_crawling:
                    break
                    
            except Exception as e:
                self.logger.error(f"페이지 {page + 1} 크롤링 실패: {e}")
                continue
        
        self.logger.info(f"크롤링 완료: {len(new_articles)}개 새 게시글")
        return new_articles, current_max_num 