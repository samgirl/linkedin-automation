"""AI LinkedIn Assistant - Streamlit Application Entry Point."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

# Load Streamlit Cloud secrets into env vars
if hasattr(st, "secrets") and st.secrets:
    for key in [
        "AI_PROVIDER", "GEMINI_API_KEY", "GEMINI_MODEL",
        "OPENAI_API_KEY", "OPENAI_MODEL", "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL", "OLLAMA_BASE_URL", "OLLAMA_MODEL",
        "EMBEDDING_MODEL", "DATABASE_URL",
    ]:
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key])

from ai_content_radar.database.manager import DatabaseManager

st.set_page_config(
    page_title="AI LinkedIn Assistant",
    page_icon=":rocket:",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource
def init_db():
    db = DatabaseManager()
    db.create_tables()
    return db

db = init_db()

if "user_id" not in st.session_state:
    from ai_content_radar.ui.pages.login_page import login_page
    login_page(db)
    st.stop()

user_id = st.session_state["user_id"]
user_name = st.session_state["user_name"]

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

with st.sidebar:
    st.markdown("## AI LinkedIn Assistant")
    st.caption(f"Welcome, **{user_name}**")
    st.divider()

    pages = {
        "home": "Home",
        "profile": "My Profile",
        "post": "Create Post",
        "comment": "Comment Helper",
        "history": "History",
    }

    for key, label in pages.items():
        if st.button(
            label,
            use_container_width=True,
            type="primary" if st.session_state.current_page == key else "secondary",
        ):
            st.session_state.current_page = key
            st.rerun()

    st.divider()
    if st.button("Switch User", use_container_width=True):
        for k in ["user_id", "user_name"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

if st.session_state.current_page == "home":
    from ai_content_radar.ui.pages.home_page import home_page
    home_page(db, user_id=user_id)
elif st.session_state.current_page == "profile":
    from ai_content_radar.ui.pages.profile_page import profile_page
    profile_page(db, user_id=user_id)
elif st.session_state.current_page == "post":
    from ai_content_radar.ui.pages.post_page import post_page
    post_page(db, user_id=user_id)
elif st.session_state.current_page == "comment":
    from ai_content_radar.ui.pages.comment_helper_page import comment_helper_page
    comment_helper_page(db, user_id=user_id)
elif st.session_state.current_page == "history":
    from ai_content_radar.ui.pages.history_page import history_page
    history_page(db, user_id=user_id)
