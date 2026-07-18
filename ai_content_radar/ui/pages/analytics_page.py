"""Analytics page - dashboard with trends and insights."""
from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import func

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.taxonomy import KeywordTaxonomy


def analytics_page(db: DatabaseManager, taxonomy: KeywordTaxonomy) -> None:
    st.title("Analytics")
    st.caption("Track your engagement patterns and preferences")

    try:
        analytics = db.get_analytics()
    except Exception as e:
        st.error("Failed to load analytics: " + str(e))
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Posts", analytics["total_posts"])
    col2.metric("Ranked", analytics["total_ranked"])
    col3.metric("Comments", analytics["total_comments"])
    col4.metric("Approved", analytics["approved"])
    col5.metric("Rejected", analytics["rejected"])

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Action Distribution")
        action_data = db.get_action_counts()
        if action_data:
            df_actions = pd.DataFrame(
                list(action_data.items()),
                columns=["Action", "Count"],
            )
            st.bar_chart(df_actions.set_index("Action"))
        else:
            st.info("No actions recorded yet.")

    with col_right:
        st.subheader("Score Distribution")
        ranked = db.get_ranked_posts(min_score=0, limit=500)
        if ranked:
            scores = [r.score for _, r in ranked]
            df_scores = pd.DataFrame(scores, columns=["Score"])
            st.bar_chart(df_scores["Score"].value_counts().sort_index())
        else:
            st.info("No ranked posts yet.")

    st.divider()

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("Average Score", analytics["avg_score"])
    with col_s2:
        st.metric("Highest Score", analytics["max_score"])

    st.divider()

    st.subheader("Recent Activity")
    recent_actions = db.get_actions(limit=20)
    if recent_actions:
        activity_data = []
        for action in recent_actions:
            post = db.get_post_by_id(action.post_id)
            post_title = (post.title or post.text[:60]) if post else "Unknown"
            activity_data.append({
                "Time": action.timestamp.strftime("%Y-%m-%d %H:%M") if action.timestamp else "",
                "Action": action.action,
                "Post": post_title,
            })
        df_activity = pd.DataFrame(activity_data)
        st.dataframe(df_activity, use_container_width=True, hide_index=True)
    else:
        st.info("No recent activity.")
