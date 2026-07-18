"""Comment page - search LinkedIn for relevant posts to comment on."""
from __future__ import annotations

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.learning import LearningEngine
from ai_content_radar.services.ranking import RankingEngine
from ai_content_radar.services.taxonomy import KeywordTaxonomy
from ai_content_radar.ui.components import render_post_card


def search_page(db: DatabaseManager, taxonomy: KeywordTaxonomy, user_id: int = 1) -> None:
    st.title("Find Posts to Comment On")

    from ai_content_radar.services.linkedin import get_status, launch_chrome, _is_cdp_running
    chrome_info = get_status()
    chrome_ok = chrome_info["status"] == "connected"

    if chrome_ok:
        st.success(chrome_info["message"])
    else:
        st.warning(chrome_info["message"])
        if st.button("Launch Chrome", type="primary"):
            with st.spinner("Launching Chrome..."):
                status = launch_chrome()
            if status in ("launched", "already_running"):
                st.success("Chrome launched! Log into LinkedIn, then come back and search.")
                st.rerun()
            else:
                st.error("Failed: " + str(status))

    if not chrome_ok:
        st.info("LinkedIn search requires Chrome. Launch it above, log in, then search.")
        return

    # --- Search Configuration ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Keywords")
        custom_keywords = st.text_area(
            "Enter topics (one per line)",
            placeholder="technology transfer\nsynthetic biology\nindustry 4.0",
            height=120,
            key="search_keywords",
        )

        st.subheader("Domains")
        available_domains = taxonomy.domains
        selected_domains = st.multiselect(
            "Select your focus areas",
            options=available_domains,
            default=available_domains[:3],
            key="search_domains",
        )

    with col2:
        st.subheader("Settings")
        max_results = st.slider("Max results", 5, 50, 20, 5)
        min_score = st.slider("Min score", 0, 100, 30, 5, key="min_score_slider")

    # Show keywords for selected domains
    if selected_domains:
        with st.expander("Keywords for selected domains", expanded=False):
            for domain in selected_domains:
                kws = taxonomy.get_domain_keywords(domain)
                terms = [kw["term"] for kw in kws]
                count = len(kws)
                label = domain + " (" + str(count) + ")"
                st.markdown("**" + label + "**")
                preview = ", ".join(terms[:12])
                if count > 12:
                    preview += "..."
                st.caption(preview)

    # --- Search Button ---
    st.divider()
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        search_clicked = st.button("Search LinkedIn", type="primary", use_container_width=True)
    with col_btn2:
        if st.button("Clear", use_container_width=True):
            st.session_state.search_results = []
            st.rerun()

    # --- Execute Search ---
    if search_clicked:
        keywords = [k.strip() for k in custom_keywords.split("\n") if k.strip()] if custom_keywords else []

        if not keywords and not selected_domains:
            st.warning("Enter topics or select at least one domain.")
            return

        if not chrome_ok:
            st.error("Chrome is not connected. Click 'Launch Chrome' first.")
            return

        from ai_content_radar.services.linkedin import get_driver, is_logged_in, search_linkedin

        try:
            driver = get_driver()
        except Exception as e:
            st.error("Could not connect to Chrome: " + str(e))
            return

        if not is_logged_in(driver):
            st.warning("Not logged into LinkedIn. Please log into LinkedIn in the Chrome window, then try again.")
            return

        # Build search terms from keywords + domain keywords
        search_terms = list(keywords)
        if not search_terms and selected_domains:
            for domain in selected_domains:
                kws = taxonomy.get_domain_keywords(domain)
                search_terms.extend([kw["term"] for kw in kws[:3]])

        search_terms = list(dict.fromkeys(search_terms))[:10]

        # Search LinkedIn
        all_results = []
        per_query = max(5, max_results // max(len(search_terms), 1))
        for term in search_terms:
            with st.spinner("Searching: " + term + "..."):
                try:
                    posts = search_linkedin(driver, term, max_results=per_query)
                    all_results.extend(posts)
                except Exception as e:
                    st.warning("Failed for '" + term + "': " + str(e))

        # Deduplicate
        seen = set()
        unique = []
        for p in all_results:
            url = p.get("url", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(p)

        # Store in DB
        stored = 0
        dupes = 0
        for post_data in unique:
            result = db.add_post(post_data)
            if result:
                stored += 1
            else:
                dupes += 1

        if not unique:
            st.warning("No results found. Try different topics.")
            return

        # Rank
        learning_engine = LearningEngine(db)
        ranking_engine = RankingEngine(db, taxonomy, learning_engine)

        with st.spinner("Ranking posts..."):
            ranked = ranking_engine.rank_all_unranked()

        st.success(
            "Found " + str(len(unique)) + " posts (" + str(stored) + " new, "
            + str(dupes) + " duplicates), ranked " + str(len(ranked))
        )
        st.divider()

        filtered = [r for r in ranked if r["score"] >= min_score]

        if not filtered:
            st.info("No posts meet the minimum score. Try lowering it.")
            return

        st.subheader("Top " + str(len(filtered)) + " Opportunities")
        filtered.sort(key=lambda x: x["score"], reverse=True)
        st.session_state.search_results = filtered

        for i, result in enumerate(filtered[:50]):
            render_post_card(db, result, i, user_id=user_id)
