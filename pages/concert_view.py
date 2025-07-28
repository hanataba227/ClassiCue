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
    if concert.get("description"):
        st.write(concert["description"])
    st.divider()

    # 설명 표시 방식 선택
    display_mode = st.radio(
        "설명 표시 방식",
        ["탭으로 구분", "전체 표시", "타입별 필터"],
        horizontal=True
    )

    for i, track in enumerate(tracks):
        st.subheader(f"🎵 {track['track_title']}")
        st.caption(f"작곡가: {track['composer']}")
        
        # 해당 곡의 모든 설명 조회
        try:
            descriptions = (
                sb.table("track_descriptions")
                  .select("*")
                  .eq("track_id", track["id"])
                  .execute()
                  .data
            )
        except:
            # 기존 데이터베이스 구조 호환성 (ai_description 컬럼)
            descriptions = []
            if track.get("ai_description"):
                descriptions = [{
                    "prompt_type": "기본 설명",
                    "description": track["ai_description"]
                }]
        
        if not descriptions:
            st.info("해당 곡에 대한 AI 설명이 없습니다.")
            st.divider()
            continue
        
        # 설명 표시 방식에 따른 렌더링
        if display_mode == "탭으로 구분" and len(descriptions) > 1:
            # 탭 방식으로 표시
            tab_names = [desc["prompt_type"] for desc in descriptions]
            tabs = st.tabs(tab_names)
            
            for tab, desc in zip(tabs, descriptions):
                with tab:
                    st.write(desc["description"])
                    
        elif display_mode == "타입별 필터" and len(descriptions) > 1:
            # 필터링 방식
            available_types = list(set(desc["prompt_type"] for desc in descriptions))
            selected_type = st.selectbox(
                f"설명 타입 선택 - {track['track_title']}",
                available_types,
                key=f"filter_{track['id']}"
            )
            
            selected_desc = next(
                desc for desc in descriptions 
                if desc["prompt_type"] == selected_type
            )
            st.write(selected_desc["description"])
            
        else:
            # 전체 표시 방식 (기본)
            for desc in descriptions:
                if len(descriptions) > 1:
                    st.markdown(f"**{desc['prompt_type']}**")
                st.write(desc["description"])
                if len(descriptions) > 1:
                    st.markdown("---")
        
        st.divider()

def render_concert_list():
    """공연 목록을 보여주고 선택할 수 있게 한다."""
    st.header("🎭 공연 선택")
    
    # 검색 기능 추가
    search_term = st.text_input("🔍 공연 검색", placeholder="공연명, 공연장명으로 검색...")
    
    # 공연 목록 조회
    query = sb.table("concerts").select("id,title,venue,date").order("date", desc=True)

    if search_term:
        # Supabase-py에는 or_가 없으므로, 두 조건을 각각 ilike로 필터링 후 합침
        title_matches = query.clone().ilike("title", f"%{search_term}%").execute().data
        venue_matches = query.clone().ilike("venue", f"%{search_term}%").execute().data
        # id로 중복 제거
        seen_ids = set()
        concerts = []
        for c in (title_matches or []) + (venue_matches or []):
            if c["id"] not in seen_ids:
                concerts.append(c)
                seen_ids.add(c["id"])
    else:
        concerts = query.execute().data
    
    if not concerts:
        if search_term:
            st.info(f"'{search_term}'에 대한 검색 결과가 없습니다.")
        else:
            st.info("등록된 공연이 없습니다.")
        return

    # 공연 목록을 카드 형태로 표시
    cols = st.columns(2)
    for idx, concert in enumerate(concerts):
        col = cols[idx % 2]
        
        with col:
            with st.container():
                st.markdown(f"### 🎵 {concert['title']}")
                st.write(f"**🏛️ 공연장:** {concert['venue']}")
                st.write(f"**📅 날짜:** {concert['date']}")
                
                # 곡 수 정보 표시
                try:
                    track_count = (
                        sb.table("concert_tracks")
                          .select("id", count="exact")
                          .eq("concert_id", concert["id"])
                          .execute()
                          .count
                    )
                    st.write(f"**🎼 곡 수:** {track_count}곡")
                except:
                    pass
                
                if st.button(
                    "상세 보기 →", 
                    key=f"select_{concert['id']}",
                    use_container_width=True
                ):
                    st.query_params["concert_id"] = concert["id"]
                    st.rerun()
                
                st.markdown("---")

# ────────────────────────────────
# 메인 로직: 파라미터에 따른 페이지 렌더링
# ────────────────────────────────
if not cid:
    render_concert_list()
else:
    # 뒤로 가기 버튼
    if st.button("← 공연 목록으로"):
        del st.query_params["concert_id"]
        st.rerun()
    
    st.markdown("---")
    
    try:
        render_detail(cid)
    except Exception as e:
        st.error(f"공연 정보를 불러오는 중 오류가 발생했습니다: {str(e)}")
        st.info("공연 목록으로 돌아가서 다시 시도해주세요.")
        
        if st.button("공연 목록으로 돌아가기"):
            del st.query_params["concert_id"]
            st.rerun()