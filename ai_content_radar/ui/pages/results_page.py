"""Results / Opportunities page - view and act on ranked posts."""
from __future__ import annotations

import json
import webbrowser
from typing import Any

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.learning import LearningEngine
from ai_content_radar.services.taxonomy import KeywordTaxonomy


def results_page(db: DatabaseManager, taxonomy: KeywordTaxonomy, user_id: int = 1) -> None:
    st.title("Opportunities")
    st.caption("Review ranked posts, generate comments, and take action")

    learning = LearningEngine(db)

    # --- Filter Controls ---
    col1, col2, col3 = st.columns(3)
    with col1:
        min_score = st.slider("Min Score", 0, 100, 40, 5, key="results_min_score")
    with col2:
        filter_action = st.selectbox("Filter", ["All", "Pending", "Approved", "Rejected", "Favorites"], key="results_filter")
    with col3:
        sort_by = st.selectbox("Sort", ["Score (high to low)", "Score (low to high)", "Most Recent"], key="results_sort")

    # --- Bulk Generate Comments ---
    ranked = db.get_ranked_posts(min_score=min_score, limit=200)

    if not ranked:
        st.info("No ranked posts found. Run a search first from the Search page.")
        return

    # Count posts without comments
    posts_without_comments = []
    for post, ranking in ranked:
        existing = db.get_comments_for_post(post.id)
        if not existing:
            posts_without_comments.append((post, ranking))

    if posts_without_comments:
        st.info(f"{len(posts_without_comments)} posts don't have comments yet.")
        if st.button(f"Generate Comments for All ({len(posts_without_comments)})", type="primary"):
            with st.spinner("Generating comments for all posts..."):
                try:
                    from ai_content_radar.ai_engine.comment_engine import CommentEngine
                    engine = CommentEngine(db)
                    generated = 0
                    progress = st.progress(0)
                    for i, (post, _) in enumerate(posts_without_comments):
                        try:
                            result = engine.generate_comment(post.id, "professional", user_id=user_id)
                            if result:
                                generated += 1
                        except Exception as e:
                            st.warning(f"Failed for post {post.id}: {e}")
                        progress.progress((i + 1) / len(posts_without_comments))
                    st.success(f"Generated {generated} comments!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Comment generation failed: {e}")

    # Apply action filter
    all_actions = db.get_actions(limit=1000, user_id=user_id)
    action_map = {}
    for a in all_actions:
        action_map.setdefault(a.post_id, []).append(a)

    filtered = []
    for post, ranking in ranked:
        post_actions = action_map.get(post.id, [])

        if filter_action == "All":
            filtered.append((post, ranking))
        elif filter_action == "Pending" and not post_actions:
            filtered.append((post, ranking))
        elif filter_action == "Approved" and any(a.action == "approved" for a in post_actions):
            filtered.append((post, ranking))
        elif filter_action == "Rejected" and any(a.action == "rejected" for a in post_actions):
            filtered.append((post, ranking))
        elif filter_action == "Favorites" and any(a.action == "favorite" for a in post_actions):
            filtered.append((post, ranking))

    if sort_by == "Score (high to low)":
        filtered.sort(key=lambda x: x[1].score, reverse=True)
    elif sort_by == "Score (low to high)":
        filtered.sort(key=lambda x: x[1].score)
    elif sort_by == "Most Recent":
        filtered.sort(key=lambda x: x[0].date_collected or "", reverse=True)

    if not filtered:
        st.info("No posts match the current filters.")
        return

    st.caption(f"Showing {len(filtered)} posts")
    st.divider()

    for post, ranking in filtered:
        _render_opportunity_card(db, post, ranking, learning_engine=learning)


