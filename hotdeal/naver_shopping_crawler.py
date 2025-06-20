"""
네이버쇼핑 크롤러 - Playwright 기반 개선된 버전
"""
import asyncio
import random
import time
from typing import Dict, List, Optional
from urllib.parse import quote, urljoin
from playwright.async_api import async_playwright
import logging
from bs4 import BeautifulSoup

from config import NAVER_SHOPPING_CONFIG, CRAWLING_CONFIG
from utils import safe_sleep, retry_on_failure


class NaverShoppingCrawler:
    """네이버쇼핑 크롤러 - Playwright 기반 개선된 버전"""
    
    def __init__(self, driver=None):
        # 기존 Selenium driver는 무시하고 Playwright 사용
        self.logger = logging.getLogger(__name__)
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        
    async def setup_browser(self) -> bool:
        """브라우저 설정"""
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            
            # 더 강화된 봇 감지 우회 설정
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # 검증 페이지 확인을 위해 헤드리스 비활성화
                args=[
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-extensions',
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ko-KR',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            self.page = await self.context.new_page()
            
            # 강화된 webdriver 탐지 방지
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
            """)
            
            self.logger.info("Playwright 브라우저 설정 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"Playwright 브라우저 설정 실패: {e}")
            return False
    
    async def close_browser(self):
        """브라우저 종료"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("Playwright 브라우저 종료 완료")
        except Exception as e:
            self.logger.error(f"브라우저 종료 실패: {e}")
    
    def _random_delay(self, min_seconds=2, max_seconds=5):
        """랜덤 지연"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    async def _simulate_human_behavior(self):
        """인간의 행동 모방"""
        try:
            await self.page.evaluate("""
                var event = new MouseEvent('mousemove', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': Math.random() * window.innerWidth,
                    'clientY': Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            """)
            await asyncio.sleep(random.uniform(0.5, 1.5))
        except:
            pass
    
    async def search_product_direct_url(self, product_name: str) -> bool:
        """네이버 쇼핑에서 자연스럽게 상품 검색"""
        try:
            self.logger.info(f"네이버쇼핑 검색: {product_name}")
            
            # 브라우저가 설정되지 않은 경우 설정
            if not self.page:
                if not await self.setup_browser():
                    return False
            
            # 1. 네이버 메인 접속
            main_url = "https://www.naver.com"
            print(f"🌐 네이버 메인 접속: {main_url}")
            self.logger.info(f"접속 시도: {main_url}")
            
            await self.page.goto(main_url)
            await asyncio.sleep(random.uniform(3, 5))
            
            current_url = self.page.url
            print(f"✅ 네이버 메인 접속 완료: {current_url}")
            self.logger.info(f"현재 페이지: {current_url}")
            
            # 2. 사용자처럼 마우스 움직임 시뮬레이션
            await self._simulate_human_behavior()
            
            # 3. 네이버 메인에서 검색어 입력
            await asyncio.sleep(random.uniform(2, 4))
            
            # 네이버 메인 검색창 찾기
            main_search_selectors = [
                'input[id="query"]',
                'input[name="query"]',
                'input[placeholder*="검색"]',
                '.search_input'
            ]
            
            search_executed = False
            for selector in main_search_selectors:
                try:
                    search_input = await self.page.query_selector(selector)
                    if search_input:
                        print(f"🔍 네이버 메인 검색창 발견: {selector}")
                        self.logger.info(f"메인 검색창 발견: {selector}")
                        
                        # 검색어 입력
                        await search_input.click()
                        await asyncio.sleep(0.5)
                        
                        # 기존 내용 지우기
                        await search_input.fill("")
                        await asyncio.sleep(0.5)
                        
                        # 검색어 입력
                        await search_input.type(product_name, delay=50)
                        
                        print(f"⌨️  메인 검색어 입력 완료: {product_name}")
                        self.logger.info(f"메인 검색어 입력 완료: {product_name}")
                        
                        await asyncio.sleep(1)
                        await search_input.press('Enter')
                        
                        # 검색 결과 대기
                        try:
                            await self.page.wait_for_load_state('networkidle', timeout=15000)
                        except:
                            await asyncio.sleep(3)
                        
                        await asyncio.sleep(random.uniform(2, 4))
                        
                        current_url = self.page.url
                        print(f"✅ 네이버 통합검색 결과: {current_url}")
                        self.logger.info(f"통합검색 결과: {current_url}")
                        
                        search_executed = True
                        break
                        
                except Exception as e:
                    print(f"❌ 메인 검색 시도 실패 ({selector}): {e}")
                    self.logger.debug(f"메인 검색 시도 실패 ({selector}): {e}")
                    continue
            
            if not search_executed:
                print("❌ 메인 검색 실행 실패")
                self.logger.error("메인 검색 실행 실패")
                return False
            
            # 4. 쇼핑 탭 클릭
            await asyncio.sleep(random.uniform(2, 4))
            
            shopping_tab_selectors = [
                'a[href*="shopping.naver.com"]',
                '.tab a:has-text("쇼핑")',
                '.gnb_item a[href*="shopping"]',
                'a:has-text("쇼핑")'
            ]
            
            shopping_clicked = False
            for selector in shopping_tab_selectors:
                try:
                    shopping_tabs = await self.page.query_selector_all(selector)
                    for shopping_tab in shopping_tabs:
                        try:
                            tab_text = await shopping_tab.text_content()
                            if tab_text and ("쇼핑" in tab_text or "SHOP" in tab_text.upper()):
                                print(f"🛒 쇼핑 탭 발견: {tab_text} ({selector})")
                                self.logger.info(f"쇼핑 탭 발견: {tab_text}")
                                
                                await shopping_tab.click()
                                await asyncio.sleep(random.uniform(3, 5))
                                
                                current_url = self.page.url
                                print(f"✅ 쇼핑 탭 이동 완료: {current_url}")
                                self.logger.info(f"쇼핑 탭 이동 완료: {current_url}")
                                
                                # 접속 제한 확인
                                page_content = await self.page.content()
                                if "잠시 후 다시 확인해주세요" in page_content or "접속이 일시적으로 제한" in page_content:
                                    print("🚫 쇼핑 탭 접속 제한 감지!")
                                    continue
                                
                                shopping_clicked = True
                                break
                        except Exception as e:
                            continue
                    
                    if shopping_clicked:
                        break
                        
                except Exception as e:
                    print(f"❌ 쇼핑 탭 시도 실패 ({selector}): {e}")
                    continue
            
            if not shopping_clicked:
                print("💰 쇼핑 탭 클릭 실패 - 통합검색 결과 사용")
                self.logger.info("쇼핑 탭 없음, 통합검색 결과 사용")
            
            # 5. 가격비교 탭으로 이동 (있으면)
            await asyncio.sleep(2)
            
            try:
                # 가격비교 탭 셀렉터들
                compare_selectors = [
                    'a[href*="productSet=model"]',
                    'button[data-value="model"]',
                    '.filter_tab a:has-text("가격비교")',
                    'a:has-text("가격비교")'
                ]
                
                for selector in compare_selectors:
                    try:
                        price_compare_tab = await self.page.query_selector(selector)
                        if price_compare_tab:
                            compare_href = await price_compare_tab.get_attribute('href')
                            print(f"💰 가격비교 탭 발견: {compare_href}")
                            self.logger.info(f"가격비교 탭 발견: {compare_href}")
                            
                            await price_compare_tab.click()
                            await asyncio.sleep(random.uniform(3, 5))
                            
                            current_url = self.page.url
                            print(f"✅ 가격비교 페이지: {current_url}")
                            self.logger.info(f"가격비교 페이지: {current_url}")
                            
                            self.logger.info(f"가격비교 탭 이동 성공: {selector}")
                            break
                    except Exception as e:
                        print(f"❌ 가격비교 탭 시도 실패 ({selector}): {e}")
                        self.logger.debug(f"가격비교 탭 시도 실패 ({selector}): {e}")
                        continue
                else:
                    print("💰 가격비교 탭 없음 - 일반 검색 결과 사용")
                    self.logger.info("가격비교 탭 없음, 일반 검색 결과 사용")
                    
            except Exception as e:
                print(f"❌ 가격비교 탭 이동 실패: {e}")
                self.logger.warning(f"가격비교 탭 이동 실패: {e}")
            
            # 6. 최종 페이지 확인
            page_content = await self.page.content()
            current_url = self.page.url
            print(f"🔍 최종 페이지 확인: {current_url}")
            
            # 검증 페이지 확인
            if await self._check_verification_page():
                print("🤖 네이버 검증 페이지 감지!")
                print("📋 가능한 해결 방법:")
                print("   1. 브라우저에서 수동으로 검증 완료")
                print("   2. 캡차 또는 보안문자 입력")
                print("   3. 잠시 기다린 후 다시 시도")
                
                # 수동 검증 대기
                if await self._wait_for_manual_verification():
                    print("✅ 검증 완료, 계속 진행")
                    current_url = self.page.url
                    print(f"🔍 검증 후 페이지: {current_url}")
                else:
                    print("❌ 검증 실패 또는 시간 초과")
                    self.logger.error("네이버 검증 실패")
                    return False
            
            if "접속이 일시적으로 제한" in page_content or "잠시 후 다시 확인해주세요" in page_content:
                print("🚫 네이버 쇼핑 접속 제한 감지!")
                self.logger.error("네이버 쇼핑 접속 제한 감지")
                return False
            
            print("✅ 검색 완료, 페이지 로드 성공")
            self.logger.info("검색 완료, 페이지 로드 성공")
            return True
            
        except Exception as e:
            print(f"❌ 전체 검색 과정 실패: {e}")
            self.logger.error(f"상품 검색 실패 ({product_name}): {str(e)}")
            return False
    
    async def get_price_comparison_info_v2(self) -> Optional[Dict]:
        """가격비교 페이지에서 정보 추출"""
        try:
            await self._simulate_human_behavior()
            
            # 접속 제한 확인
            page_content = await self.page.content()
            if "접속이 일시적으로 제한" in page_content:
                self.logger.error("네이버 쇼핑 접속 제한 감지")
                return self._create_no_data_result("접속 제한")
            
            # 현재 URL 저장
            current_url = self.page.url
            
            # 가격비교 페이지인지 확인
            is_price_compare = 'productSet=model' in current_url or '가격비교' in page_content
            
            if is_price_compare:
                # 가격비교 페이지에서 첫 번째 상품의 쇼핑몰별 가격 정보 추출
                return await self._extract_price_comparison_details()
            else:
                # 일반 검색 결과에서 기본 정보 추출
                return await self._extract_basic_product_info(current_url)
                
        except Exception as e:
            self.logger.error(f"가격비교 정보 추출 실패: {str(e)}")
            return self._create_no_data_result("에러 발생")

    async def _extract_price_comparison_details(self) -> Dict:
        """가격비교 페이지에서 상세 쇼핑몰별 가격 정보 추출"""
        try:
            # 첫 번째 상품 클릭하여 상세 페이지로 이동
            first_product = await self.page.query_selector('.basicList_item__2XT81:first-child a, .product_item:first-child a, .basicList_link__1MaTN')
            if first_product:
                await first_product.click()
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)
                self.logger.info("첫 번째 상품 클릭 완료")
            
            # 상품명 추출
            product_name = await self._extract_product_name()
            
            # 쇼핑몰별 가격 리스트 추출
            mall_prices = await self._extract_all_mall_prices()
            
            # 최저가 계산
            min_price = "가격 정보 없음"
            if mall_prices:
                prices = []
                for mall_info in mall_prices:
                    price_str = mall_info.get('price', '0').replace(',', '').replace('원', '')
                    if price_str.isdigit():
                        prices.append(int(price_str))
                if prices:
                    min_price = f"{min(prices):,}원"
            
            # 전체 리뷰 수 추출
            review_count = await self._extract_review_count()
            
            result = {
                'naver_link': self.page.url,
                'catalog_id': self._extract_catalog_id_from_url(self.page.url),
                'product_name': product_name,
                'price': min_price,
                'delivery_info': f"가격비교 상세 (총 {len(mall_prices)}개 쇼핑몰)",
                'review_count': review_count,
                'mall_prices': mall_prices  # 쇼핑몰별 가격 리스트
            }
            
            self.logger.info(f"가격비교 상세 추출 완료 - 상품명: {product_name[:30]}..., 쇼핑몰: {len(mall_prices)}개")
            return result
            
        except Exception as e:
            self.logger.error(f"가격비교 상세 추출 실패: {e}")
            return self._create_no_data_result("상세 추출 실패")

    async def _extract_all_mall_prices(self) -> List[Dict]:
        """모든 쇼핑몰의 가격 정보 추출"""
        mall_prices = []
        
        # 쇼핑몰별 가격 정보 셀렉터들
        price_selectors = [
            '.productByMall_list_item__2-vzc',  # 쇼핑몰별 아이템
            '.mall_list_item',
            '.price_mall_item',
            '.basicList_mall_item__1wXSo'
        ]
        
        for selector in price_selectors:
            try:
                mall_items = await self.page.query_selector_all(selector)
                if mall_items:
                    self.logger.info(f"쇼핑몰 아이템 {len(mall_items)}개 발견: {selector}")
                    
                    for i, item in enumerate(mall_items[:20]):  # 최대 20개 쇼핑몰
                        try:
                            mall_info = await self._extract_single_mall_info(item)
                            if mall_info and mall_info['mall_name'] != "정보없음":
                                mall_prices.append(mall_info)
                                
                        except Exception as e:
                            self.logger.debug(f"쇼핑몰 {i+1} 정보 추출 실패: {e}")
                            continue
                    
                    break  # 성공한 셀렉터에서 결과를 얻었으면 중단
                    
            except Exception as e:
                self.logger.debug(f"쇼핑몰 셀렉터 실패 ({selector}): {e}")
                continue
        
        # 가격 순으로 정렬
        if mall_prices:
            mall_prices.sort(key=lambda x: int(x['price'].replace(',', '').replace('원', '')) if x['price'].replace(',', '').replace('원', '').isdigit() else 999999999)
        
        return mall_prices

    async def _extract_single_mall_info(self, item_element) -> Dict:
        """단일 쇼핑몰 정보 추출"""
        try:
            # 쇼핑몰명 추출
            mall_selectors = [
                '.productByMall_mall_name__3qkWl',
                '.mall_name',
                '.shop_name',
                'img[alt]'  # 쇼핑몰 로고 alt 텍스트
            ]
            
            mall_name = "정보없음"
            for selector in mall_selectors:
                try:
                    element = await item_element.query_selector(selector)
                    if element:
                        if selector == 'img[alt]':
                            mall_name = await element.get_attribute('alt')
                        else:
                            mall_name = await element.inner_text()
                        if mall_name and mall_name.strip():
                            mall_name = mall_name.strip()
                            break
                except:
                    continue
            
            # 가격 추출
            price_selectors = [
                '.productByMall_price__1y4Gx',
                '.price_num',
                '.mall_price',
                'strong'
            ]
            
            price = "가격없음"
            for selector in price_selectors:
                try:
                    element = await item_element.query_selector(selector)
                    if element:
                        price_text = await element.inner_text()
                        if price_text and ('원' in price_text or ',' in price_text):
                            # 숫자만 추출
                            numbers = re.findall(r'[\d,]+', price_text.replace(',', ''))
                            if numbers:
                                price_value = max([int(num) for num in numbers if num.isdigit()])
                                if price_value > 100:
                                    price = f"{price_value:,}원"
                                    break
                except:
                    continue
            
            # 배송비 추출
            delivery_selectors = [
                '.productByMall_delivery__2KCTD',
                '.delivery_info',
                '.shipping_fee'
            ]
            
            delivery = "배송비정보없음"
            for selector in delivery_selectors:
                try:
                    element = await item_element.query_selector(selector)
                    if element:
                        delivery = await element.inner_text()
                        if delivery and delivery.strip():
                            delivery = delivery.strip()
                            break
                except:
                    continue
            
            return {
                'mall_name': mall_name,
                'price': price,
                'delivery': delivery
            }
            
        except Exception as e:
            self.logger.debug(f"단일 쇼핑몰 정보 추출 실패: {e}")
            return {
                'mall_name': "정보없음",
                'price': "가격없음", 
                'delivery': "배송비정보없음"
            }

    async def _extract_basic_product_info(self, current_url: str) -> Dict:
        """일반 검색 결과에서 기본 정보 추출"""
        # 제품명 추출
        product_name = await self._extract_product_name()
        
        # 가격 정보 추출
        price = await self._extract_price()
        
        # 리뷰 수 추출
        review_count = await self._extract_review_count()
        
        # 추가 정보 추출
        shop_count = await self._extract_shop_count()
        
        result = {
            'naver_link': current_url,
            'catalog_id': self._extract_catalog_id_from_url(current_url),
            'product_name': product_name,
            'price': price,
            'delivery_info': f"일반 검색 결과 (판매처: {shop_count}개)" if shop_count != "0" else "일반 검색 결과",
            'review_count': review_count,
            'mall_prices': []  # 일반 검색에서는 빈 리스트
        }
        
        self.logger.info(f"기본 정보 추출 완료 - 상품명: {product_name[:30]}..., 가격: {price}, 리뷰: {review_count}")
        return result
    
    async def _extract_product_name(self) -> str:
        """상품명 추출 - 가격비교 페이지 최적화"""
        # 가격비교 페이지 전용 셀렉터들
        selectors = [
            # 가격비교 페이지 상품명 셀렉터들
            '.productName_title__4_PwQ',
            '.title_area h1',
            '.product_title',
            '.basicList_title__3P9Q7',
            'h1[data-testid="product-name"]',
            
            # 일반 검색 결과 백업 셀렉터들
            'div[class*="Product"] a',
            'div[class*="card"] a',
            'a[href*="shopping.naver.com"]',
            'span[class*="title"]',
            'h2', 'h3'
        ]
        
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 5:
                        # 의미있는 상품명인지 확인 (너무 짧거나 버튼 텍스트 제외)
                        if not any(skip_word in text.lower() for skip_word in ['더보기', '접기', '선택', '구매', '장바구니']):
                            self.logger.info(f"상품명 추출 성공: {selector}")
                            return text.strip()
            except Exception as e:
                self.logger.debug(f"셀렉터 시도 실패 ({selector}): {e}")
                continue
        
        return "상품명 없음"
    
    async def _extract_price(self) -> str:
        """가격 추출 - 가격비교 최저가 중심"""
        # 가격비교 페이지의 최저가 셀렉터들
        selectors = [
            # 가격비교 페이지 최저가 셀렉터들
            '.lowPrice_num__2E3jC',
            '.price_num__2WUXn',
            '.lowestPrice_num__3AlQ-',
            '.basicList_price_num__1JUZ6',
            'strong[data-testid="lowest-price"]',
            '.product_price strong',
            
            # 일반 가격 셀렉터들 (백업)
            'span[class*="Price"]',
            'div[class*="price"]',
            'em[class*="price"]',
            'strong[class*="price"]',
            '.price'
        ]
        
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if text and ('원' in text or ',' in text):
                        # 가격에서 숫자만 추출
                        price_numbers = re.findall(r'[\d,]+', text.replace(',', ''))
                        if price_numbers:
                            # 가장 큰 숫자를 가격으로 인식 (원 단위)
                            price_value = max([int(num.replace(',', '')) for num in price_numbers if num.replace(',', '').isdigit()])
                            if price_value > 100:  # 100원 이상인 경우만
                                formatted_price = f"{price_value:,}원"
                                self.logger.info(f"가격 추출 성공: {selector} -> {formatted_price}")
                                return formatted_price
            except Exception as e:
                self.logger.debug(f"가격 셀렉터 시도 실패 ({selector}): {e}")
                continue
        
        return "가격 정보 없음"
    
    async def _extract_review_count(self) -> str:
        """리뷰 수 추출"""
        selectors = [
            # 가격비교 페이지 리뷰 셀렉터들
            '.score_num__1yGGV',
            '.reviewCount_num__2WS2m',
            '.basicList_etc_num__3aAeF',
            'span[data-testid="review-count"]',
            
            # 일반 리뷰 셀렉터들
            'span[class*="review"]',
            'div[class*="review"]',
            'a[class*="review"]',
            '.review_count'
        ]
        
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if text:
                        # 숫자 패턴 찾기
                        numbers = re.findall(r'\d+', text.replace(',', ''))
                        if numbers:
                            # 가장 큰 숫자를 리뷰수로 인식
                            review_num = max([int(num) for num in numbers if num.isdigit()])
                            self.logger.info(f"리뷰수 추출 성공: {selector} -> {review_num}")
                            return str(review_num)
            except Exception:
                continue
        
        return "0"
    
    def _extract_catalog_id_from_url(self, url: str) -> str:
        """URL에서 카탈로그 ID 추출"""
        try:
            if 'catalog' in url:
                # catalog ID 추출 로직
                parts = url.split('/')
                for i, part in enumerate(parts):
                    if part == 'catalog' and i + 1 < len(parts):
                        return parts[i + 1].split('?')[0]
            return "ID_없음"
        except Exception:
            return "ID_없음"
    
    async def _extract_shop_count(self) -> str:
        """판매처 개수 추출"""
        selectors = [
            '.shopCount_num__3JaxW',
            '.shop_count',
            'span[data-testid="shop-count"]',
            '.basicList_mall_count__2Xjqs'
        ]
        
        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        return numbers[0]
            except Exception:
                continue
        
        return "0"
    
    def search_products_batch(self, product_names: List[str]) -> List[Dict]:
        """상품 목록 일괄 검색 - 동기 인터페이스"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 이벤트 루프가 있는 경우
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.run(self._search_products_batch_async(product_names))
            else:
                return asyncio.run(self._search_products_batch_async(product_names))
        except RuntimeError:
            # 새로운 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._search_products_batch_async(product_names))
            finally:
                loop.close()
    
    async def _search_products_batch_async(self, product_names: List[str]) -> List[Dict]:
        """상품 목록 일괄 검색 - 비동기 구현"""
        self.logger.info(f"네이버쇼핑 일괄 검색 시작: {len(product_names)}개")
        
        if not product_names:
            return []
        
        results = []
        
        try:
            # 브라우저 설정
            if not await self.setup_browser():
                return [self._create_no_data_result("브라우저 설정 실패") for _ in product_names]
            
            for i, product_name in enumerate(product_names):
                self.logger.info(f"진행률: {i+1}/{len(product_names)} - {product_name}")
                
                try:
                    # 상품 검색
                    if await self.search_product_direct_url(product_name):
                        result = await self.get_price_comparison_info_v2()
                        if result:
                            results.append(result)
                        else:
                            results.append(self._create_no_data_result("정보 추출 실패"))
                    else:
                        results.append(self._create_no_data_result("검색 실패"))
                    
                    # 요청 간 지연
                    if i < len(product_names) - 1:
                        await asyncio.sleep(CRAWLING_CONFIG.get('sleep_between_requests', 3))
                        
                except Exception as e:
                    self.logger.error(f"상품 처리 실패 ({product_name}): {e}")
                    results.append(self._create_no_data_result("처리 실패"))
            
        except Exception as e:
            self.logger.error(f"일괄 검색 실패: {e}")
            # 남은 상품들에 대해 실패 결과 추가
            while len(results) < len(product_names):
                results.append(self._create_no_data_result("일괄 검색 실패"))
        
        finally:
            await self.close_browser()
        
        self.logger.info("네이버쇼핑 일괄 검색 완료")
        return results
    
    def _create_no_data_result(self, reason: str) -> Dict:
        """데이터 없음 결과 생성"""
        return {
            'naver_link': f"검색실패_{reason}",
            'catalog_id': "ID_없음",
            'product_name': "상품명_없음",
            'price': "가격_없음",
            'delivery_info': "배송정보_없음",
            'review_count': "0"
        }

    async def _check_verification_page(self) -> bool:
        """네이버 검증 페이지 확인"""
        try:
            page_content = await self.page.content()
            current_url = self.page.url
            
            # 다양한 검증 페이지 패턴 확인
            verification_patterns = [
                "잠시 후 다시 확인해주세요",
                "접속이 일시적으로 제한",
                "자동 프로그램 접속 차단",
                "captcha",
                "verification",
                "보안문자",
                "인증",
                "blocked",
                "임시 제한"
            ]
            
            for pattern in verification_patterns:
                if pattern in page_content.lower():
                    print(f"🚫 네이버 검증 페이지 감지: {pattern}")
                    print(f"🔍 현재 URL: {current_url}")
                    self.logger.warning(f"검증 페이지 감지: {pattern}")
                    
                    # 검증 페이지 스크린샷 저장
                    screenshot_path = f"verification_page_{int(time.time())}.png"
                    await self.page.screenshot(path=screenshot_path)
                    print(f"📸 검증 페이지 스크린샷 저장: {screenshot_path}")
                    
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"검증 페이지 확인 실패: {e}")
            return False

    async def _wait_for_manual_verification(self, timeout_seconds=300):
        """수동 검증 완료 대기"""
        try:
            print(f"⏳ 수동 검증 대기 중... ({timeout_seconds}초 제한)")
            print("💡 브라우저에서 검증을 완료한 후 계속됩니다.")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout_seconds:
                current_url = self.page.url
                page_content = await self.page.content()
                
                # 검증이 완료되었는지 확인
                if not await self._check_verification_page():
                    print("✅ 수동 검증 완료!")
                    return True
                
                print(f"⏳ 대기 중... ({int(time.time() - start_time)}초 경과)")
                await asyncio.sleep(5)
            
            print("⏰ 검증 대기 시간 초과")
            return False
            
        except Exception as e:
            print(f"❌ 수동 검증 대기 실패: {e}")
            return False 