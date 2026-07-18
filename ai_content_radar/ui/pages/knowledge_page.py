"""Knowledge Base page - manage personal context for AI."""
from __future__ import annotations

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.taxonomy import KeywordTaxonomy


CATEGORIES = {
    "project": "Current Projects",
    "industry": "Industries",
    "technology": "Technologies",
    "interest": "Research Interests",
    "background": "Professional Background",
}


def knowledge_page(db: DatabaseManager, taxonomy: KeywordTaxonomy, user_id: int = 1) -> None:
    st.title("My Context")
    st.caption("Add info about your work so AI sounds like YOU, not a bot")

    tab_add, tab_view = st.tabs(["Add Context", "View Context"])

    with tab_add:
        st.subheader("Add Context Entry")

        category = st.selectbox(
            "Category",
            options=list(CATEGORIES.keys()),
            format_func=lambda x: CATEGORIES[x],
        )

        key = st.text_input("Label", placeholder="e.g. Current Project, Core Skill, Industry")
        value = st.text_area(
            "Details",
            placeholder="e.g. Building AI tools for precision fermentation in biotech",
            height=100,
        )

        if st.button("Add", type="primary"):
            if key and value:
                db.add_knowledge(category, key, value, user_id=user_id)
                st.success("Added: " + key)
                st.rerun()
            else:
                st.warning("Fill in both fields.")

        st.divider()
        st.subheader("Quick Add")
        templates = [
            ("project", "Current Project", "Working on technology transfer for deep tech startups"),
            ("industry", "Primary Industry", "Biotechnology and synthetic biology"),
            ("technology", "Core Technology", "Precision fermentation and metabolic engineering"),
            ("interest", "Research Interest", "AI applications in agricultural biotechnology"),
            ("background", "Professional Role", "Early-career researcher in industrial biotechnology"),
            ("interest", "Watching", "Climate technology and circular economy developments"),
        ]

        cols = st.columns(2)
        for i, (cat, tpl_key, tpl_value) in enumerate(templates):
            with cols[i % 2]:
                if st.button("Add: " + tpl_key, key="tpl_" + str(i)):
                    db.add_knowledge(cat, tpl_key, tpl_value, user_id=user_id)
                    st.success("Added: " + tpl_key)
                    st.rerun()

    with tab_view:
        st.subheader("Your Context")

        selected_category = st.selectbox(
            "Filter",
            ["All"] + list(CATEGORIES.keys()),
            format_func=lambda x: CATEGORIES.get(x, x) if x != "All" else "All",
            key="view_category",
        )

        if selected_category == "All":
            entries = db.get_knowledge(user_id=user_id)
        else:
            entries = db.get_knowledge(category=selected_category, user_id=user_id)

        if not entries:
            st.info("No context yet. Add info about your work, expertise, and interests.")
            return

        for entry in entries:
            cat_label = CATEGORIES.get(entry.category, entry.category)
            with st.expander("[" + cat_label + "] " + entry.key):
                st.markdown(entry.value)
                st.caption("Weight: " + str(entry.relevance_weight))
                if st.button("Delete", key="del_know_" + str(entry.id)):
                    db.delete_knowledge(entry.id)
                    st.rerun()

        st.divider()
        st.subheader("AI Sees This")
        entries = db.get_knowledge(user_id=user_id)
        if entries:
            context = "\n".join(
                e.category + ": " + e.key + ": " + e.value
                for e in entries
            )
            st.code(context, language=None)
