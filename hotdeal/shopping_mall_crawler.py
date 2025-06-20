"""
쇼핑몰 크롤러 - Playwright 기반
"""
import logging
import time
import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config import SHOPPING_MALL_SELECTORS, CRAWLING_CONFIG
from utils import safe_sleep, retry_on_failure, validate_url, detect_shopping_mall


class ShoppingMallCrawler:
    """쇼핑몰 크롤러 - Playwright 기반"""
    
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
            
            self.logger.info("쇼핑몰 크롤러 Playwright 브라우저 설정 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"쇼핑몰 크롤러 브라우저 설정 실패: {e}")
            return False
    
    async def close_browser(self):
        """브라우저 종료"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("쇼핑몰 크롤러 브라우저 종료 완료")
        except Exception as e:
            self.logger.error(f"쇼핑몰 크롤러 브라우저 종료 실패: {e}")
    
    async def extract_product_title_async(self, url: str) -> str:
        """쇼핑몰에서 상품명 추출 - 비동기"""
        if not validate_url(url):
            return "링크 접속불가"
        
        try:
            self.logger.info(f"쇼핑몰 접속: {url}")
            
            # 브라우저가 설정되지 않은 경우 설정
            if not self.page:
                if not await self.setup_browser():
                    return "브라우저 설정 실패"
            
            await self.page.goto(url, timeout=30000)
            await asyncio.sleep(3)  # 페이지 로딩 대기
            
            # 쇼핑몰 종류 감지
            mall_type = detect_shopping_mall(url)
            if not mall_type:
                return "모르는 사이트"
            
            # 해당 쇼핑몰의 셀렉터들로 상품명 추출 시도
            selectors = SHOPPING_MALL_SELECTORS.get(mall_type, [])
            
            for selector in selectors:
                try:
                    # XPath를 CSS 셀렉터로 변환하거나 직접 사용
                    if selector.startswith('//') or selector.startswith('/'):
                        # XPath인 경우
                        element = await self.page.query_selector(f'xpath={selector}')
                    else:
                        # CSS 셀렉터인 경우
                        element = await self.page.query_selector(selector)
                    
                    if element:
                        title = await element.inner_text()
                        if title and title.strip():
                            self.logger.info(f"상품명 추출 성공: {title}")
                            return title.strip()
                except Exception as e:
                    self.logger.debug(f"셀렉터 시도 실패 ({selector}): {e}")
                    continue
            
            # 모든 셀렉터 실패시
            return "설정된 사이트, 설정안된 태그"
            
        except Exception as e:
            self.logger.error(f"상품명 추출 실패 ({url}): {e}")
            return "링크 접속불가"
    
    def extract_product_title(self, url: str) -> str:
        """쇼핑몰에서 상품명 추출 - 동기 인터페이스"""
        return asyncio.run(self._extract_product_title_with_browser(url))
    
    async def _extract_product_title_with_browser(self, url: str) -> str:
        """브라우저 설정과 함께 상품명 추출"""
        try:
            if not await self.setup_browser():
                return "브라우저 설정 실패"
            
            result = await self.extract_product_title_async(url)
            return result
            
        finally:
            await self.close_browser()
    
    def extract_titles_from_urls(self, urls: List[str], fallback_titles: List[str]) -> List[str]:
        """URL 리스트에서 상품명들 추출 - 동기 인터페이스"""
        return asyncio.run(self._extract_titles_from_urls_async(urls, fallback_titles))
    
    async def _extract_titles_from_urls_async(self, urls: List[str], fallback_titles: List[str]) -> List[str]:
        """URL 리스트에서 상품명들 추출 - 비동기 구현"""
        self.logger.info(f"쇼핑몰 상품명 추출 시작: {len(urls)}개")
        
        if not urls:
            return []
        
        extracted_titles = []
        
        try:
            # 브라우저 설정
            if not await self.setup_browser():
                return fallback_titles  # 브라우저 설정 실패시 대체 제목 사용
            
            for i, (url, fallback_title) in enumerate(zip(urls, fallback_titles)):
                self.logger.info(f"진행률: {i+1}/{len(urls)}")
                
                title = await self.extract_product_title_async(url)
                
                # 실패한 경우 대체 제목 사용
                if title in ["설정된 사이트, 설정안된 태그", "모르는 사이트", "링크 접속불가", "브라우저 설정 실패"]:
                    title = fallback_title
                    self.logger.info(f"대체 제목 사용: {title}")
                
                extracted_titles.append(title)
                
                # 요청 간 지연
                if i < len(urls) - 1:
                    await asyncio.sleep(CRAWLING_CONFIG.get('sleep_between_requests', 3))
        
        except Exception as e:
            self.logger.error(f"일괄 추출 실패: {e}")
            # 실패한 경우 대체 제목들 반환
            extracted_titles.extend(fallback_titles[len(extracted_titles):])
        
        finally:
            await self.close_browser()
        
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