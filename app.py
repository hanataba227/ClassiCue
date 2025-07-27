# app.py ─ 메인 라우터 (관리자·사용자 공통)

import streamlit as st
st.set_page_config(page_title="클래식 곡 설명 생성기", layout="wide")

from utils.supabase_client import get_sb_client
from utils.auth            import get_current_user, get_role

sb = get_sb_client()

# ──────────────────────────
# 1) 로그인‧권한 확인
# ──────────────────────────
user = get_current_user()
if not user:
    st.header("🎵 클래식 곡 설명 생성기")
    st.info("로그인이 필요합니다.")
    st.page_link("pages/login.py", label="🔑 로그인")
    st.stop()

role = get_role()

# ──────────────────────────
# 2) 헤더 + 관리자 링크
# ──────────────────────────
st.header("🎵 클래식 곡 설명 생성기")

if role == "admin":
    st.page_link(
        "pages/admin_dashboard.py",
        label="🛠️ 공연 생성 / 편집",
    )

st.divider()

# ──────────────────────────
# 3) 공연 목록 (전체 공개)
# ──────────────────────────
st.subheader("📜 등록된 공연")

concerts = (
    sb.table("concerts")
      .select("id,title,venue,date")
      .order("date", desc=False)
      .execute()
      .data
)

if not concerts:
    st.info("등록된 공연이 없습니다.")
    if role == "admin":
        st.info("상단 버튼으로 새 공연을 추가하세요.")
else:
    for c in concerts:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"**{c['title']}**  \n"
                f"{c['venue']} │ {c['date']}",
                help=f"concert_id: {c['id']}",
            )
        with col2:
            st.page_link(
                "pages/concert_view.py",   # 파라미터 없이 이동 → 내부에서 선택
                label="자세히",
            )
        st.divider()
