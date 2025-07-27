# utils/auth.py
import os, streamlit as st
from dotenv import load_dotenv
from utils.supabase_client import get_sb_client

load_dotenv()
sb = get_sb_client()

# 1) 로그인 & 세션 저장
def sign_in(email: str, password: str) -> None:
    res = sb.auth.sign_in_with_password({"email": email, "password": password})
    st.session_state["sb_session"] = res.session
    st.session_state["sb_user"]    = res.user

    # 오직 두 계정만 가정 → 이메일로 역할 직접 지정
    role = "admin" if email.lower() == "admin@test.com" else "user"
    st.session_state["sb_role"] = role

def sign_out() -> None:
    st.session_state.clear()

# 2) 세션 복구 & 편의 함수
def _restore_session() -> None:
    if "sb_session" in st.session_state:
        at = st.session_state["sb_session"].access_token
        rt = st.session_state["sb_session"].refresh_token
        sb.auth.set_session(at, rt)

def get_current_user():
    _restore_session()
    return st.session_state.get("sb_user")

def get_role() -> str | None:
    return st.session_state.get("sb_role")

# 페이지용 데코 유사 함수
def require_login(role: str | None = None):
    """
    role 인자가 있으면 admin/user 문자열만 비교.
    조건 불충족 시 메시지 없이 st.stop() 으로 즉시 중단.
    """
    if "sb_user" not in st.session_state:
        st.stop()
    if role and get_role() != role:
        st.stop()
    return st.session_state["sb_user"]
