"""AI LinkedIn Assistant - Streamlit Application Entry Point."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

# Load Streamlit Cloud secrets into env vars so settings.py picks them up
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

# --- Page Config ---
st.set_page_config(
    page_title="AI Content Radar",
    page_icon="radar",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Initialize DB ---
@st.cache_resource
def init_db():
    db = DatabaseManager()
    db.create_tables()
    return db

db = init_db()

# --- Check Login ---
if "user_id" not in st.session_state:
    from ai_content_radar.ui.pages.login_page import login_page
    login_page(db)
    st.stop()

user_id = st.session_state["user_id"]
user_name = st.session_state["user_name"]

# --- Session State ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "post"

# --- Sidebar ---
with st.sidebar:
    st.title("AI Content Radar")
    st.caption("Logged in as **" + user_name + "**")
    st.divider()

    pages = {
        "post": "Create Post",
        "comment": "Comment Helper",
        "keywords": "Keywords",
        "knowledge": "My Context",
        "analytics": "Analytics",
        "history": "History",
        "settings": "Settings",
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
        del st.session_state["user_id"]
        del st.session_state["user_name"]
        st.rerun()

# --- Page Router ---
if st.session_state.current_page == "post":
    from ai_content_radar.ui.pages.post_page import post_page
    post_page(db, user_id=user_id)
elif st.session_state.current_page == "comment":
    from ai_content_radar.ui.pages.comment_helper_page import comment_helper_page
    comment_helper_page(db, user_id=user_id)
elif st.session_state.current_page == "keywords":
    from ai_content_radar.services.taxonomy import KeywordTaxonomy
    taxonomy = KeywordTaxonomy()
    from ai_content_radar.ui.pages.keywords_page import keywords_page
    keywords_page(db, taxonomy)
elif st.session_state.current_page == "knowledge":
    from ai_content_radar.ui.pages.knowledge_page import knowledge_page
    from ai_content_radar.services.taxonomy import KeywordTaxonomy
    taxonomy = KeywordTaxonomy()
    knowledge_page(db, taxonomy, user_id=user_id)
elif st.session_state.current_page == "analytics":
    from ai_content_radar.services.taxonomy import KeywordTaxonomy
    taxonomy = KeywordTaxonomy()
    from ai_content_radar.ui.pages.analytics_page import analytics_page
    analytics_page(db, taxonomy)
elif st.session_state.current_page == "history":
    from ai_content_radar.ui.pages.history_page import history_page
    history_page(db, user_id=user_id)
elif st.session_state.current_page == "settings":
    from ai_content_radar.ui.pages.settings_page import settings_page
    from ai_content_radar.services.taxonomy import KeywordTaxonomy
    taxonomy = KeywordTaxonomy()
    settings_page(db, taxonomy)
