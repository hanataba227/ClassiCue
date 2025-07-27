import streamlit as st
import uuid, os
from dotenv import load_dotenv
from utils.supabase_client import get_sb_client
from utils.auth            import require_login
from utils.ai              import generate_classical_description

load_dotenv()
sb   = get_sb_client(use_service=True)
user = require_login(role="admin")

st.header("🎫 공연 페이지 관리")

# ───────────────────────────────
# ① 공연 + 곡 입력 폼
with st.form("concert_form", clear_on_submit=True):
    st.subheader("새 공연 생성")

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("공연명")
        venue = st.text_input("공연장")
        date  = st.date_input("공연 일자")

    description = st.text_area("공연 설명")

    st.markdown("#### 곡 목록 (한 줄에 ‘곡명 - 작곡가’)")
    tracks_raw = st.text_area("", height=180)

    # 프롬프트 템플릿 선택 (옵션)
    templates = sb.table("prompt_templates").select("*").execute().data
    tpl_map   = {t["name"]: t for t in templates}
    template_txt = st.selectbox(
        "AI 설명 프롬프트 선택",
        list(tpl_map.keys()) if tpl_map else ["기본 프롬프트"],
        index=0,
    )
    submitted = st.form_submit_button("공연 + 곡 저장")

# ② 데이터베이스 저장
if submitted:
    if not title or not venue or not tracks_raw.strip():
        st.warning("필수 항목을 모두 입력하세요.")
        st.stop()

    cid = str(uuid.uuid4())

    # concerts INSERT (qr_url 제거)
    sb.table("concerts").insert({
        "id": cid,
        "title": title,
        "venue": venue,
        "date": str(date),
        "description": description,
        "created_by": user.id,
    }).execute()

    # 곡 + AI 설명
    def parse_tracks(raw):
        for line in raw.splitlines():
            if "-" in line:
                name, composer = [x.strip() for x in line.split("-", 1)]
                if name:
                    yield name, composer

    tpl_body = tpl_map.get(template_txt, {}).get(
        "template",
        "곡명: {track_title}\n작곡가: {composer}\n\n"
        "클래식 초보도 이해할 수 있도록 200자 내외로 설명해줘."
    )

    rows = []
    with st.spinner("AI 설명 생성 중…"):
        for track_title, composer in parse_tracks(tracks_raw):
            ai_desc = generate_classical_description(
                tpl_body, track_title, composer
            )
            rows.append({
                "concert_id": cid,
                "track_title": track_title,
                "composer": composer,
                "ai_description": ai_desc,
            })

    if rows:
        sb.table("concert_tracks").insert(rows).execute()

    st.success(f"✅ 저장 완료!  (총 {len(rows)}곡)")
