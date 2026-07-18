"""Analytics page - dashboard with trends and insights."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from sqlalchemy import func

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.taxonomy import KeywordTaxonomy


def analytics_page(db: DatabaseManager, taxonomy: KeywordTaxonomy) -> None:
    st.title("Analytics")
    st.caption("Track your engagement patterns and preferences")

    # --- Overview Metrics ---
    try:
        analytics = db.get_analytics()
    except Exception as e:
        st.error(f"Failed to load analytics: {e}")
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Posts", analytics["total_posts"])
    col2.metric("Ranked", analytics["total_ranked"])
    col3.metric("Comments", analytics["total_comments"])
    col4.metric("Approved", analytics["approved"])
    col5.metric("Rejected", analytics["rejected"])

    st.divider()

    # --- Action Distribution ---
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

    # --- Score Metrics ---
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("Average Score", analytics["avg_score"])
    with col_s2:
        st.metric("Highest Score", analytics["max_score"])

    # --- Top Keywords / Domains ---
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.subheader("Top Keyword Matches")
        keyword_counts = _get_keyword_stats(db)
        if keyword_counts:
            df_kw = pd.DataFrame(
                keyword_counts[:10],
                columns=["Keyword", "Matches"],
            )
            st.dataframe(df_kw, use_container_width=True, hide_index=True)
        else:
            st.info("No keyword data yet.")

    with col_t2:
        st.subheader("Top Domains")
        domain_counts = _get_domain_stats(db)
        if domain_counts:
            df_dom = pd.DataFrame(
                domain_counts[:10],
                columns=["Domain", "Posts"],
            )
            st.dataframe(df_dom, use_container_width=True, hide_index=True)
        else:
            st.info("No domain data yet.")

    st.divider()

    # --- Recent Activity ---
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


def _get_keyword_stats(db: DatabaseManager) -> list[tuple[str, int]]:
    """Get top keyword matches from the database."""
    with db.session() as s:
        from ai_content_radar.models.database import KeywordRanking, Keyword
        results = (
            s.query(Keyword.term, func.count(KeywordRanking.id))
            .join(Keyword, KeywordRanking.keyword_id == Keyword.id)
            .group_by(Keyword.term)
            .order_by(func.count(KeywordRanking.id).desc())
            .limit(10)
            .all()
        )
        return results


def _get_domain_stats(db: DatabaseManager) -> list[tuple[str, int]]:
    """Get post counts by domain from taxonomy."""
    from ai_content_radar.services.taxonomy import KeywordTaxonomy
    taxonomy = KeywordTaxonomy()
    domain_counts = []
    for domain in taxonomy.domains:
        keywords = taxonomy.get_domain_keywords(domain)
        count = len(keywords)
        domain_counts.append((domain, count))
    domain_counts.sort(key=lambda x: x[1], reverse=True)
    return domain_counts
