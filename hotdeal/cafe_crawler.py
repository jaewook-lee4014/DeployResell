"""
네이버 카페 크롤러 - Playwright 기반
"""
import logging
import time
import asyncio
from typing import List, Dict, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup
import pandas as pd

from config import CAFE_CONFIG, CRAWLING_CONFIG, REGEX_PATTERNS
from utils import (
    extract_price_from_title, clean_product_title, get_current_timestamp,
    create_dataframe_row, safe_sleep, retry_on_failure, extract_urls_from_text
)


class CafeCrawler:
    """네이버 카페 크롤러 - Playwright 기반"""
    
    def __init__(self, driver=None):
        # 기존 Selenium driver는 무시하고 Playwright 사용
        self.logger = logging.getLogger(__name__)
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        
    async def setup_browser(self, headless=True):
        """Playwright 브라우저 설정"""
        try:
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security'
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await self.context.new_page()
            
            # webdriver 탐지 방지
            await self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("카페 크롤러 Playwright 브라우저 설정 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"카페 크롤러 브라우저 설정 실패: {e}")
            return False
    
    async def close_browser(self):
        """브라우저 종료"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("카페 크롤러 브라우저 종료 완료")
        except Exception as e:
            self.logger.error(f"카페 크롤러 브라우저 종료 실패: {e}")
    
    async def get_link_from_comments_async(self) -> str:
        """댓글에서 링크 추출 - 비동기"""
        try:
            self.logger.debug("댓글에서 링크 추출 시작")
            
            # iframe 전환
            try:
                iframe = await self.page.query_selector('iframe[name="cafe_main"]')
                if iframe:
                    frame = await iframe.content_frame()
                    if frame:
                        self.page = frame
            except Exception as e:
                self.logger.warning(f"iframe 전환 실패: {e}")
            
            # 댓글 박스 찾기
            comment_boxes = await self.page.query_selector_all('.comment_box')
            
            for comment in comment_boxes:
                try:
                    # 작성자 여부 확인
                    writer_badge = await comment.query_selector('.comment_badge_writer')
                    is_writer = writer_badge is not None
                    
                    if is_writer:
                        comment_text_element = await comment.query_selector('.text_comment')
                        if comment_text_element:
                            
                            # a 태그에서 링크 추출 시도
                            link_element = await comment_text_element.query_selector('a')
                            if link_element:
                                link = await link_element.get_attribute('href')
                                if link:
                                    self.logger.debug(f"댓글에서 링크 발견: {link}")
                                    return link
                            
                            # 텍스트에서 정규식으로 링크 추출
                            text = await comment_text_element.inner_text()
                            urls = extract_urls_from_text(text)
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
    
    def get_link_from_comments(self) -> str:
        """댓글에서 링크 추출 - 동기 인터페이스"""
        return asyncio.run(self.get_link_from_comments_async())
    
    def extract_article_info(self, article_element) -> Optional[Dict]:
        """게시글 정보 추출 (BeautifulSoup 사용)"""
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
    
    async def get_shopping_link_async(self, article_url: str) -> str:
        """게시글에서 쇼핑몰 링크 추출 - 비동기"""
        try:
            await self.page.goto(article_url)
            await asyncio.sleep(CRAWLING_CONFIG.get('sleep_between_requests', 3))
            
            # iframe 전환
            try:
                iframe = await self.page.query_selector('iframe[name="cafe_main"]')
                if iframe:
                    frame = await iframe.content_frame()
                    if frame:
                        self.page = frame
            except Exception as e:
                self.logger.warning(f"iframe 전환 실패: {e}")
            
            # 본문에서 링크 찾기
            try:
                link_element = await self.page.query_selector('.se-link')
                if link_element:
                    link = await link_element.inner_text()
                    if link and link.startswith(('http://', 'https://')):
                        return link
            except Exception:
                pass
            
            # 댓글에서 링크 찾기
            link = await self.get_link_from_comments_async()
            return link if link != "NO_LINK" else "링크 없음"
            
        except Exception as e:
            self.logger.error(f"쇼핑몰 링크 추출 실패: {e}")
            return "링크 없음"
    
    def get_shopping_link(self, article_url: str) -> str:
        """게시글에서 쇼핑몰 링크 추출 - 동기 인터페이스"""
        return asyncio.run(self._get_shopping_link_with_browser(article_url))
    
    async def _get_shopping_link_with_browser(self, article_url: str) -> str:
        """브라우저 설정과 함께 쇼핑몰 링크 추출"""
        try:
            if not await self.setup_browser():
                return "브라우저 설정 실패"
            
            result = await self.get_shopping_link_async(article_url)
            return result
            
        finally:
            await self.close_browser()
    
    def crawl_new_articles(self, last_search_num: int) -> Tuple[List[Dict], int]:
        """새로운 게시글 크롤링 - 동기 인터페이스"""
        return asyncio.run(self._crawl_new_articles_async(last_search_num))
    
    async def _crawl_new_articles_async(self, last_search_num: int) -> Tuple[List[Dict], int]:
        """새로운 게시글 크롤링 - 비동기 구현"""
        self.logger.info("맘이베베 크롤링 시작")
        
        new_articles = []
        current_max_num = last_search_num
        
        try:
            # 브라우저 설정
            if not await self.setup_browser():
                self.logger.error("브라우저 설정 실패")
                return [], last_search_num
        
            for page in range(CAFE_CONFIG['max_pages']):
                try:
                    # 페이지 로드
                    page_url = f"{CAFE_CONFIG['base_url']}&search.menuid={CAFE_CONFIG['menu_id']}&search.page={page + 1}"
                    await self.page.goto(page_url)
                    await asyncio.sleep(CRAWLING_CONFIG.get('sleep_between_requests', 3))
                    
                    # iframe 전환
                    try:
                        iframe = await self.page.query_selector('iframe[name="cafe_main"]')
                        if iframe:
                            frame = await iframe.content_frame()
                            if frame:
                                current_page = frame
                            else:
                                current_page = self.page
                        else:
                            current_page = self.page
                    except Exception as e:
                        self.logger.warning(f"페이지 {page + 1} iframe 로드 실패: {e}")
                        current_page = self.page
                    
                    # HTML 파싱
                    page_content = await current_page.content()
                    soup = BeautifulSoup(page_content, 'html.parser')
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
                        
                        # 최대 번호 업데이트
                        if matching_number > current_max_num:
                            current_max_num = matching_number
                        
                        # 이미 처리한 게시글인지 확인
                        if matching_number <= last_search_num:
                            self.logger.info(f"이미 처리된 게시글 도달: {matching_number}")
                            stop_crawling = True
                            break
                        
                        # 쇼핑몰 링크 추출
                        shopping_link = await self.get_shopping_link_async(article_info['article_url'])
                        
                        # 데이터 행 생성
                        row_data = create_dataframe_row(
                            article_info['matching_number'],
                            article_info['article_title'],
                            article_info['product_title'],
                            article_info['price'],
                            shopping_link
                        )
                        
                        new_articles.append(row_data)
                        self.logger.info(f"새 게시글 추가: {matching_number} - {article_info['product_title']}")
                    
                    if stop_crawling:
                        break
                        
                except Exception as e:
                    self.logger.error(f"페이지 {page + 1} 처리 실패: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"크롤링 실패: {e}")
        
        finally:
            await self.close_browser()
        
        self.logger.info(f"크롤링 완료: {len(new_articles)}개 새 게시글")
        return new_articles, current_max_num 