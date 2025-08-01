# 프롬프트 관리 페이지
import streamlit as st
from utils.supabase_client import get_sb_client
from utils.auth import require_login, sign_out

st.set_page_config(page_title="프롬프트 관리", layout="wide")

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
        <h1>프롬프트 관리</h1>
        <p>AI 설명 생성을 위한 프롬프트 템플릿을 관리하세요</p>
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
    if st.button("🎫 공연 등록"):
        st.switch_page("pages/admin_dashboard.py")
with col4:
    if st.button("🗑️ 공연 관리"):
        st.switch_page("pages/admin_manage.py")
with col5:
    st.markdown("**📍 현재: 프롬프트 관리**")

st.divider()

# 현재 저장된 프롬프트 조회 및 편집
@st.cache_data(ttl=60)
def get_current_templates():
    try:
        templates = sb.table("prompt_templates").select("*").execute().data
        return templates
    except Exception as e:
        st.error(f"프롬프트 조회 실패: {str(e)}")
        return []

# 기본 템플릿 정의 (DB에 아무것도 없을 경우)
default_templates = {
    "감상 가이드": """곡명: {track_title}
작곡가: {composer}

### 🎵 감상 가이드

이 곡을 처음 듣는 분들을 위한 감상 포인트를 안내해드립니다:

**들어보세요:**
- 곡의 시작부터 끝까지의 감정 변화와 흐름
- 주요 멜로디가 어떻게 반복되고 변화하는지
- 악기들 간의 대화와 조화

**느껴보세요:**
- 이 곡이 표현하고자 하는 감정과 분위기
- 작곡가가 음악으로 그려낸 이야기나 풍경
- 클래식 음악만이 가진 깊이와 아름다움

200자 내외로 초보자도 쉽게 이해할 수 있도록 따뜻하고 친근한 톤으로 작성해주세요.""",

    "기본 설명": """곡명: {track_title}
작곡가: {composer}

### 📖 기본 설명

이 곡에 대한 기본 정보를 알려드립니다:

**기본 정보:**
- 곡의 형식과 구조 (소나타, 교향곡, 협주곡 등)
- 작곡 연도와 시대적 배경
- 연주 편성 (독주, 실내악, 관현악 등)

**특징:**
- 이 곡만의 독특한 특색과 매력
- 클래식 음악사에서의 의미와 위치
- 현재까지도 사랑받는 이유

클래식 초보자가 이해하기 쉽도록 전문 용어는 쉽게 풀어서 200자 내외로 설명해주세요.""",

    "음악적 특징": """곡명: {track_title}
작곡가: {composer}

### 🎼 음악적 특징

이 곡의 음악적 요소와 기법을 분석해드립니다:

**음악적 구조:**
- 조성, 박자, 템포의 특징
- 주요 주제와 모티프의 전개 방식
- 형식적 구조와 악장 구성

**연주 기법:**
- 특별한 연주 기법이나 표현법
- 악기별 역할과 상호작용
- 기술적 난이도와 표현의 포인트

**혁신적 요소:**
- 당시로서는 새로웠던 음악적 시도
- 후대에 미친 영향과 의미

음악 전공자나 애호가들도 흥미롭게 읽을 수 있도록 전문적이지만 이해하기 쉽게 200자 내외로 작성해주세요.""",

    "역사적 배경": """곡명: {track_title}
작곡가: {composer}

### 🏛️ 역사적 배경

이 곡이 탄생한 시대적 배경과 문화적 맥락을 알아봅니다:

**시대적 배경:**
- 작곡 당시의 사회적, 정치적 상황
- 해당 시대의 음악 경향과 유행
- 작곡가가 처한 개인적 상황과 환경

**문화적 의미:**
- 당시 사회에서 이 곡이 갖는 의미
- 초연 당시의 반응과 평가
- 시대를 넘나드는 보편적 가치

**영향과 의의:**
- 음악사에서의 위치와 중요성
- 후대 작곡가들에게 미친 영향
- 오늘날까지 이어지는 의미

역사적 맥락을 통해 곡을 더 깊이 이해할 수 있도록 200자 내외로 설명해주세요.""",

    "작곡가 설명": """곡명: {track_title}
작곡가: {composer}

### 👨‍🎼 작곡가 설명

{composer}에 대해 알아보고, 이 곡과의 연관성을 살펴봅니다:

**작곡가 소개:**
- 생애와 주요 경력, 음악적 여정
- 대표작품과 음악적 스타일의 특징
- 개성적인 작곡 기법과 표현 방식

**이 곡과의 관계:**
- 작곡가 생애에서 이 곡이 갖는 의미
- 작곡 당시의 개인적 상황과 영감의 원천
- 작곡가의 다른 작품들과의 비교

**음악적 유산:**
- 클래식 음악사에서의 위치
- 후대에 미친 영향과 의미
- 현재까지도 사랑받는 이유

작곡가의 인간적 면모와 음악적 천재성을 모두 느낄 수 있도록 200자 내외로 친근하게 설명해주세요."""
}

