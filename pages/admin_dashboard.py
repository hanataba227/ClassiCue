import streamlit as st
import uuid, os
from dotenv import load_dotenv
from utils.supabase_client import get_sb_client
from utils.auth            import require_login
from utils.ai              import (
    generate_classical_description, 
    generate_multiple_descriptions_parallel,
    get_available_prompt_types
)

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

    st.markdown("#### 곡 목록 (한 줄에 '곡명 - 작곡가')")
    tracks_raw = st.text_area("", height=180)

    # AI 설명 생성 방식 선택
    st.markdown("#### AI 설명 생성 옵션")
    
    # 단일 프롬프트 vs 다중 프롬프트 선택
    ai_mode = st.radio(
        "AI 설명 생성 방식",
        ["단일 프롬프트", "다중 프롬프트"],
        horizontal=True
    )
    
    if ai_mode == "단일 프롬프트":
        # 기존 방식: 커스텀 프롬프트 템플릿 사용 (여러 프롬프트 선택 가능하게 개선)
        templates = sb.table("prompt_templates").select("*").execute().data
        tpl_map   = {t["name"]: t for t in templates}
        # 기본 프롬프트도 선택지에 포함
        default_prompt = {
            "name": "기본 설명",
            "template": "곡명: {track_title}\n작곡가: {composer}\n\n클래식 초보도 이해할 수 있도록 200자 내외로 설명해줘."
        }
        all_tpls = [default_prompt] + [t for t in templates if t["name"] != "기본 설명"] if templates else [default_prompt]
        tpl_map = {t["name"]: t for t in all_tpls}
        template_txt = st.selectbox(
            "프롬프트 템플릿 선택",
            list(tpl_map.keys()),
            index=0,
        )
    else:
        # 새로운 방식: 다중 프롬프트 선택
        available_types = get_available_prompt_types()
        selected_prompts = st.multiselect(
            "생성할 설명 타입 선택",
            available_types,
            default=["기본 설명", "작곡가 중심 설명", "시대적 배경 중심 설명", "감상 포인트", "같이 들으면 좋은 곡"],
            help="여러 타입을 선택하면 각각의 설명이 생성됩니다."
        )
        
        # 병렬 처리 옵션
        use_parallel = st.checkbox(
            "병렬 처리 사용 (속도 향상)", 
            value=True,
            help="여러 설명을 동시에 생성하여 처리 시간을 단축합니다."
        )

    submitted = st.form_submit_button("공연 + 곡 저장")

# ② 데이터베이스 저장
if submitted:
    if not title or not venue or not tracks_raw.strip():
        st.warning("필수 항목을 모두 입력하세요.")
        st.stop()
    
    if ai_mode == "다중 프롬프트" and not selected_prompts:
        st.warning("최소 1개의 설명 타입을 선택해주세요.")
        st.stop()

    cid = str(uuid.uuid4())

    # concerts INSERT
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

    # AI 설명 생성 및 데이터베이스 저장
    track_rows = []
    description_rows = []
    
    with st.spinner("AI 설명 생성 중…"):
        for track_title, composer in parse_tracks(tracks_raw):
            # 곡 정보 먼저 저장
            track_id = str(uuid.uuid4())
            track_rows.append({
                "id": track_id,
                "concert_id": cid,
                "track_title": track_title,
                "composer": composer,
            })
            
            if ai_mode == "단일 프롬프트":
                # 선택된 프롬프트로 AI 설명 생성
                tpl_body = tpl_map.get(template_txt, {}).get(
                    "template",
                    "곡명: {track_title}\n작곡가: {composer}\n\n클래식 초보도 이해할 수 있도록 200자 내외로 설명해줘."
                )
                ai_desc = generate_classical_description(
                    tpl_body, track_title, composer
                )
                description_rows.append({
                    "track_id": track_id,
                    "prompt_type": template_txt,
                    "description": ai_desc,
                })
                
            else:
                # 새로운 방식: 다중 AI 설명
                if use_parallel:
                    ai_descriptions = generate_multiple_descriptions_parallel(
                        selected_prompts, track_title, composer
                    )
                else:
                    from utils.ai import generate_multiple_descriptions
                    ai_descriptions = generate_multiple_descriptions(
                        selected_prompts, track_title, composer
                    )
                
                # 각 설명 타입별로 별도 레코드 생성
                for prompt_type, desc_content in ai_descriptions.items():
                    description_rows.append({
                        "track_id": track_id,
                        "prompt_type": prompt_type,
                        "description": desc_content,
                    })

    # 데이터베이스에 저장
    if track_rows:
        # 곡 정보 저장
        sb.table("concert_tracks").insert(track_rows).execute()
        
        # AI 설명 저장 (새로운 테이블 구조 필요)
        sb.table("track_descriptions").insert(description_rows).execute()

    if ai_mode == "단일 프롬프트":
        st.success(f"✅ 저장 완료! (총 {len(track_rows)}곡, 각 1개 설명)")
    else:
        total_descriptions = len(description_rows)
        st.success(f"✅ 저장 완료! (총 {len(track_rows)}곡, {total_descriptions}개 설명)")
        
        # 생성된 설명 타입별 개수 표시
        type_counts = {}
        for row in description_rows:
            prompt_type = row["prompt_type"]
            type_counts[prompt_type] = type_counts.get(prompt_type, 0) + 1
        
        st.info("생성된 설명 타입별 개수: " + 
                ", ".join([f"{k}: {v}개" for k, v in type_counts.items()]))

# ───────────────────────────────
# ③ 추가: 기존 공연 목록 및 설명 미리보기
st.divider()
st.subheader("📋 기존 공연 목록")

concerts = (
    sb.table("concerts")
      .select("id,title,venue,date")
      .order("date", desc=True)
      .limit(10)
      .execute()
      .data
)

if concerts:
    for concert in concerts:
        with st.expander(f"🎵 {concert['title']} ({concert['date']})"):
            st.write(f"**공연장:** {concert['venue']}")
            
            # 해당 공연의 곡 및 설명 개수 조회
            track_count = (
                sb.table("concert_tracks")
                  .select("id", count="exact")
                  .eq("concert_id", concert["id"])
                  .execute()
                  .count
            )
            
            # 설명 개수 조회 (새로운 테이블 구조 기준)
            try:
                desc_count = (
                    sb.table("track_descriptions")
                      .select("id", count="exact")
                      .in_("track_id", 
                           [t["id"] for t in sb.table("concert_tracks")
                                                 .select("id")
                                                 .eq("concert_id", concert["id"])
                                                 .execute().data])
                      .execute()
                      .count
                )
                st.write(f"**곡 수:** {track_count}곡, **AI 설명:** {desc_count}개")
            except:
                st.write(f"**곡 수:** {track_count}곡")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"상세보기", key=f"view_{concert['id']}"):
                    st.query_params["concert_id"] = concert["id"]
                    st.switch_page("pages/concert_view.py")
            with col2:
                if st.button(f"수정", key=f"edit_{concert['id']}"):
                    st.info("수정 기능은 향후 구현 예정입니다.")
else:
    st.info("등록된 공연이 없습니다.")