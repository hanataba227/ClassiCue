import streamlit as st
st.set_page_config(page_title="공연 상세", layout="wide")

from utils.supabase_client import get_sb_client
sb = get_sb_client()

cid = st.query_params.get("concert_id")  # None or uuid

def render_detail(concert_id: str):
    """선택된 공연의 AI 곡 설명을 보여준다."""
    concert = (
        sb.table("concerts")
          .select("*")
          .eq("id", concert_id)
          .single()
          .execute()
          .data
    )
    tracks = (
        sb.table("concert_tracks")
          .select("*")
          .eq("concert_id", concert_id)
          .execute()
          .data
    )

    st.title(concert["title"])
    st.caption(f'{concert["venue"]} │ {concert["date"]}')
    st.write(concert["description"])
    st.divider()

    for t in tracks:
        st.subheader(t["track_title"])
        st.caption(t["composer"])
        st.write(t["ai_description"])
        st.divider()

# ────────────────────────────────
# 파라미터가 없으면 목록 → 선택
# ────────────────────────────────
if not cid:
    st.header("공연 선택")
    concerts = (
        sb.table("concerts")
          .select("id,title,venue,date")
          .order("date", desc=False)
          .execute()
          .data
    )
    if not concerts:
        st.info("등록된 공연이 없습니다.")
        st.stop()

    options = {f"{c['title']} ({c['date']})": c["id"] for c in concerts}
    choice = st.selectbox("공연을 선택하세요", list(options.keys()))
    if st.button("상세 보기"):
        st.query_params["concert_id"] = options[choice]
        st.rerun()
else:
    render_detail(cid)
