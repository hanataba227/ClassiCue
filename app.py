# app.py ─ 메인 라우터 (관리자·사용자 공통)

import streamlit as st
st.set_page_config(page_title="클래식 곡 설명 생성기", layout="wide")

from utils.supabase_client import get_sb_client
from utils.auth            import get_current_user, get_role

# CSS 스타일 로드
try:
    with open("static/classical_styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("CSS 파일을 찾을 수 없습니다. static/classical_styles.css 파일을 생성해주세요.")

sb = get_sb_client()

# ──────────────────────────
# 1) 로그인‧권한 확인
# ──────────────────────────
user = get_current_user()
if not user:
    # 로그인되지 않은 사용자를 위한 헤더
    st.markdown(
        """
        <div class="classical-header">
            <h1>🎵 클래식 곡 설명 생성기</h1>
            <p>AI가 들려주는 클래식 음악의 아름다운 이야기</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <div class="info-box info-box-pink">
            <h3>🔑 로그인이 필요합니다</h3>
            <p>클래식 공연 정보를 확인하려면 로그인해주세요.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 로그인 버튼을 스타일링된 링크로 표시
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.page_link("pages/login.py", label="🔑 로그인하기")
    st.stop()

role = get_role()

# ──────────────────────────
# 2) 헤더 + 관리자 링크
# ──────────────────────────
st.markdown(
    """
    <div class="classical-header">
        <h1>🎵 클래식 곡 설명 생성기</h1>
        <p>AI가 들려주는 클래식 음악의 아름다운 이야기</p>
    </div>
    """,
    unsafe_allow_html=True
)

# 관리자 링크는 조건부로 표시
if role == "admin":
    st.markdown(
        """
        <div class="info-box info-box-green">
            <h4>🛠️ 관리자 메뉴</h4>
            <p>새로운 공연을 생성하거나 기존 공연을 편집할 수 있습니다.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.page_link(
            "pages/admin_dashboard.py",
            label="🛠️ 공연 생성 / 편집",
        )

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ──────────────────────────
# 3) 공연 목록 (전체 공개)
# ──────────────────────────
concerts = (
    sb.table("concerts")
      .select("id,title,venue,date")
      .order("date", desc=False)
      .execute()
      .data
)

st.markdown(
    """
    <div class="concerts-container">
        <h2 class="concerts-title">📜 등록된 공연</h2>
    </div>
    """,
    unsafe_allow_html=True
)

if not concerts:
    st.markdown(
        """
        <div class="info-box info-box-blue">
            <h4>📋 등록된 공연이 없습니다</h4>
            <p>아직 등록된 공연 정보가 없습니다.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if role == "admin":
        st.markdown(
            """
            <div class="info-box info-box-gold">
                <h4>💡 관리자 안내</h4>
                <p>상단의 "공연 생성 / 편집" 버튼으로 새 공연을 추가하세요.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    for i, c in enumerate(concerts):
        # 공연 정보를 카드 형태로 표시
        st.markdown(
            f"""
            <div class="concert-card">
                <div class="concert-title">{c['title']}</div>
                <div class="concert-details">
                    <span class="concert-venue">📍 {c['venue']}</span>
                    <span style="margin: 0 1rem;">│</span>
                    <span class="concert-date">📅 {c['date']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 각 공연마다 "자세히 보기" 버튼
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            st.page_link(
                "pages/concert_view.py",
                label="🎼 자세히 보기",
                help=f"concert_id: {c['id']}"
            )
        
        # 마지막 공연이 아니라면 구분선 추가
        if i < len(concerts) - 1:
            st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)