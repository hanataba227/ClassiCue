# pages/login.py  ★전면교체
import streamlit as st
from utils.auth import sign_in, sign_out, get_current_user

st.set_page_config(page_title="로그인", layout="centered")
st.title("🔐 로그인")

user = get_current_user()

if user:
    st.success(f"{user.email} 로 로그인됨")
    if st.button("로그아웃"):
        sign_out()
        st.rerun()
else:
    with st.form("login_form"):
        email    = st.text_input("이메일", placeholder="admin@test.com")
        password = st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인"):
            sign_in(email, password)
            st.rerun()