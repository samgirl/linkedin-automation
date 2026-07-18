"""Shared UI components for post rendering."""
from __future__ import annotations

import json
import webbrowser
from typing import Any

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


def render_post_card(db: DatabaseManager, result: dict[str, Any], index: int, user_id: int = 1) -> None:
    """Render a single post card in the search results."""
    post = None
    ranking = result.get("ranking")
    score = result.get("score", 0)
    reason = result.get("reason", "")

    if hasattr(result, "post"):
        post = result.post
        ranking = result.ranking
        score = ranking.score if ranking else 0
        reason = ranking.reason if ranking else ""
    elif "post" in result:
        post = result["post"]

    if not post:
        return

    if score >= 80:
        score_color = "green"
    elif score >= 60:
        score_color = "orange"
    elif score >= 40:
        score_color = "blue"
    else:
        score_color = "gray"

    actions = db.get_actions(limit=500, user_id=user_id)
    post_actions = [a for a in actions if a.post_id == post.id]
    is_approved = any(a.action == "approved" for a in post_actions)
    is_rejected = any(a.action == "rejected" for a in post_actions)
    is_favorited = any(a.action == "favorite" for a in post_actions)

    status_badge = ""
    if is_approved:
        status_badge = " :green[APPROVED]"
    elif is_rejected:
        status_badge = " :red[REJECTED]"
    elif is_favorited:
        status_badge = " :star[FAVORITE]"

    title_text = post.title or (post.text[:80] if post.text else "Untitled")
    with st.expander(
        f":{score_color}[Score: {score}] | {title_text}...{status_badge}",
        expanded=False,
    ):
        col_score, col_info = st.columns([1, 3])
        with col_score:
            st.metric("Score", score)
            if reason:
                st.caption(reason)
        with col_info:
            if hasattr(post, "author_rel") and post.author_rel:
                st.markdown(f"**{post.author_rel.name}**")
                if post.author_rel.title:
                    st.caption(post.author_rel.title)
                if post.author_rel.organization:
                    st.caption(post.author_rel.organization)

            eng_parts = []
            if post.engagement_likes:
                eng_parts.append(f"{post.engagement_likes} likes")
            if post.engagement_comments:
                eng_parts.append(f"{post.engagement_comments} comments")
            if post.engagement_shares:
                eng_parts.append(f"{post.engagement_shares} shares")
            if eng_parts:
                st.caption(" | ".join(eng_parts))

        st.divider()
        st.markdown("**Post Content:**")
        st.text_area(
            f"post_text_{index}",
            post.text[:1500] if post.text else "",
            height=120,
            disabled=True,
            key=f"search_post_text_{post.id}",
        )

        if ranking:
            st.markdown("**Score Breakdown:**")
            bcols = st.columns(4)
            bcols[0].metric("Keyword", f"{ranking.keyword_match_score:.0f}")
            bcols[1].metric("Quality", f"{ranking.quality_score:.0f}")
            bcols[2].metric("Freshness", f"{ranking.freshness_score:.0f}")
            bcols[3].metric("Opportunity", f"{ranking.opportunity_score:.0f}")

        comments = db.get_comments_for_post(post.id, user_id=user_id)
        if comments:
            st.markdown("**Generated Comments:**")
            for comment in comments:
                ctype = comment.comment_type.replace("_", " ").title()
                st.markdown(f"*{ctype}:*")
                st.text_area(
                    f"search_comment_{comment.id}",
                    comment.text,
                    height=80,
                    disabled=True,
                    key=f"search_cmt_{comment.id}",
                )

        st.divider()
        act_cols = st.columns(7)

        with act_cols[0]:
            if st.button("Generate", key=f"s_gen_{post.id}", use_container_width=True,
                         help="Generate AI comment for this post"):
                with st.spinner("Generating comment..."):
                    try:
                        from ai_content_radar.ai_engine.comment_engine import CommentEngine
                        engine = CommentEngine(db)
                        result = engine.generate_comment(post.id, "professional", user_id=user_id)
                        if result:
                            st.success("Comment generated!")
                            st.rerun()
                        else:
                            st.error("AI returned no response. Check your AI settings.")
                    except Exception as e:
                        st.error(f"Failed: {e}")

        with act_cols[1]:
            if st.button("Approve", key=f"s_approve_{post.id}", type="primary", use_container_width=True):
                db.record_action(post.id, "approved", user_id=user_id)
                st.success("Approved!")
                st.rerun()
        with act_cols[2]:
            if st.button("Reject", key=f"s_reject_{post.id}", use_container_width=True):
                db.record_action(post.id, "rejected", user_id=user_id)
                st.rerun()
        with act_cols[3]:
            fav_label = "Unfavorite" if is_favorited else "Favorite"
            if st.button(fav_label, key=f"s_fav_{post.id}", use_container_width=True):
                action = "unfavorite" if is_favorited else "favorite"
                db.record_action(post.id, action, user_id=user_id)
                st.rerun()
        with act_cols[4]:
            if st.button("Copy", key=f"s_copy_{post.id}", use_container_width=True):
                if comments:
                    st.code(comments[0].text, language=None)
                    db.record_action(post.id, "copied", user_id=user_id)
        with act_cols[5]:
            if st.button("Open", key=f"s_open_{post.id}", use_container_width=True):
                webbrowser.open(post.url)
        with act_cols[6]:
            if comments and st.button("Post", key=f"s_post_{post.id}", use_container_width=True,
                                      help="Post this comment to LinkedIn"):
                _post_to_linkedin(post.url, comments[0].text, post.id, db)

        st.caption(f"Source: {post.url}")


def _post_to_linkedin(post_url: str, comment_text: str, post_id: int, db: DatabaseManager) -> None:
    """Post a comment to LinkedIn via the user's Chrome."""
    from ai_content_radar.services.linkedin import _is_cdp_running, launch_chrome, get_driver, post_comment

    if not _is_cdp_running():
        status = launch_chrome()
        if status == "not_found":
            st.error("Chrome not found. Please install Google Chrome.")
            return
        if status != "launched":
            st.error(f"Could not launch Chrome: {status}")
            return
        st.info("Chrome launched. Log into LinkedIn in the Chrome window, then click Post again.")
        return

    try:
        driver = get_driver()
    except Exception as e:
        st.error(f"Could not connect to Chrome: {e}")
        return

    with st.spinner("Posting comment..."):
        result = post_comment(driver, post_url, comment_text)

    if result["success"]:
        st.success(result["message"])
        db.record_action(post_id, "posted_to_linkedin")
    else:
        st.error(result["message"])
