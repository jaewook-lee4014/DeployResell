"""
맘이베베 핫딜 대시보드
Streamlit을 사용한 웹 대시보드
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
import re
import numpy as np
import hashlib

# 페이지 설정
st.set_page_config(
    page_title="맘이베베 핫딜 대시보드",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 비밀번호 설정 - Streamlit Secrets 사용
def get_dashboard_password():
    """Streamlit Secrets에서 비밀번호 가져오기"""
    try:
        return st.secrets["dashboard"]["password"]
    except KeyError:
        # Secrets가 설정되지 않은 경우 기본값 사용 (개발용)
        st.warning("⚠️ Secrets가 설정되지 않았습니다. 기본 비밀번호를 사용합니다.")
        return "hotdeal2024"

def check_password():
    """비밀번호 확인 함수"""
    def password_entered():
        """비밀번호 입력 확인"""
        dashboard_password = get_dashboard_password()
        if st.session_state["password"] == dashboard_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 보안을 위해 비밀번호 삭제
        else:
            st.session_state["password_correct"] = False

    # 로그인 상태 확인
    if "password_correct" not in st.session_state:
        # 첫 방문 - 비밀번호 입력 화면
        st.markdown("""
        <div style="
            max-width: 400px; 
            margin: 100px auto; 
            padding: 2rem; 
            background: white; 
            border-radius: 10px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
        ">
            <h2>🔐 대시보드 접근</h2>
            <p>비밀번호를 입력하여 대시보드에 접근하세요</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input(
                "비밀번호", 
                type="password", 
                on_change=password_entered, 
                key="password",
                placeholder="비밀번호를 입력하세요"
            )
        return False
    elif not st.session_state["password_correct"]:
        # 비밀번호 틀림
        st.markdown("""
        <div style="
            max-width: 400px; 
            margin: 100px auto; 
            padding: 2rem; 
            background: white; 
            border-radius: 10px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
        ">
            <h2>🔐 대시보드 접근</h2>
            <p>비밀번호를 입력하여 대시보드에 접근하세요</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.error("❌ 비밀번호가 올바르지 않습니다.")
            st.text_input(
                "비밀번호", 
                type="password", 
                on_change=password_entered, 
                key="password",
                placeholder="비밀번호를 입력하세요"
            )
        return False
    else:
        # 비밀번호 맞음 - 대시보드 표시
        return True

# 로그아웃 함수
def logout():
    """로그아웃 함수"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        position: relative;
    }
    
    .logout-btn {
        position: absolute;
        top: 1rem;
        right: 1rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .deal-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        transition: transform 0.2s;
    }
    
    .deal-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .price-comparison {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 1rem 0;
    }
    
    .price-hot {
        color: #e74c3c;
        font-weight: bold;
        font-size: 1.2em;
    }
    
    .price-naver {
        color: #2ecc71;
        font-weight: bold;
        font-size: 1.1em;
    }
    
    .savings {
        background: #e8f5e8;
        color: #27ae60;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .free-shipping {
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.9em;
        font-weight: bold;
    }
    
    .paid-shipping {
        background: #fff3e0;
        color: #f57c00;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.9em;
    }
    
    .sidebar .stSelectbox > div > div {
        background-color: #f8f9fa;
    }
    
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 한글 날짜 파싱 함수
def parse_korean_datetime(date_str):
    try:
        date_str = str(date_str).strip()
        
        # 형식 1: "6월 13일 16시 42분"
        pattern1 = r'(\d{1,2})월 (\d{1,2})일 (\d{1,2})시 (\d{1,2})분'
        match1 = re.match(pattern1, date_str)
        
        if match1:
            month, day, hour, minute = match1.groups()
            # 현재 연도 사용
            year = datetime.now().year
            return datetime(year, int(month), int(day), int(hour), int(minute))
        
        # 형식 2: "2024년 06월 14일 오후 02:16:42"
        pattern2 = r'(\d{4})년 (\d{2})월 (\d{2})일 (오전|오후) (\d{2}):(\d{2}):(\d{2})'
        match2 = re.match(pattern2, date_str)
        
        if match2:
            year, month, day, ampm, hour, minute, second = match2.groups()
            hour = int(hour)
            
            # 오후이고 12시가 아닌 경우 12를 더함
            if ampm == '오후' and hour != 12:
                hour += 12
            # 오전이고 12시인 경우 0시로 변경
            elif ampm == '오전' and hour == 12:
                hour = 0
                
            return datetime(int(year), int(month), int(day), hour, int(minute), int(second))
        
        # 다른 형식도 시도
        return pd.to_datetime(date_str, errors='coerce')
    except:
        return pd.NaT

