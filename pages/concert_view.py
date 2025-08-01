import streamlit as st
import logging
from utils.supabase_client import get_sb_client
from utils.auth import get_current_user, get_role, sign_out

st.set_page_config(page_title="공연 상세", layout="wide")

# CSS 스타일 로드
try:
    with open("static/classical_styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sb = get_sb_client()

# 로그인 상태 확인
user = get_current_user()
if not user:
    st.warning("🔑 로그인이 필요합니다.")
    st.info("메인 페이지로 이동하여 로그인해주세요.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏠 메인 페이지로 이동"):
            st.switch_page("app.py")
    st.stop()

role = get_role()

# 상단 헤더 및 네비게이션
st.markdown(
    """
    <div class="classical-header">
        <h1>🎵 공연 보기</h1>
        <p>클래식 공연과 AI가 생성한 곡 설명을 확인하세요</p>
    </div>
    """,
    unsafe_allow_html=True
)

# 네비게이션 버튼
if role == "admin":
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        if st.button("🏠 메인 페이지"):
            st.switch_page("app.py")
    with col2:
        if st.button("➕ 공연 등록"):
            st.switch_page("pages/admin_dashboard.py")
    with col3:
        if st.button("🗑️ 공연 관리"):
            st.switch_page("pages/admin_manage.py")
    with col4:
        if st.button("🔧 프롬프트 관리"):
            st.switch_page("pages/prompt_manager.py")
    with col5:
        st.markdown("**📍 현재: 공연 보기**")
else:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🏠 메인 페이지"):
            st.switch_page("app.py")
    with col2:
        st.markdown("**📍 현재: 공연 보기**")

st.divider()

cid = st.query_params.get("concert_id")  # None or uuid

def render_detail(concert_id: str):
    """선택된 공연의 AI 곡 설명을 보여준다."""
    if not concert_id:
        st.error("유효하지 않은 공연 ID입니다.")
        return
    
    try:
        concert = (
            sb.table("concerts")
              .select("*")
              .eq("id", concert_id)
              .single()
              .execute()
              .data
        )
    except Exception as e:
        st.error(f"공연 정보를 불러올 수 없습니다: {str(e)}")
        return
    
    try:
        tracks = (
            sb.table("concert_tracks")
              .select("*")
              .eq("concert_id", concert_id)
              .execute()
              .data
        )
    except Exception as e:
        st.error(f"곡 목록을 불러올 수 없습니다: {str(e)}")
        return

    st.markdown(
        f"""
        <div class="classical-header">
            <h1>🎭 {concert["title"]}</h1>
            <p>{concert["venue"]} │ {concert["date"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if concert.get("description"):
        st.markdown(
            f"""
            <div class="info-box info-box-purple">
                <h4>📖 공연 소개</h4>
                <p>{concert["description"]}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.divider()
    
    # 곡이 없는 경우 안내
    if not tracks:
        st.markdown(
            """
            <div class="info-box info-box-gold">
                <h3>🎵 곡 목록 준비 중</h3>
                <p>이 공연의 곡 목록과 AI 해설이 곧 추가될 예정입니다.</p>
                <p>조금만 기다려주시면 더 풍성한 정보를 제공해드리겠습니다!</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # 설명 표시 방식 선택을 더 보기 좋게
    st.markdown(
        """
        <div class="selection-container">
            <h4 class="selection-title">🎚️ 설명 표시 방식 선택</h4>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    display_mode = st.radio(
        "",  # 라벨은 위에서 처리
        ["탭으로 구분", "전체 표시", "타입별 필터"],
        horizontal=True,
        help="곡 설명을 어떤 방식으로 볼지 선택하세요"
    )

    st.markdown("---")

    for i, track in enumerate(tracks):
        # 곡 번호와 함께 표시
        st.markdown(
            f"""
            <div class="track-card">
                <div class="track-title">🎵 {i+1}. {track['track_title']}</div>
                <div class="track-composer">작곡가: {track['composer']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 해당 곡의 모든 설명 조회
        try:
            descriptions = (
                sb.table("track_descriptions")
                  .select("*")
                  .eq("track_id", track["id"])
                  .execute()
                  .data
            )
        except Exception as e:
            logger.error(f"곡 설명 조회 오류 - {track['track_title']}: {str(e)}")
            descriptions = []
        
        if not descriptions:
            st.markdown(
                """
                <div class="info-box info-box-pink">
                    <h4>💭 AI 설명 준비 중</h4>
                    <p>이 곡에 대한 AI 해설을 준비하고 있습니다. 곧 업데이트될 예정입니다!</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.divider()
            continue
        
        # 설명 표시 방식에 따른 렌더링
        if display_mode == "탭으로 구분" and len(descriptions) > 1:
            # 탭 방식으로 표시
            tab_names = [f"{desc['prompt_type']}" for desc in descriptions]
            tabs = st.tabs(tab_names)
            
            for tab, desc in zip(tabs, descriptions):
                with tab:
                    st.markdown(
                        f"""
                        <div class="track-description">
                            {desc['description']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
        elif display_mode == "타입별 필터" and len(descriptions) > 1:
            # 필터링 방식
            available_types = list(set(desc["prompt_type"] for desc in descriptions))
            selected_type = st.selectbox(
                f"💡 설명 타입 선택",
                available_types,
                key=f"filter_{track['id']}",
                help="보고 싶은 설명 타입을 선택하세요"
            )
            
            selected_desc = next(
                desc for desc in descriptions 
                if desc["prompt_type"] == selected_type
            )
            
            st.markdown(
                f"""
                <div class="info-box info-box-blue">
                    <h4>📝 {selected_type}</h4>
                    <div class="track-description">
                        {selected_desc['description']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        else:
            # 전체 표시 방식 (기본)
            for desc in descriptions:
                if len(descriptions) > 1:
                    st.markdown(
                        f"""
                        <div class="info-box info-box-green">
                            <h4>📝 {desc['prompt_type']}</h4>
                            <div class="track-description">
                                {desc['description']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="track-description">
                            {desc['description']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

def render_concert_list():
    """공연 목록을 보여주고 선택할 수 있게 한다."""
    st.markdown(
        """
        <div class="classical-header">
            <h1>🎭 클래식 공연 목록</h1>
            <p>AI가 들려주는 클래식 음악의 아름다운 이야기를 만나보세요</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 개선된 검색 UI
    with st.container():
        st.markdown("### 🔍 공연 검색")
        
        # 검색 방식 선택
        search_mode = st.radio(
            "검색 방식",
            ["🔍 통합 검색", "🎼 고급 검색"],
            horizontal=True
        )
        
        if search_mode == "🔍 통합 검색":
            # 기본 통합 검색
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input(
                    "", 
                    placeholder="🎵 공연명, 🏛️ 공연장명, 👤 작곡가명으로 검색해보세요...",
                    help="예: '베토벤', '예술의전당', '콘체르토', '모차르트' 등"
                )
            with col2:
                clear_search = st.button("🗑️ 검색 초기화", use_container_width=True)
                if clear_search:
                    st.rerun()
        else:
            # 고급 검색 옵션
            col1, col2, col3 = st.columns(3)
            
            with col1:
                title_search = st.text_input("🎵 공연명", placeholder="공연 제목으로 검색")
            with col2:
                venue_search = st.text_input("🏛️ 공연장", placeholder="공연장명으로 검색")
            with col3:
                composer_search = st.text_input("👤 작곡가", placeholder="작곡가명으로 검색")
            
            # 날짜 범위 필터
            col4, col5 = st.columns(2)
            with col4:
                start_date = st.date_input("📅 시작 날짜", value=None)
            with col5:
                end_date = st.date_input("📅 종료 날짜", value=None)
            
            # 고급 검색은 별도 처리
            search_term = None
    
    st.divider()
    
    # 공연 목록 조회 (고급 검색 지원)
    try:
        # 검색 조건 적용
        if search_mode == "🔍 통합 검색" and search_term:
            # 통합 검색: 공연명, 공연장, 설명으로 검색 (개별 쿼리 후 합치기)
            concerts_basic = []
            
            # 제목으로 검색
            title_results = (
                sb.table("concerts")
                .select("id,title,venue,date,description")
                .ilike("title", f"%{search_term}%")
                .execute()
                .data
            )
            concerts_basic.extend(title_results)
            
            # 공연장으로 검색
            venue_results = (
                sb.table("concerts")
                .select("id,title,venue,date,description")
                .ilike("venue", f"%{search_term}%")
                .execute()
                .data
            )
            concerts_basic.extend(venue_results)
            
            # 설명으로 검색
            desc_results = (
                sb.table("concerts")
                .select("id,title,venue,date,description")
                .ilike("description", f"%{search_term}%")
                .execute()
                .data
            )
            concerts_basic.extend(desc_results)
            
            # 작곡가로도 검색
            try:
                composer_tracks = (
                    sb.table("concert_tracks")
                    .select("concert_id")
                    .ilike("composer", f"%{search_term}%")
                    .execute()
                    .data
                )
                
                composer_concert_ids = [track['concert_id'] for track in composer_tracks]
                
                if composer_concert_ids:
                    concerts_by_composer = (
                        sb.table("concerts")
                        .select("id,title,venue,date,description")
                        .in_("id", composer_concert_ids)
                        .execute()
                        .data
                    )
                else:
                    concerts_by_composer = []
                    
            except Exception as e:
                logger.warning(f"작곡가 검색 실패: {str(e)}")
                concerts_by_composer = []
            
            # 결과 합치기 (중복 제거)
            concert_ids = set()
            concerts = []
            
            for concert_list in [concerts_basic, concerts_by_composer]:
                for concert in concert_list:
                    if concert['id'] not in concert_ids:
                        concerts.append(concert)
                        concert_ids.add(concert['id'])
                        
        elif search_mode == "🎼 고급 검색":
            # 기본 쿼리 시작
            query = sb.table("concerts").select("id,title,venue,date,description")
            
            # 각 조건별로 순차적으로 필터 적용
            if title_search:
                query = query.ilike("title", f"%{title_search}%")
            if venue_search:
                query = query.ilike("venue", f"%{venue_search}%")
            if start_date:
                query = query.gte("date", str(start_date))
            if end_date:
                query = query.lte("date", str(end_date))
            
            concerts = query.execute().data
            
            # 작곡가 검색이 있는 경우 추가 필터링
            if composer_search:
                try:
                    composer_tracks = (
                        sb.table("concert_tracks")
                        .select("concert_id")
                        .ilike("composer", f"%{composer_search}%")
                        .execute()
                        .data
                    )
                    
                    valid_ids = [track['concert_id'] for track in composer_tracks]
                    concerts = [c for c in concerts if c['id'] in valid_ids]
                except Exception as e:
                    logger.warning(f"고급 검색에서 작곡가 필터링 실패: {str(e)}")
        else:
            # 기본 조회 (검색 없음)
            concerts = (
                sb.table("concerts")
                .select("id,title,venue,date,description")
                .order("date", desc=True)
                .execute()
                .data
            )
            
    except Exception as e:
        st.error(f"공연 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")
        logger.error(f"공연 조회 오류: {str(e)}")
        return
    
    # 검색 결과 처리
    if not concerts:
        if search_mode == "🔍 통합 검색" and search_term:
            st.markdown(
                f"""
                <div class="info-box info-box-blue">
                    <h3>🔍 '{search_term}'에 대한 검색 결과가 없습니다</h3>
                    <p>다른 키워드로 검색해보시거나 검색어를 줄여보세요.</p>
                    <p>💡 팁: 공연명, 공연장명, 작곡가명으로 검색할 수 있습니다.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif search_mode == "🎼 고급 검색":
            st.markdown(
                """
                <div class="info-box info-box-blue">
                    <h3>🔍 검색 조건에 맞는 공연이 없습니다</h3>
                    <p>검색 조건을 조정해보시거나 일부 조건을 제거해보세요.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div class="info-box info-box-blue">
                    <h3>🎭 아직 등록된 공연이 없습니다</h3>
                    <p>새로운 클래식 공연이 추가되면 이곳에 표시됩니다.</p>
                    <p>관리자가 곧 멋진 공연들을 등록할 예정이니 조금만 기다려주세요!</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        return

    # 정렬 옵션
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"**🎭 총 {len(concerts)}개의 공연**")
    with col2:
        sort_option = st.selectbox(
            "정렬 기준",
            ["📅 날짜순 (최신순)", "📅 날짜순 (과거순)", "🔤 제목순", "🏛️ 공연장순"],
            index=0
        )
    with col3:
        view_mode = st.selectbox("보기", ["카드뷰", "리스트뷰"], index=0)
    
    # 정렬 적용
    if sort_option == "📅 날짜순 (최신순)":
        concerts.sort(key=lambda x: x['date'], reverse=True)
    elif sort_option == "📅 날짜순 (과거순)":
        concerts.sort(key=lambda x: x['date'])
    elif sort_option == "🔤 제목순":
        concerts.sort(key=lambda x: x['title'])
    elif sort_option == "🏛️ 공연장순":
        concerts.sort(key=lambda x: x['venue'])
    
    st.divider()

    # 뷰 모드에 따른 표시
    if view_mode == "카드뷰":
        # 기존 2열 카드 표시
        cols = st.columns(2)
        
        for idx, concert in enumerate(concerts):
            col = cols[idx % 2]
            
            with col:
                # 공연 날짜 포맷팅
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(concert['date'], '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%Y년 %m월 %d일')
                    day_of_week = ['월', '화', '수', '목', '금', '토', '일'][date_obj.weekday()]
                    date_display = f"{formatted_date} ({day_of_week})"
                except:
                    date_display = concert['date']
                
                # 개선된 카드 디자인
                st.markdown(
                    f"""
                    <div class="concert-card">
                        <div class="concert-title">🎵 {concert['title']}</div>
                        <div class="concert-details">
                            <div class="concert-venue">🏛️ {concert['venue']}</div>
                            <div class="concert-date">📅 {date_display}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # 곡 수 정보와 미리보기
                col_info, col_btn = st.columns([3, 2])
                
                with col_info:
                    try:
                        track_count = (
                            sb.table("concert_tracks")
                              .select("id", count="exact")
                              .eq("concert_id", concert["id"])
                              .execute()
                              .count
                        )
                        
                        if track_count > 0:
                            st.markdown(f"**🎼 총 {track_count}곡**")
                            
                            # 첫 번째 곡 미리보기
                            first_track = (
                                sb.table("concert_tracks")
                                  .select("track_title, composer")
                                  .eq("concert_id", concert["id"])
                                  .limit(1)
                                  .execute()
                                  .data
                            )
                            if first_track:
                                st.caption(f"♪ {first_track[0]['track_title']} - {first_track[0]['composer']}")
                                if track_count > 1:
                                    st.caption(f"외 {track_count-1}곡")
                        else:
                            st.markdown("**🎼 곡 정보 준비 중**")
                            st.caption("곧 곡 목록이 업데이트됩니다")
                            
                    except Exception as e:
                        st.markdown("**🎼 곡 수: 정보 없음**")
                        logger.warning(f"곡 수 조회 오류: {str(e)}")
                
                with col_btn:
                    if st.button(
                        "🎼 자세히 보기", 
                        key=f"select_{concert['id']}",
                        use_container_width=True,
                        type="primary"
                    ):
                        st.query_params["concert_id"] = concert["id"]
                        st.rerun()
                
                # 카드 간격
                st.markdown("<br>", unsafe_allow_html=True)
    
    else:
        # 리스트뷰 표시
        for idx, concert in enumerate(concerts):
            # 공연 날짜 포맷팅
            try:
                from datetime import datetime
                date_obj = datetime.strptime(concert['date'], '%Y-%m-%d')
                formatted_date = date_obj.strftime('%m월 %d일')
                day_of_week = ['월', '화', '수', '목', '금', '토', '일'][date_obj.weekday()]
                date_display = f"{formatted_date} ({day_of_week})"
            except:
                date_display = concert['date']
            
            # 리스트 아이템
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"**🎵 {concert['title']}**")
                if concert.get('description'):
                    st.caption(concert['description'][:50] + "..." if len(concert['description']) > 50 else concert['description'])
            
            with col2:
                st.write(f"🏛️ {concert['venue']}")
            
            with col3:
                st.write(f"📅 {date_display}")
                
                # 곡 수 표시
                try:
                    track_count = (
                        sb.table("concert_tracks")
                          .select("id", count="exact")
                          .eq("concert_id", concert["id"])
                          .execute()
                          .count
                    )
                    st.caption(f"🎼 {track_count}곡")
                except:
                    st.caption("🎼 정보 없음")
            
            with col4:
                if st.button(
                    "보기", 
                    key=f"list_select_{concert['id']}",
                    use_container_width=True
                ):
                    st.query_params["concert_id"] = concert["id"]
                    st.rerun()
            
            # 구분선
            if idx < len(concerts) - 1:
                st.markdown("---")

# ────────────────────────────────
# 메인 로직: 파라미터에 따른 페이지 렌더링
# ────────────────────────────────
try:
    if not cid:
        render_concert_list()
    else:
        # 뒤로 가기 버튼
        if st.button("← 공연 목록으로"):
            del st.query_params["concert_id"]
            st.rerun()
        
        st.markdown("---")
        
        render_detail(cid)
        
except Exception as e:
    logger.error(f"페이지 렌더링 중 예상치 못한 오류 발생: {str(e)}")
    st.error("페이지를 불러오는 중 오류가 발생했습니다.")
    st.info("잠시 후 다시 시도해주세요.")
    
    # 공연 목록으로 돌아가기 버튼
    if st.button("🏠 홈으로 돌아가기"):
        if "concert_id" in st.query_params:
            del st.query_params["concert_id"]
        st.rerun()