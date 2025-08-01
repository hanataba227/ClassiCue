# pages/login.py  ★전면교체
import streamlit as st
from utils.auth import sign_in, sign_out, get_current_user

st.set_page_config(page_title="로그인", layout="centered")

# CSS 스타일 로드
try:
    with open("static/classical_styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.markdown(
    """
    <div class="classical-header">
        <h1>🔐 로그인</h1>
        <p>클래식 곡 설명 생성기에 오신 것을 환영합니다</p>
    </div>
    """,
    unsafe_allow_html=True
)

user = get_current_user()

if user:
    st.markdown(
        """
        <div class="info-box info-box-green">
            <h3>✅ 로그인 성공!</h3>
            <p>원하시는 페이지로 이동하거나 메인 페이지에서 시작하세요.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 사용자 정보 표시
    st.markdown(f"**👤 사용자:** {user.email}")
    st.markdown(f"**🎭 역할:** {'관리자' if st.session_state.get('sb_role') == 'admin' else '일반 사용자'}")
    
    st.divider()
    
    # 사용자 역할에 따른 버튼 표시
    role = st.session_state.get("sb_role", "user")
    
    if role == "admin":
        st.markdown("### 🛠️ 관리자 메뉴")
        # 관리자용 5개 버튼
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        with col1:
            if st.button("🏠 메인 페이지", use_container_width=True):
                st.switch_page("app.py")
        with col2:
            if st.button("🎫 공연 등록", use_container_width=True):
                st.switch_page("pages/admin_dashboard.py")
        with col3:
            if st.button("🗑️ 공연 관리", use_container_width=True):
                st.switch_page("pages/admin_manage.py")
        with col4:
            if st.button("🔧 프롬프트 관리", use_container_width=True):
                st.switch_page("pages/prompt_manager.py")
    else:
        st.markdown("### 👤 사용자 메뉴")
        # 일반 사용자용 3개 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🏠 메인 페이지", use_container_width=True):
                st.switch_page("app.py")
        with col2:
            if st.button("🎵 공연 보기", use_container_width=True):
                st.switch_page("pages/concert_view.py")
            
else:
    with st.form("login_form"):
        email    = st.text_input("이메일", placeholder="admin@test.com")
        password = st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인"):
            try:
                sign_in(email, password)
                st.success("✅ 로그인 성공! 메인 페이지로 이동합니다...")
                st.switch_page("app.py")
            except Exception as e:
                st.error(f"❌ 로그인 실패: {str(e)}")
                st.info("이메일과 비밀번호를 확인해주세요.")