# 데이터 로드 함수
@st.cache_data(ttl=300)
def load_data():
    try:
        data_path = Path(__file__).parent / "data" / "results.xlsx"
        df = pd.read_excel(data_path)
        
        # 한글 날짜 파싱
        df['시간'] = df['시간'].apply(parse_korean_datetime)
        
        # 유효하지 않은 날짜 데이터 제거
        df = df.dropna(subset=['시간'])
        
        # "검색 실패" 텍스트를 NaN으로 변환
        df = df.replace('검색 실패', np.nan)
        
        # 가격 데이터 정제
        df['핫딜몰 가격'] = pd.to_numeric(df['핫딜몰 가격'].astype(str).str.replace(',', ''), errors='coerce')
        df['네이버 가격'] = pd.to_numeric(df['네이버 가격'].astype(str).str.replace(',', ''), errors='coerce')
        
        # 유효하지 않은 가격 데이터가 있는 행 제거
        df = df.dropna(subset=['핫딜몰 가격'])
        
        # NaN 값 처리
        df['쇼핑몰 제목'] = df['쇼핑몰 제목'].fillna('알 수 없음')
        df['네이버 배송료'] = df['네이버 배송료'].fillna('검색 실패')
        # 네이버 가격은 NaN으로 유지 (검색 실패한 경우)
        
        # 가격 차이 계산
        df['가격 차이'] = df['네이버 가격'].fillna(0) - df['핫딜몰 가격'].fillna(0)
        df['가격 차이율'] = (df['가격 차이'] / df['핫딜몰 가격'].replace(0, np.nan) * 100).round(1)
        
        # 배송비 무료 여부
        df['무료배송'] = df['네이버 배송료'].str.contains('무료', na=False)
        
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

