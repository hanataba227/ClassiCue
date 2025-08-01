import streamlit as st
import uuid, os
import logging
from dotenv import load_dotenv
from utils.supabase_client import get_sb_client
from utils.auth import require_login, sign_out
from utils.ai import generate_classical_description, validate_api_key

st.set_page_config(page_title="공연 등록", layout="wide")

# CSS 스타일 로드
try:
    with open("static/classical_styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
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
        <h1>🎫 공연 등록</h1>
        <p>새로운 클래식 공연과 곡 정보를 등록하고 AI 설명을 생성하세요</p>
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
    if st.button("🗑️ 공연 관리"):
        st.switch_page("pages/admin_manage.py")
with col4:
    if st.button("🔧 프롬프트 관리"):
        st.switch_page("pages/prompt_manager.py")
with col5:
    st.markdown("**📍 현재: 공연 등록**")

st.divider()

# 곡 목록 관리 (폼 외부)
st.markdown("### 🎵 곡 목록 관리")

# 세션 상태에 곡 목록 초기화
if "tracks" not in st.session_state:
    st.session_state.tracks = [{"title": "", "composer": ""}]

# 곡 추가/제거 버튼
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    if st.button("➕ 곡 추가"):
        st.session_state.tracks.append({"title": "", "composer": ""})
        st.rerun()

with col2:
    if len(st.session_state.tracks) > 1:
        if st.button("🗑️ 모든 곡 초기화"):
            st.session_state.tracks = [{"title": "", "composer": ""}]
            st.rerun()

# 곡 입력 폼들 (폼 외부)
for i, track in enumerate(st.session_state.tracks):
    col1, col2, col3 = st.columns([3, 3, 1])
    
    with col1:
        track_title = st.text_input(
            f"곡명 {i+1}", 
            value=track["title"],
            key=f"track_title_{i}",
            placeholder="곡 제목을 입력하세요"
        )
        st.session_state.tracks[i]["title"] = track_title
    
    with col2:
        composer = st.text_input(
            f"작곡가 {i+1}", 
            value=track["composer"],
            key=f"composer_{i}",
            placeholder="작곡가 이름을 입력하세요"
        )
        st.session_state.tracks[i]["composer"] = composer
    
    with col3:
        if len(st.session_state.tracks) > 1:
            if st.button("❌", key=f"remove_{i}", help="이 곡 삭제"):
                st.session_state.tracks.pop(i)
                st.rerun()

st.divider()

# ───────────────────────────────
# ① 공연 + 곡 입력 폼
with st.form("concert_form", clear_on_submit=True):
    st.subheader("새 공연 생성")

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("공연명")
        venue = st.text_input("공연장")
        
        # 날짜 범위 선택
        st.markdown("**공연 기간**")
        date_type = st.radio(
            "날짜 선택 방식",
            ["단일 날짜", "기간 선택"],
            horizontal=True
        )
        
        if date_type == "단일 날짜":
            start_date = st.date_input("공연 일자")
            end_date = None
        else:
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("시작 날짜")
            with col_end:
                end_date = st.date_input("종료 날짜")
            
            # 날짜 검증
            if end_date and start_date > end_date:
                st.error("⚠️ 시작 날짜가 종료 날짜보다 늦을 수 없습니다.")

    with col2:
        description = st.text_area("공연 설명")

    # 프롬프트 템플릿 선택 - 다중 선택 방식
    st.markdown("#### 🤖 AI 설명 템플릿 선택")
    
    try:
        templates = sb.table("prompt_templates").select("*").execute().data
        tpl_map = {t["name"]: t for t in templates}
        
        # Session state에 template map 저장
        st.session_state['tpl_map'] = tpl_map
        
        if not tpl_map:
            st.warning("⚠️ 사용 가능한 프롬프트 템플릿이 없습니다.")
            st.info("시스템 관리자에게 문의하거나 데이터베이스를 확인해주세요.")
            st.stop()
        
        # 모든 템플릿을 다중 선택으로 제공
        selected_templates = st.multiselect(
            "생성할 AI 설명 타입들을 선택하세요 (1개 이상 필수)",
            list(tpl_map.keys()),
            default=[list(tpl_map.keys())[0]],  # 첫 번째 템플릿을 기본 선택
            help="여러 개의 설명 타입을 선택하면 각 곡마다 선택한 모든 타입의 설명이 생성됩니다."
        )
        
        # Session state에 템플릿 선택 상태 저장
        st.session_state['selected_templates'] = selected_templates
        
        # 템플릿 선택 상태에 따른 경고 표시
        submit_enabled = len(selected_templates) > 0
        if not submit_enabled:
            st.error("⚠️ 최소 1개의 템플릿을 선택해야 저장할 수 있습니다.")
            
        # 선택된 템플릿들 미리보기
        if selected_templates:
            with st.expander("📝 선택된 템플릿 미리보기"):
                for template_name in selected_templates:
                    template_data = tpl_map[template_name]
                    st.markdown(f"**{template_name}**")
                    st.code(template_data.get("template", "템플릿 내용 없음"), language="text")
                    st.divider()
        
    except Exception as e:
        st.error(f"템플릿 로드 실패: {str(e)}")
        st.stop()
    
    # 현재 입력된 곡 목록 표시 (읽기 전용)
    st.markdown("#### 📋 현재 입력된 곡 목록")
    if st.session_state.tracks:
        valid_tracks_display = []
        for i, track in enumerate(st.session_state.tracks):
            if track["title"].strip() and track["composer"].strip():
                valid_tracks_display.append(f"{i+1}. **{track['title']}** - {track['composer']}")
        
        if valid_tracks_display:
            for track_display in valid_tracks_display:
                st.markdown(track_display)
        else:
            st.info("유효한 곡이 없습니다. 위에서 곡 정보를 입력해주세요.")
    else:
        st.info("곡이 없습니다. 위에서 곡을 추가해주세요.")
    
    submitted = st.form_submit_button(
        "🎼 공연 + 곡 저장",
        disabled=(not st.session_state.get('valid_tracks', False) or 
                 len(st.session_state.get('selected_templates', [])) == 0)
    )

# ② 데이터베이스 저장
if submitted:
    # 입력 검증
    if not title or not venue:
        st.warning("공연명과 공연장을 모두 입력하세요.")
        st.stop()
    
    # 곡 목록 검증
    valid_tracks = []
    for track in st.session_state.tracks:
        if track["title"].strip() and track["composer"].strip():
            valid_tracks.append(track)
    
    if not valid_tracks:
        st.warning("최소 1개의 곡 정보(곡명, 작곡가)를 입력하세요.")
        st.stop()
    
    if not selected_templates:
        st.warning("최소 1개의 AI 설명 템플릿을 선택하세요.")
        st.stop()

    cid = str(uuid.uuid4())

    # 날짜 문자열 생성
    if end_date:
        date_str = f"{start_date} ~ {end_date}"
    else:
        date_str = str(start_date)

    # concerts INSERT
    sb.table("concerts").insert({
        "id": cid,
        "title": title,
        "venue": venue,
        "date": date_str,
        "description": description,
        "created_by": user.id,
    }).execute()

    # 기본 템플릿 내용
    default_template = (
        "곡명: {track_title}\n작곡가: {composer}\n\n"
        "클래식 초보도 이해할 수 있도록 200자 내외로 설명해줘."
    )
    
    # 선택된 템플릿들 준비 - session state에서 가져오기
    selected_templates = st.session_state.get('selected_templates', [])
    tpl_map = st.session_state.get('tpl_map', {})
    all_templates = []
    for template_name in selected_templates:
        template_data = tpl_map.get(template_name, {})
        template_body = template_data.get("template", default_template)
        all_templates.append((template_name, template_body))

    # 곡 데이터 먼저 저장
    track_rows = []
    for track in valid_tracks:
        track_id = str(uuid.uuid4())
        track_rows.append({
            "id": track_id,
            "concert_id": cid,
            "track_title": track["title"].strip(),
            "composer": track["composer"].strip(),
        })

    if track_rows:
        sb.table("concert_tracks").insert(track_rows).execute()
        
        # AI 설명 생성 및 저장
        description_rows = []
        total_descriptions = len(track_rows) * len(all_templates)
        
        st.markdown("### 🤖 AI 설명 생성 진행 상황")
        st.info(f"총 {total_descriptions}개의 설명을 생성합니다. 잠시만 기다려주세요...")
        
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            current_progress = 0
            
            for track_idx, track_data in enumerate(track_rows):
                for template_idx, (template_name, template_body) in enumerate(all_templates):
                    status_text.text(f"🎵 {track_data['track_title']} - {template_name} 생성 중...")
                    
                    try:
                        ai_desc = generate_classical_description(
                            template_body, 
                            track_data["track_title"], 
                            track_data["composer"]
                        )
                        
                        description_rows.append({
                            "track_id": track_data["id"],
                            "prompt_type": template_name,
                            "description": ai_desc,
                        })
                        
                        current_progress += 1
                        progress_percentage = current_progress / total_descriptions
                        progress_bar.progress(progress_percentage)
                        
                        # 성공 메시지를 잠깐 표시
                        status_text.success(f"✅ {track_data['track_title']} - {template_name} 완료!")
                        
                    except Exception as e:
                        error_msg = f"❌ '{track_data['track_title']}' - '{template_name}' 생성 실패: {str(e)}"
                        st.warning(error_msg)
                        logger.error(error_msg)
                        
                        # 실패한 경우 기본 설명 추가
                        description_rows.append({
                            "track_id": track_data["id"],
                            "prompt_type": template_name,
                            "description": f"'{track_data['track_title']}' by {track_data['composer']} - AI 설명 생성에 실패했습니다. 나중에 다시 생성하거나 수동으로 편집해주세요.",
                        })
                        
                        current_progress += 1
                        progress_percentage = current_progress / total_descriptions
                        progress_bar.progress(progress_percentage)
            
            # 완료 메시지
            status_text.success(f"🎉 모든 AI 설명 생성이 완료되었습니다! ({len(description_rows)}개)")
            progress_bar.progress(1.0)
        
        # 설명 데이터 일괄 저장
        if description_rows:
            try:
                sb.table("track_descriptions").insert(description_rows).execute()
                st.success(
                    f"✅ 저장 완료!\n"
                    f"- 곡: {len(track_rows)}개\n"
                    f"- 설명: {len(description_rows)}개 ({len(all_templates)}가지 타입)"
                )
                
                # 성공 후 곡 목록 초기화
                st.session_state.tracks = [{"title": "", "composer": ""}]
                
                # 메인 페이지로 이동 옵션 제공
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("🏠 메인 페이지로 이동"):
                        st.switch_page("app.py")
                with col2:
                    if st.button("👀 공연 보기"):
                        st.switch_page("pages/concert_view.py")
                with col3:
                    if st.button("🔄 새 공연 등록"):
                        st.rerun()
                
            except Exception as e:
                st.error(f"설명 저장 중 오류: {str(e)}")
                # 곡 데이터는 저장되었으므로 롤백하지 않음
                st.info("곡 정보는 저장되었습니다. 설명은 나중에 다시 생성할 수 있습니다.")
    else:
        st.warning("저장할 곡이 없습니다.")