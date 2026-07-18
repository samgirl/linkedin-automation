"""History page - view past activity."""
from __future__ import annotations

import json

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


def history_page(db: DatabaseManager, user_id: int = 1) -> None:
    st.title("History")
    st.caption("View your past activity")

    tab_actions, tab_search = st.tabs(["Actions", "Search History"])

    with tab_actions:
        st.subheader("Recent Actions")
        actions = db.get_actions(limit=50, user_id=user_id)
        if not actions:
            st.info("No actions yet. Create posts or generate comments to see history here.")
            return

        for action in actions:
            post = db.get_post_by_id(action.post_id)
            post_title = (post.title or post.text[:60]) if post else "Unknown"
            ts = action.timestamp.strftime("%Y-%m-%d %H:%M") if action.timestamp else ""
            st.markdown(f"**{action.action}** - {post_title}")
            st.caption(ts)

    with tab_search:
        st.subheader("Search History")
        history = db.get_search_history(limit=50)
        if not history:
            st.info("No search history yet.")
            return

        for entry in history:
            domains = json.loads(entry.domains) if entry.domains else []
            keywords = json.loads(entry.keywords_used) if entry.keywords_used else []
            ts = entry.searched_at.strftime("%Y-%m-%d %H:%M") if entry.searched_at else ""

            with st.expander(
                "Search: " + entry.query[:60] + " | " + str(entry.results_count) + " results"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Query:** " + entry.query)
                    st.markdown("**Domains:** " + (", ".join(domains) if domains else "N/A"))
                with col2:
                    st.metric("Results", entry.results_count)
                    st.metric("Avg Score", "%.1f" % entry.avg_score)
                st.caption("Searched at: " + ts)
