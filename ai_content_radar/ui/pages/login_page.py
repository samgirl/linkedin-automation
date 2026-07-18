"""Login page - simple name-based login for personalization."""
from __future__ import annotations

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


def login_page(db: DatabaseManager) -> bool:
    """Show login screen. Returns True if logged in, False otherwise."""
    st.title("Welcome to AI LinkedIn Assistant")
    st.caption("Log in to personalize your experience")

    users = db.get_all_users()

    tab_login, tab_new = st.tabs(["Log In", "New User"])

    with tab_login:
        if users:
            user_names = [u.name for u in users]
            selected = st.selectbox("Select your name", user_names, key="login_select")
            if st.button("Log In", type="primary", use_container_width=True):
                user = next(u for u in users if u.name == selected)
                st.session_state["user_id"] = user.id
                st.session_state["user_name"] = user.name
                st.rerun()
        else:
            st.info("No users yet. Create your profile first.")

    with tab_new:
        name = st.text_input("Your name", placeholder="e.g. Arjun", key="new_name")
        email = st.text_input("Email (optional)", placeholder="you@example.com", key="new_email")

        if st.button("Create Profile", type="primary", use_container_width=True):
            if name.strip():
                user = db.get_or_create_user(name.strip(), email.strip())
                st.session_state["user_id"] = user.id
                st.session_state["user_name"] = user.name
                st.rerun()
            else:
                st.warning("Enter your name.")

    return False
