"""
유틸리티 함수들
"""
import logging
import re
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import pandas as pd

from config import LOGGING_CONFIG, REGEX_PATTERNS


def setup_logging() -> logging.Logger:
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG['level']),
        format=LOGGING_CONFIG['format'],
        handlers=[
            logging.FileHandler(LOGGING_CONFIG['file'], encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def extract_price_from_title(title: str) -> int:
    """제목에서 가격 추출"""
    patterns = [
        REGEX_PATTERNS['price_6'],
        REGEX_PATTERNS['price_5'],
        REGEX_PATTERNS['price_4'],
        REGEX_PATTERNS['price_6_no_won'],
        REGEX_PATTERNS['price_5_no_won'],
        REGEX_PATTERNS['price_4_no_won']
    ]
    
    for pattern in patterns:
        match = re.match(pattern, title)
        if match:
            price_str = match.groups()[0].replace("원", "")
            try:
                return int(price_str)
            except ValueError:
                continue
    
    return 999999  # 가격을 찾을 수 없는 경우


def extract_urls_from_text(text: str) -> List[str]:
    """텍스트에서 URL 추출"""
    urls = re.findall(REGEX_PATTERNS['url'], text)
    return [url[0] for url in urls] if urls else []


def clean_product_title(title: str) -> str:
    """상품명 정제"""
    # 괄호 이후 부분만 추출
    if ')' in title:
        title = title[title.find(')') + 1:]
    
    # 불필요한 문자 제거
    title = title.replace(",", "").replace(".", "").replace('\n', "").strip()
    
    return title


def get_current_timestamp() -> str:
    """현재 시간을 문자열로 반환"""
    now = datetime.now()
    return f'{now.month}월 {now.day}일 {now.hour}시 {now.minute}분'


def safe_sleep(seconds: float) -> None:
    """안전한 슬립 (키보드 인터럽트 처리)"""
    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        logging.info("사용자에 의해 중단됨")
        raise


def create_dataframe_row(timestamp: str, source: str, article_id: int, 
                        article_url: str, original_title: str, cleaned_title: str,
                        shop_url: str, price: int) -> Dict[str, Any]:
    """데이터프레임 행 생성"""
    return {
        '시간': timestamp,
        '핫딜몰': source,
        '게시글 id': article_id,
        '핫딜몰 링크': article_url,
        '핫딜몰 제품명': original_title,
        '보정 제품명': cleaned_title,
        '쇼핑몰 주소': shop_url,
        '핫딜몰 가격': price
    }


def save_search_info(file_path: Path, search_key: int) -> None:
    """검색 정보 저장"""
    try:
        df = pd.DataFrame({'search key': [search_key]})
        df.to_excel(file_path, sheet_name="검색정보", index=False)
        logging.info(f"검색 정보 저장 완료: {search_key}")
    except Exception as e:
        logging.error(f"검색 정보 저장 실패: {e}")


def load_search_info(file_path: Path) -> Optional[int]:
    """검색 정보 로드"""
    try:
        if file_path.exists():
            df = pd.read_excel(file_path, sheet_name="검색정보")
            return int(df['search key'].iloc[0])
        else:
            # 초기 파일 생성
            save_search_info(file_path, 0)
            return 0
    except Exception as e:
        logging.error(f"검색 정보 로드 실패: {e}")
        return None


def save_results(file_path: Path, df: pd.DataFrame) -> None:
    """결과 저장"""
    try:
        if file_path.exists():
            existing_df = pd.read_excel(file_path)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            combined_df = df
        
        combined_df.to_excel(file_path, index=False)
        logging.info(f"결과 저장 완료: {len(df)}개 항목")
    except Exception as e:
        logging.error(f"결과 저장 실패: {e}")


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """재시도 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logging.warning(f"{func.__name__} 시도 {attempt + 1}/{max_retries} 실패: {e}")
                    if attempt < max_retries - 1:
                        safe_sleep(delay * (attempt + 1))
            
            logging.error(f"{func.__name__} 최대 재시도 횟수 초과")
            raise last_exception
        return wrapper
    return decorator


def validate_url(url: str) -> bool:
    """URL 유효성 검사"""
    if not url or url in ['NO_LINK', '링크 없음']:
        return False
    return url.startswith(('http://', 'https://'))


def detect_shopping_mall(url: str) -> Optional[str]:
    """URL에서 쇼핑몰 종류 감지"""
    mall_patterns = {
        'auction': 'auction',
        'lotteon': 'lotteon',
        'wemakeprice': 'wemakeprice',
        'gmarket': 'gmarket',
        'gs': 'gs',
        'tmon': 'tmon',
        '11st': '11st',
        'interpark': 'interpark',
        'coupang': 'coupang',
        'naver': 'naver',
        'brand.naver': 'brand.naver',
        'kakao': 'kakao',
        'yes24': 'yes24',
        'nsmall': 'nsmall',
        'ssg': 'ssg'
    }
    
    url_lower = url.lower()
    for pattern, mall_name in mall_patterns.items():
        if pattern in url_lower:
            return mall_name
    
    return None 