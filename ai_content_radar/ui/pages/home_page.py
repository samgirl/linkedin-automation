"""Home page - dashboard with quick actions and overview."""
from __future__ import annotations

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


def home_page(db: DatabaseManager, user_id: int = 1) -> None:
    knowledge = db.get_knowledge(user_id=user_id)
    has_profile = len(knowledge) > 0

    if not has_profile:
        st.title("Welcome!")
        st.markdown(
            "Before you start, tell us about yourself so AI can write content that sounds like **you**."
        )
        st.divider()
        if st.button("Set Up My Profile", type="primary", use_container_width=True):
            st.session_state.current_page = "profile"
            st.rerun()
        st.divider()
        st.info("Once your profile is set up, you can create posts and comments.")
        return

    st.title("Home")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Create a Post")
        st.caption("AI writes a LinkedIn post based on your expertise")
        if st.button("Start Writing", use_container_width=True, key="home_post"):
            st.session_state.current_page = "post"
            st.rerun()

    with col2:
        st.subheader("Comment on a Post")
        st.caption("Paste a LinkedIn post, get AI comment options")
        if st.button("Get Comments", use_container_width=True, key="home_comment"):
            st.session_state.current_page = "comment"
            st.rerun()

    st.divider()

    st.subheader("Your Context")
    with st.expander(f"{len(knowledge)} entries saved", expanded=False):
        for k in knowledge:
            st.caption(f"**{k.key}**: {k.value[:150]}")

    if st.button("Edit Profile", key="home_edit_profile"):
        st.session_state.current_page = "profile"
        st.rerun()
