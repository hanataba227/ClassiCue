# app.py ─ 메인 라우터 (관리자·사용자 공통)

import streamlit as st
st.set_page_config(page_title="클래식 곡 설명 생성기", layout="wide")

from utils.supabase_client import get_sb_client
from utils.auth import get_current_user, get_role

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

# 상단 사용자 정보 및 네비게이션
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"**👤 사용자:** {user.email} | **🎭 역할:** {'관리자' if role == 'admin' else '일반 사용자'}")

# 네비게이션 버튼
if role == "admin":
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.markdown("**📍 현재: 메인 페이지**")
    with col2:
        if st.button("🎵 공연 보기"):
            st.switch_page("pages/concert_view.py")
    with col3:
        if st.button("🎫 공연 등록"):
            st.switch_page("pages/admin_dashboard.py")
    with col4:
        if st.button("🗑️ 공연 관리"):
            st.switch_page("pages/admin_manage.py")
    with col5:
        if st.button("🔧 프롬프트 관리"):
            st.switch_page("pages/prompt_manager.py")
else:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("**📍 현재: 메인 페이지**")
    with col2:
        if st.button("🎵 공연 보기"):
            st.switch_page("pages/concert_view.py")

# 관리자 안내 메시지
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
            <h3>🎭 곧 멋진 공연들이 찾아옵니다!</h3>
            <p>현재 새로운 클래식 공연들을 준비하고 있습니다.</p>
            <p>AI가 생성하는 깊이 있는 곡 해설과 함께 클래식의 매력을 만나보세요.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if role == "admin":
        st.markdown(
            """
            <div class="info-box info-box-yellow">
                <h4>🎯 관리자 안내</h4>
                <p>첫 번째 공연을 등록하여 서비스를 시작해보세요!</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.page_link("pages/admin_dashboard.py", label="🎫 첫 공연 등록하기")
else:
    # 공연 목록을 카드 형태로 표시
    for i in range(0, len(concerts), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(concerts):
                concert = concerts[i + j]
                with col:
                    st.markdown(
                        f"""
                        <div class="concert-card">
                            <h3 class="concert-title">{concert['title']}</h3>
                            <div class="concert-info">
                                <p><strong>🏛️ 공연장:</strong> {concert['venue']}</p>
                                <p><strong>📅 일정:</strong> {concert['date']}</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # 공연 상세 보기 버튼
                    if st.button(f"🎵 {concert['title']} 상세보기", key=f"concert_{concert['id']}"):
                        st.query_params["concert_id"] = concert["id"]
                        st.switch_page("pages/concert_view.py")

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# ──────────────────────────
# 4) 푸터
# ──────────────────────────
st.markdown(
    """
    <div class="footer">
        <p>🎼 클래식 음악의 아름다움을 AI와 함께 만나보세요</p>
        <p>✨ 모든 곡 설명은 AI가 생성한 창작물입니다</p>
    </div>
    """,
    unsafe_allow_html=True
)
