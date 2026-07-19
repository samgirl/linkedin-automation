"""History page - view past activity."""
from __future__ import annotations

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


def history_page(db: DatabaseManager, user_id: int = 1) -> None:
    st.title("History")
    st.caption("Your recent activity")

    actions = db.get_actions(limit=50, user_id=user_id)

    if not actions:
        st.info("No history yet. Create posts or generate comments to see them here.")
        return

    for action in actions:
        post = db.get_post_by_id(action.post_id)
        post_title = (post.title or post.text[:60]) if post else "Unknown"
        ts = action.timestamp.strftime("%Y-%m-%d %H:%M") if action.timestamp else ""
        st.markdown(f"**{action.action}** - {post_title}")
        st.caption(ts)
