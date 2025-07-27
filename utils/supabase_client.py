import os, streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY    = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

@st.cache_resource(ttl=300)
def get_sb_client(use_service: bool = False) -> Client:
    key = SUPABASE_SERVICE_KEY if use_service else SUPABASE_ANON_KEY
    return create_client(SUPABASE_URL, key)