def _render_opportunity_card(db: DatabaseManager, post: Any, ranking: Any, learning_engine: Any = None) -> None:
    """Render a single post opportunity card."""
    actions = db.get_actions(limit=1000)
    post_actions = [a for a in actions if a.post_id == post.id]
    is_approved = any(a.action == "approved" for a in post_actions)
    is_rejected = any(a.action == "rejected" for a in post_actions)
    is_favorited = any(a.action == "favorite" for a in post_actions)

    if ranking.score >= 80:
        score_color = "green"
    elif ranking.score >= 60:
        score_color = "orange"
    elif ranking.score >= 40:
        score_color = "blue"
    else:
        score_color = "gray"

    status_badge = ""
    if is_approved:
        status_badge = " :green[APPROVED]"
    elif is_rejected:
        status_badge = " :red[REJECTED]"
    elif is_favorited:
        status_badge = " :star[FAVORITE]"

    post_title = post.title or (post.text[:80] if post.text else "Untitled")
    with st.expander(
        f":{score_color}[Score: {ranking.score}] | {post_title}...{status_badge}",
        expanded=False,
    ):
        col_score, col_info = st.columns([1, 3])
        with col_score:
            st.metric("Score", ranking.score)
            st.caption(ranking.reason)
        with col_info:
            if post.author_rel:
                st.markdown(f"**{post.author_rel.name}**")
                if post.author_rel.title:
                    st.caption(f"{post.author_rel.title}")
                if post.author_rel.organization:
                    st.caption(f"{post.author_rel.organization}")
            else:
                st.caption("Unknown author")

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
        st.text_area("Post", (post.text or "")[:1500], height=150, disabled=True, key=f"post_text_{post.id}")

        hashtags = json.loads(post.hashtags) if post.hashtags else []
        tech = json.loads(post.mentioned_tech) if post.mentioned_tech else []
        orgs = json.loads(post.mentioned_orgs) if post.mentioned_orgs else []

        if hashtags or tech or orgs:
            st.markdown("**Tags:**")
            tag_cols = st.columns(3)
            with tag_cols[0]:
                if hashtags:
                    st.caption("Hashtags: " + ", ".join(hashtags[:5]))
            with tag_cols[1]:
                if tech:
                    st.caption("Technologies: " + ", ".join(tech[:5]))
            with tag_cols[2]:
                if orgs:
                    st.caption("Organizations: " + ", ".join(orgs[:5]))

        st.markdown("**Score Breakdown:**")
        score_cols = st.columns(4)
        score_cols[0].metric("Keyword", f"{ranking.keyword_match_score:.0f}")
        score_cols[1].metric("Quality", f"{ranking.quality_score:.0f}")
        score_cols[2].metric("Freshness", f"{ranking.freshness_score:.0f}")
        score_cols[3].metric("Opportunity", f"{ranking.opportunity_score:.0f}")

        comments = db.get_comments_for_post(post.id)
        if comments:
            st.markdown("**Generated Comments:**")
            for comment in comments:
                ctype = comment.comment_type.replace("_", " ").title()
                st.markdown(f"*{ctype}:*")
                st.text_area(
                    f"Comment {comment.id}",
                    comment.text,
                    height=100,
                    disabled=True,
                    key=f"comment_{comment.id}",
                )

        st.divider()
        btn_cols = st.columns(7)

        with btn_cols[0]:
            if st.button("Generate", key=f"gen_{post.id}", use_container_width=True,
                         help="Generate AI comment"):
                with st.spinner("Generating..."):
                    try:
                        from ai_content_radar.ai_engine.comment_engine import CommentEngine
                        engine = CommentEngine(db)
                        gen_result = engine.generate_comment(post.id, "professional")
                        if gen_result:
                            st.success("Generated!")
                            st.rerun()
                        else:
                            st.error("AI returned no response.")
                    except Exception as e:
                        st.error(f"Failed: {e}")

        with btn_cols[1]:
            if st.button("Approve", key=f"approve_{post.id}", type="primary", use_container_width=True):
                if learning_engine:
                    learning_engine.record_action(post.id, "approved")
                else:
                    db.record_action(post.id, "approved")
                st.success("Approved!")
                st.rerun()

        with btn_cols[2]:
            if st.button("Reject", key=f"reject_{post.id}", use_container_width=True):
                if learning_engine:
                    learning_engine.record_action(post.id, "rejected")
                else:
                    db.record_action(post.id, "rejected")
                st.warning("Rejected")
                st.rerun()

        with btn_cols[3]:
            fav_label = "Unfavorite" if is_favorited else "Favorite"
            if st.button(fav_label, key=f"fav_{post.id}", use_container_width=True):
                action = "unfavorite" if is_favorited else "favorite"
                if learning_engine:
                    learning_engine.record_action(post.id, action)
                else:
                    db.record_action(post.id, action)
                st.rerun()

        with btn_cols[4]:
            if st.button("Copy", key=f"copy_{post.id}", use_container_width=True):
                if comments:
                    st.code(comments[0].text, language=None)
                    if learning_engine:
                        learning_engine.record_action(post.id, "copied")
                    else:
                        db.record_action(post.id, "copied")
                    st.success("Copied!")

        with btn_cols[5]:
            if st.button("Open", key=f"open_{post.id}", use_container_width=True):
                webbrowser.open(post.url)

        with btn_cols[6]:
            if comments and st.button("Post", key=f"post_li_{post.id}", use_container_width=True,
                                      help="Post comment to LinkedIn"):
                from ai_content_radar.ui.components import _post_to_linkedin
                _post_to_linkedin(post.url, comments[0].text, post.id, db)

        st.caption(f"Source: {post.url}")