# 메인 함수
def main():
    # 헤더와 로그아웃 버튼
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown("""
        <div class="main-header">
            <h1>🛍️ 맘이베베 핫딜 대시보드</h1>
            <p>실시간 가격 비교 및 핫딜 정보를 한눈에 확인하세요</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # 여백 추가
        if st.button("🚪 로그아웃", key="logout_btn", use_container_width=True):
            logout()
    
    # 데이터 로드
    df = load_data()
    if df.empty:
        st.error("📂 데이터를 불러올 수 없습니다. Excel 파일이 올바른 위치에 있는지 확인해주세요.")
        return
    
    # 디버깅 정보 (개발용)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 데이터 정보")
    st.sidebar.write(f"총 데이터 수: {len(df)}")
    if not df.empty:
        # 유효한 날짜만 필터링
        valid_dates = df['시간'].dropna()
        if not valid_dates.empty:
            st.sidebar.write(f"날짜 범위: {valid_dates.min().strftime('%Y-%m-%d')} ~ {valid_dates.max().strftime('%Y-%m-%d')}")
        else:
            st.sidebar.write("날짜 데이터: 유효한 날짜 없음")
        
        # 유효한 가격만 필터링
        valid_prices = df['핫딜몰 가격'].dropna()
        if not valid_prices.empty:
            st.sidebar.write(f"가격 범위: {valid_prices.min():,.0f}원 ~ {valid_prices.max():,.0f}원")
        else:
            st.sidebar.write("가격 데이터: 유효한 가격 없음")
    
    # 사이드바 필터
    with st.sidebar:
        st.markdown("### 🔍 필터 옵션")
        
        # 날짜 필터
        st.markdown("#### 📅 날짜 범위")
        date_range = st.date_input(
            "날짜 선택",
            value=(datetime.now() - timedelta(days=7), datetime.now()),
            max_value=datetime.now(),
            key="date_filter",
            label_visibility="collapsed"
        )
        
        # 가격 필터
        st.markdown("#### 💰 가격 범위")
        max_price = int(df['핫딜몰 가격'].max()) if not df.empty else 1000000
        min_price, max_price_filter = st.slider(
            "가격 범위 선택",
            0, max_price, (0, max_price),
            step=1000,
            format="%d원",
            label_visibility="collapsed"
        )
        
        # 배송비 필터
        st.markdown("#### 🚚 배송비 옵션")
        shipping_options = st.radio(
            "배송비 선택",
            ["전체", "무료배송만", "유료배송만"],
            key="shipping_filter",
            label_visibility="collapsed"
        )
        
        # 쇼핑몰 필터
        st.markdown("#### 🏪 쇼핑몰 선택")
        mall_list = ["전체"] + sorted(df['쇼핑몰 제목'].unique().tolist())
        mall_filter = st.selectbox("쇼핑몰 선택", mall_list, key="mall_filter", label_visibility="collapsed")
        
        # 검색어 필터
        st.markdown("#### 🔎 상품명 검색")
        search_query = st.text_input("상품명 검색", placeholder="검색어를 입력하세요...", label_visibility="collapsed")
        
        # 새로고침 버튼
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # 데이터 필터링
    # 날짜 범위 처리 (단일 날짜 또는 범위 모두 처리)
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    else:
        # 단일 날짜인 경우
        single_date = pd.to_datetime(date_range) if not isinstance(date_range, (list, tuple)) else pd.to_datetime(date_range[0])
        start_date = single_date
        end_date = single_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    mask = (
        (df['시간'] >= start_date) &
        (df['시간'] <= end_date) &
        (df['핫딜몰 가격'] >= min_price) &
        (df['핫딜몰 가격'] <= max_price_filter)
    )
    
    if shipping_options == "무료배송만":
        mask &= df['무료배송']
    elif shipping_options == "유료배송만":
        mask &= ~df['무료배송']
    
    if mall_filter != "전체":
        mask &= df['쇼핑몰 제목'] == mall_filter
    
    if search_query:
        mask &= df['핫딜몰 제품명'].str.contains(search_query, case=False, na=False)
    
    filtered_df = df[mask]
    
    # 필터링 결과 디버깅
    st.sidebar.write(f"필터링 후: {len(filtered_df)}개")
    if len(filtered_df) == 0:
        st.sidebar.write("⚠️ 필터 조건을 확인하세요:")
        try:
            st.sidebar.write(f"- 선택된 날짜: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        except:
            st.sidebar.write(f"- 선택된 날짜: {start_date} ~ {end_date}")
        st.sidebar.write(f"- 가격 범위: {min_price:,}원 ~ {max_price_filter:,}원")
        st.sidebar.write(f"- 배송비: {shipping_options}")
        st.sidebar.write(f"- 쇼핑몰: {mall_filter}")
    
    # 상단 통계 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_products = len(filtered_df)
        st.markdown(f"""
        <div class="metric-card">
            <h3>📦 총 상품 수</h3>
            <h2 style="color: #667eea;">{total_products:,}개</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        free_shipping = filtered_df['무료배송'].sum() if not filtered_df.empty else 0
        free_shipping_rate = (free_shipping / total_products * 100) if total_products > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>🚚 무료배송</h3>
            <h2 style="color: #2ecc71;">{free_shipping}개</h2>
            <p style="color: #7f8c8d;">({free_shipping_rate:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_discount = filtered_df['가격 차이'].mean() if not filtered_df.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>💸 평균 할인</h3>
            <h2 style="color: #e74c3c;">{avg_discount:,.0f}원</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        max_discount = filtered_df['가격 차이'].max() if not filtered_df.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎯 최대 할인</h3>
            <h2 style="color: #f39c12;">{max_discount:,.0f}원</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # 메인 콘텐츠 영역
    col_main, col_chart = st.columns([2, 1])
    
    with col_main:
        st.markdown("### 🔥 최신 핫딜 목록")
        
        if filtered_df.empty:
            st.info("🔍 조건에 맞는 상품이 없습니다. 필터 조건을 조정해보세요.")
        else:
            # 정렬 옵션
            sort_option = st.selectbox(
                "정렬 기준",
                ["최신순", "할인율 높은순", "할인금액 높은순", "가격 낮은순"],
                key="sort_option"
            )
            
            if sort_option == "최신순":
                display_df = filtered_df.sort_values('시간', ascending=False)
            elif sort_option == "할인율 높은순":
                display_df = filtered_df.sort_values('가격 차이율', ascending=False)
            elif sort_option == "할인금액 높은순":
                display_df = filtered_df.sort_values('가격 차이', ascending=False)
            else:  # 가격 낮은순
                display_df = filtered_df.sort_values('핫딜몰 가격', ascending=True)
            
            # 상품 카드 표시
            for card_idx, (idx, row) in enumerate(display_df.head(15).iterrows()):
                price_diff = row['가격 차이']
                price_diff_rate = row['가격 차이율']
                
                # 할인 정보
                if price_diff > 0:
                    savings_text = f"💰 {price_diff:,.0f}원 절약 ({price_diff_rate:.1f}% 할인)"
                    savings_color = "#27ae60"
                else:
                    savings_text = "가격 비교 불가"
                    savings_color = "#7f8c8d"
                
                # 배송비 정보
                shipping_info = row['네이버 배송료']
                if '무료' in str(shipping_info):
                    shipping_badge = f'<span class="free-shipping">🚚 무료배송</span>'
                else:
                    shipping_badge = f'<span class="paid-shipping">🚚 {shipping_info}</span>'
                
                # 상품 카드를 컨테이너로 표시
                with st.container():
                    # 제품명
                    st.markdown(f"### {row['핫딜몰 제품명']}")
                    
                    # 가격 비교 섹션
                    col_price1, col_price2, col_info = st.columns([1, 1, 1])
                    
                    with col_price1:
                        st.metric(
                            "🔥 핫딜몰 가격",
                            f"{row['핫딜몰 가격']:,}원"
                        )
                    
                    with col_price2:
                        if pd.notna(row['네이버 가격']):
                            st.metric(
                                "🛒 네이버 최저가",
                                f"{row['네이버 가격']:,}원",
                                f"{price_diff:,}원" if price_diff != 0 else None,
                                delta_color="inverse" if price_diff > 0 else "normal"
                            )
                        else:
                            st.metric(
                                "🛒 네이버 최저가",
                                "검색 실패",
                                help="네이버쇼핑에서 해당 상품을 찾을 수 없습니다"
                            )
                    
                    with col_info:
                        # 할인 정보
                        if pd.notna(row['네이버 가격']) and price_diff > 0:
                            st.success(f"💰 {price_diff:,}원 절약\n({price_diff_rate:.1f}% 할인)")
                        elif pd.notna(row['네이버 가격']) and price_diff < 0:
                            st.error(f"⚠️ {abs(price_diff):,}원 더 비쌈\n({abs(price_diff_rate):.1f}% 더 비쌈)")
                        elif pd.notna(row['네이버 가격']) and price_diff == 0:
                            st.info("💯 동일한 가격")
                        else:
                            st.warning("🔍 가격 비교 불가\n(네이버 검색 실패)")
                        
                        # 배송비 정보
                        if shipping_info == '검색 실패':
                            st.warning("🚚 배송비 정보 없음")
                        elif '무료' in str(shipping_info):
                            st.success(f"🚚 {shipping_info}")
                        else:
                            st.info(f"🚚 {shipping_info}")
                    
                    # 링크 버튼들
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                    
                    with col_btn1:
                        st.link_button(
                            "🛒 핫딜몰 바로가기",
                            row['핫딜몰 링크'],
                            use_container_width=True
                        )
                    
                    with col_btn2:
                        if pd.notna(row['네이버 주소']) and row['네이버 주소'] != '검색 실패':
                            st.link_button(
                                "🔍 네이버쇼핑",
                                row['네이버 주소'],
                                use_container_width=True
                            )
                        else:
                            st.button("🔍 네이버쇼핑", disabled=True, use_container_width=True, key=f"naver_disabled_btn_{card_idx}")
                    
                    with col_btn3:
                        # 상품 정보
                        st.caption(f"📅 {row['시간'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['시간']) else '날짜 정보 없음'} | 🏪 {row['쇼핑몰 제목']}")
                    
                    st.divider()  # 구분선
    
    with col_chart:
        st.markdown("### 📊 분석 차트")
        
        if not filtered_df.empty:
            # 가격 차이 분포
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown("#### 💹 가격 차이 분포")
            fig_hist = px.histogram(
                filtered_df,
                x='가격 차이',
                nbins=20,
                title="",
                color_discrete_sequence=['#667eea']
            )
            fig_hist.update_layout(
                xaxis_title="가격 차이 (원)",
                yaxis_title="상품 수",
                showlegend=False,
                height=300
            )
            fig_hist.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="동일가격")
            st.plotly_chart(fig_hist, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 배송비 현황
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown("#### 🚚 배송비 현황")
            shipping_stats = filtered_df['무료배송'].value_counts()
            if not shipping_stats.empty:
                labels = ['유료배송', '무료배송'] if len(shipping_stats) == 2 else (['무료배송'] if shipping_stats.index[0] else ['유료배송'])
                fig_pie = px.pie(
                    values=shipping_stats.values,
                    names=labels,
                    title="",
                    color_discrete_sequence=['#e74c3c', '#2ecc71']
                )
                fig_pie.update_layout(height=300, showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 시간대별 핫딜 등록 현황
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown("#### ⏰ 시간대별 현황")
            hourly_data = filtered_df.groupby(filtered_df['시간'].dt.hour).size()
            fig_time = px.bar(
                x=hourly_data.index,
                y=hourly_data.values,
                title="",
                color_discrete_sequence=['#f39c12']
            )
            fig_time.update_layout(
                xaxis_title="시간",
                yaxis_title="등록 수",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_time, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 하단 추가 정보
    st.markdown("---")
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("### 📈 상위 할인 상품")
        if not filtered_df.empty:
            top_discounts = filtered_df.nlargest(5, '가격 차이')[['핫딜몰 제품명', '가격 차이', '가격 차이율']]
            for _, item in top_discounts.iterrows():
                st.markdown(f"• **{item['핫딜몰 제품명'][:30]}...** - {item['가격 차이']:,.0f}원 ({item['가격 차이율']:.1f}%)")
    
    with col_info2:
        st.markdown("### 🏪 쇼핑몰별 현황")
        if not filtered_df.empty:
            mall_stats = filtered_df['쇼핑몰 제목'].value_counts().head(5)
            for mall, count in mall_stats.items():
                percentage = (count / len(filtered_df) * 100)
                st.markdown(f"• **{mall}** - {count}개 ({percentage:.1f}%)")

if __name__ == "__main__":
    if check_password():
        main() 