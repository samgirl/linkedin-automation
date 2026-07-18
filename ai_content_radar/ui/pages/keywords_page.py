"""Keywords page - manage keyword taxonomy."""
from __future__ import annotations

import json

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.taxonomy import KeywordTaxonomy


def keywords_page(db: DatabaseManager, taxonomy: KeywordTaxonomy) -> None:
    st.title("Keywords")
    st.caption("Manage your keyword taxonomy")

    tab_overview, tab_domain, tab_add, tab_search = st.tabs(
        ["Overview", "By Domain", "Add Custom", "Search"]
    )

    # --- Overview Tab ---
    with tab_overview:
        st.subheader("Taxonomy Overview")
        total_kw = taxonomy.total_keywords()
        total_domains = len(taxonomy.domains)
        st.metric("Total Keywords", total_kw)
        st.metric("Domains", total_domains)

        st.divider()
        for domain in taxonomy.domains:
            keywords = taxonomy.get_domain_keywords(domain)
            with st.expander(f"{domain} ({len(keywords)} keywords)"):
                for kw in keywords:
                    aliases = kw.get("aliases", [])
                    synonyms = kw.get("synonyms", [])
                    weight = kw.get("weight", 1.0)

                    col_term, col_weight, col_delete = st.columns([4, 1, 1])
                    with col_term:
                        st.markdown(f"**{kw['term']}** (weight: {weight})")
                        if aliases:
                            st.caption(f"Aliases: {', '.join(aliases)}")
                        if synonyms:
                            st.caption(f"Synonyms: {', '.join(synonyms)}")
                    with col_weight:
                        new_weight = st.number_input(
                            "Weight",
                            min_value=0.0,
                            max_value=5.0,
                            value=weight,
                            step=0.1,
                            key=f"weight_{domain}_{kw['term']}",
                            label_visibility="collapsed",
                        )
                        if new_weight != weight:
                            taxonomy.add_keyword(domain, kw["term"], weight=new_weight)
                            st.rerun()
                    with col_delete:
                        if st.button("Remove", key=f"del_{domain}_{kw['term']}"):
                            taxonomy.remove_keyword(domain, kw["term"])
                            st.rerun()

    # --- By Domain Tab ---
    with tab_domain:
        st.subheader("Filter by Domain")
        selected_domain = st.selectbox("Select domain", taxonomy.domains, key="domain_filter")

        if selected_domain:
            keywords = taxonomy.get_domain_keywords(selected_domain)
            st.caption(f"{len(keywords)} keywords in {selected_domain}")

            for kw in keywords:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"- **{kw['term']}** (weight: {kw.get('weight', 1.0)})")
                with col2:
                    if st.button("x", key=f"rm_{selected_domain}_{kw['term']}"):
                        taxonomy.remove_keyword(selected_domain, kw["term"])
                        st.rerun()

    # --- Add Custom Tab ---
    with tab_add:
        st.subheader("Add Custom Keyword")

        add_domain = st.selectbox("Domain", taxonomy.domains + ["Custom Domain"], key="add_domain")
        if add_domain == "Custom Domain":
            add_domain = st.text_input("Enter new domain name", key="custom_domain_name")

        add_term = st.text_input("Keyword term", key="add_term")
        add_weight = st.slider("Weight", 0.0, 5.0, 1.0, 0.1, key="add_weight")
        add_aliases = st.text_input("Aliases (comma-separated)", key="add_aliases")
        add_synonyms = st.text_input("Synonyms (comma-separated)", key="add_synonyms")

        if st.button("Add Keyword", type="primary", key="add_kw_btn"):
            if add_term and add_domain:
                aliases = [a.strip() for a in add_aliases.split(",") if a.strip()]
                synonyms = [s.strip() for s in add_synonyms.split(",") if s.strip()]
                taxonomy.add_keyword(add_domain, add_term, add_weight, aliases, synonyms)
                db.add_keyword(add_term, add_domain, add_weight, is_custom=True, aliases=aliases, synonyms=synonyms)
                st.success(f"Added '{add_term}' to {add_domain}")
                st.rerun()
            else:
                st.warning("Please enter a keyword term and domain.")

    # --- Search Tab ---
    with tab_search:
        st.subheader("Search Keywords")
        search_query = st.text_input("Search", key="kw_search")
        if search_query:
            results = taxonomy.search(search_query)
            if results:
                st.success(f"Found {len(results)} matches")
                for kw in results:
                    st.markdown(f"- **{kw['term']}** in {kw['domain']} (weight: {kw.get('weight', 1.0)})")
            else:
                st.info("No matches found.")