# 현재 템플릿 가져오기
current_templates = get_current_templates()

# DB에서 가져온 템플릿을 딕셔너리로 변환
if current_templates:
    templates_dict = {template['name']: template['template'] for template in current_templates}
    template_ids = {template['name']: template['id'] for template in current_templates}
else:
    # DB가 비어있으면 기본 템플릿 사용
    templates_dict = default_templates.copy()
    template_ids = {}

st.subheader("프롬프트 템플릿 편집")

# 탭으로 각 템플릿을 분리하여 편집
tab_names = list(templates_dict.keys())
tabs = st.tabs([f"📝 {name}" for name in tab_names])

edited_templates = {}

for i, (name, tab) in enumerate(zip(tab_names, tabs)):
    with tab:
        st.markdown(f"### {name}")
        
        # 현재 템플릿 내용을 텍스트 에리어로 편집
        edited_content = st.text_area(
            f"{name} 템플릿 내용",
            value=templates_dict[name],
            height=400,
            key=f"template_{i}",
            help=f"{name} 템플릿의 내용을 수정하세요"
        )
        
        edited_templates[name] = edited_content
        
        # 미리보기
        with st.expander("📋 편집된 내용 미리보기"):
            st.code(edited_content, language="text")

st.divider()

# 저장 버튼
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("🔄 기본 템플릿으로 초기화", type="secondary"):
        st.session_state.reset_templates = True
        st.rerun()

with col2:
    if st.button("💾 템플릿 저장", type="primary"):
        try:
            # 기존 템플릿들을 개별적으로 삭제
            existing_templates = sb.table("prompt_templates").select("id").execute().data
            for template in existing_templates:
                sb.table("prompt_templates").delete().eq("id", template["id"]).execute()
            
            # 새로운 템플릿 삽입
            template_data = []
            for name, template in edited_templates.items():
                template_data.append({
                    "name": name,
                    "template": template
                })
            
            sb.table("prompt_templates").insert(template_data).execute()
            
            st.success("✅ 프롬프트 템플릿이 성공적으로 저장되었습니다!")
            st.cache_data.clear()
            st.rerun()
            
        except Exception as e:
            st.error(f"저장 실패: {str(e)}")

with col3:
    if st.button("🔍 현재 DB 템플릿 새로고침"):
        st.cache_data.clear()
        st.rerun()

# 초기화 처리
if st.session_state.get('reset_templates', False):
    try:
        # 기존 템플릿들을 개별적으로 삭제
        existing_templates = sb.table("prompt_templates").select("id").execute().data
        for template in existing_templates:
            sb.table("prompt_templates").delete().eq("id", template["id"]).execute()
        
        # 기본 템플릿 삽입
        template_data = []
        for name, template in default_templates.items():
            template_data.append({
                "name": name,
                "template": template
            })
        
        sb.table("prompt_templates").insert(template_data).execute()
        
        st.success("✅ 기본 템플릿으로 초기화되었습니다!")
        st.session_state.reset_templates = False
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"초기화 실패: {str(e)}")
        st.session_state.reset_templates = False

st.markdown("---")
st.markdown("### 💡 사용 안내")
st.info("""
**🎯 기능 설명:**
- **📝 템플릿 편집**: 각 탭에서 프롬프트 템플릿을 직접 수정할 수 있습니다
- **💾 템플릿 저장**: 편집한 내용을 데이터베이스에 저장합니다
- **🔄 기본 템플릿으로 초기화**: 모든 템플릿을 기본값으로 되돌립니다
- **🔍 새로고침**: 데이터베이스에서 최신 템플릿을 다시 불러옵니다

**🔧 템플릿 변수:**
- `{track_title}`: 곡명으로 자동 치환됩니다
- `{composer}`: 작곡가명으로 자동 치환됩니다

**💡 팁:**
- 각 템플릿은 200자 내외의 설명을 생성하도록 설계되었습니다
- 편집 중 미리보기를 통해 변경사항을 확인할 수 있습니다
- 저장하기 전에 모든 탭의 내용을 확인해주세요
""")
