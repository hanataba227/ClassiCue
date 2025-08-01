# pages/admin_manage.py - 공연 관리 (삭제/편집)
import streamlit as st
import uuid
from utils.supabase_client import get_sb_client
from utils.auth import require_login, get_current_user, sign_out

st.set_page_config(page_title="공연 관리", layout="wide")

# CSS 스타일 로드
try:
    with open("static/classical_styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

sb = get_sb_client(use_service=True)

# 로그인 상태 확인 및 권한 검증
if "sb_user" not in st.session_state:
    st.warning("🔑 로그인이 필요합니다.")
    st.info("메인 페이지로 이동하여 로그인해주세요.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏠 메인 페이지로 이동"):
            st.switch_page("app.py")
    st.stop()

# 어드민 권한 확인
if st.session_state.get("sb_role") != "admin":
    st.error("⚠️ 관리자 권한이 필요합니다.")
    st.info("일반 사용자는 공연 정보 조회만 가능합니다.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏠 메인 페이지로 이동"):
            st.switch_page("app.py")
    st.stop()

user = require_login(role="admin")

# 상단 헤더 및 네비게이션
st.markdown(
    """
    <div class="classical-header">
        <h1>🗑️ 공연 관리</h1>
        <p>기존 공연을 삭제하거나 편집할 수 있습니다</p>
    </div>
    """,
    unsafe_allow_html=True
)

# 네비게이션 버튼
col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
with col1:
    if st.button("🏠 메인 페이지"):
        st.switch_page("app.py")
with col2:
    if st.button("🎵 공연 보기"):
        st.switch_page("pages/concert_view.py")
with col3:
    if st.button("➕ 공연 등록"):
        st.switch_page("pages/admin_dashboard.py")
with col4:
    if st.button("🔧 프롬프트 관리"):
        st.switch_page("pages/prompt_manager.py")
with col5:
    st.markdown("**📍 현재: 공연 관리**")

st.divider()

# 공연 목록 조회
@st.cache_data(ttl=60)
def get_concerts():
    try:
        concerts = sb.table("concerts").select("*").order("created_at", desc=True).execute().data
        return concerts
    except Exception as e:
        st.error(f"공연 목록 조회 실패: {str(e)}")
        return []

concerts = get_concerts()

if not concerts:
    st.info("📝 등록된 공연이 없습니다.")
    if st.button("➕ 첫 공연 등록하기"):
        st.switch_page("pages/admin_dashboard.py")
    st.stop()

# 공연 선택
st.subheader("🎫 공연 선택")
selected_concert_id = st.selectbox(
    "관리할 공연을 선택하세요",
    options=[c["id"] for c in concerts],
    format_func=lambda x: next((f"{c['title']} ({c['venue']}, {c['date']})" for c in concerts if c["id"] == x), x),
    help="삭제하거나 편집할 공연을 선택해주세요"
)

if selected_concert_id:
    selected_concert = next((c for c in concerts if c["id"] == selected_concert_id), None)
    
    if selected_concert:
        # 선택된 공연 정보 표시
        st.markdown("---")
        st.subheader("📋 선택된 공연 정보")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**🎫 공연명:** {selected_concert['title']}")
            st.markdown(f"**🏛️ 공연장:** {selected_concert['venue']}")
            st.markdown(f"**📅 일정:** {selected_concert['date']}")
            st.markdown(f"**📝 설명:** {selected_concert['description']}")
        
        with col2:
            st.markdown("**⚠️ 위험 구역**")
            if st.button("🗑️ 전체 공연 삭제", type="secondary", use_container_width=True):
                st.session_state['show_delete_confirm'] = True
            
            if st.session_state.get('show_delete_confirm', False):
                st.error("**정말로 이 공연을 완전히 삭제하시겠습니까?**")
                st.warning("이 작업은 되돌릴 수 없습니다!")
                
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("🗑️ 예, 삭제합니다", type="primary"):
                        try:
                            # 관련 데이터 삭제 (역순)
                            # 1. track_descriptions 삭제
                            tracks_result = sb.table("concert_tracks").select("id").eq("concert_id", selected_concert_id).execute()
                            track_ids = [t["id"] for t in tracks_result.data]
                            
                            if track_ids:
                                sb.table("track_descriptions").delete().in_("track_id", track_ids).execute()
                            
                            # 2. concert_tracks 삭제
                            sb.table("concert_tracks").delete().eq("concert_id", selected_concert_id).execute()
                            
                            # 3. concerts 삭제
                            sb.table("concerts").delete().eq("id", selected_concert_id).execute()
                            
                            st.success("✅ 공연이 완전히 삭제되었습니다.")
                            st.session_state['show_delete_confirm'] = False
                            st.cache_data.clear()
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"삭제 중 오류 발생: {str(e)}")
                
                with col_no:
                    if st.button("❌ 취소"):
                        st.session_state['show_delete_confirm'] = False
                        st.rerun()
        
        # 곡별 관리
        st.markdown("---")
        st.subheader("🎵 곡별 관리")
        
        # 곡 목록 조회
        try:
            tracks = sb.table("concert_tracks").select("*").eq("concert_id", selected_concert_id).execute().data
            
            if not tracks:
                st.info("이 공연에 등록된 곡이 없습니다.")
            else:
                for i, track in enumerate(tracks):
                    with st.expander(f"🎼 {track['track_title']} - {track['composer']}", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**곡명:** {track['track_title']}")
                            st.markdown(f"**작곡가:** {track['composer']}")
                            
                            # 이 곡의 AI 설명들 조회
                            descriptions = sb.table("track_descriptions").select("*").eq("track_id", track["id"]).execute().data
                            
                            if descriptions:
                                st.markdown("**🤖 AI 설명들:**")
                                for desc in descriptions:
                                    st.markdown(f"- **{desc['prompt_type']}**: {desc['description'][:100]}...")
                            else:
                                st.info("AI 설명이 없습니다.")
                        
                        with col2:
                            st.markdown("**🗑️ 삭제 옵션**")
                            
                            # 개별 설명 삭제
                            if descriptions:
                                selected_desc = st.selectbox(
                                    "삭제할 설명 선택",
                                    options=[""] + [d["id"] for d in descriptions],
                                    format_func=lambda x: "선택하세요" if x == "" else next((d["prompt_type"] for d in descriptions if d["id"] == x), x),
                                    key=f"desc_select_{track['id']}"
                                )
                                
                                if selected_desc:
                                    if st.button(f"🗑️ 설명 삭제", key=f"del_desc_{selected_desc}"):
                                        try:
                                            sb.table("track_descriptions").delete().eq("id", selected_desc).execute()
                                            st.success("✅ 설명이 삭제되었습니다.")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"설명 삭제 실패: {str(e)}")
                            
                            # 곡 전체 삭제
                            if st.button(f"🗑️ 곡 삭제", key=f"del_track_{track['id']}", type="secondary"):
                                try:
                                    # 곡의 모든 설명 삭제
                                    sb.table("track_descriptions").delete().eq("track_id", track["id"]).execute()
                                    # 곡 삭제
                                    sb.table("concert_tracks").delete().eq("id", track["id"]).execute()
                                    
                                    st.success("✅ 곡이 삭제되었습니다.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"곡 삭제 실패: {str(e)}")
                
        except Exception as e:
            st.error(f"곡 목록 조회 실패: {str(e)}")

st.markdown("---")
st.markdown("### 💡 사용 안내")
st.info("""
**🎯 기능 설명:**
- **전체 공연 삭제**: 공연과 관련된 모든 데이터(곡, AI 설명)를 완전히 삭제
- **곡 삭제**: 특정 곡과 해당 곡의 모든 AI 설명 삭제
- **설명 삭제**: 특정 곡의 특정 AI 설명만 삭제

**⚠️ 주의사항:**
- 모든 삭제 작업은 되돌릴 수 없습니다
- 삭제 전에 신중히 검토해주세요
""")
