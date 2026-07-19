"""Profile page - tell the AI about yourself."""
from __future__ import annotations

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


def profile_page(db: DatabaseManager, user_id: int = 1) -> None:
    st.title("My Profile")
    st.caption("Tell the AI about yourself so it writes content that sounds like you, not a bot")

    knowledge = db.get_knowledge(user_id=user_id)
    existing = {}
    for k in knowledge:
        existing[k.key] = k.value

    tab_add, tab_view = st.tabs(["Add Context", "View Context"])

    with tab_add:
        st.subheader("What do you do?")

        fields = [
            ("Role / Title", "project", "e.g. Research Scientist, Product Manager, CEO"),
            ("Industry", "industry", "e.g. Biotechnology, SaaS, Climate Tech"),
            ("Current Work", "project", "e.g. Building AI tools for drug discovery"),
            ("Key Skills", "technology", "e.g. Machine learning, fermentation, fundraising"),
            ("Interests", "interest", "e.g. Deep tech, sustainability, startup ecosystems"),
            ("Background", "background", "e.g. 5 years in biotech, previously at Google"),
            ("Writing Style", "interest", "e.g. Direct, data-driven, occasional humor"),
        ]

        for label, category, placeholder in fields:
            current_value = existing.get(label, "")
            value = st.text_area(
                label,
                value=current_value,
                placeholder=placeholder,
                height=80,
                key=f"profile_{label}",
            )
            if value.strip() and value.strip() != current_value:
                db.add_knowledge(category, label, value.strip(), user_id=user_id)

        st.divider()

        st.subheader("Quick Start Templates")
        st.caption("Click to add pre-filled examples (you can edit them after)")

        templates = [
            ("Role / Title", "project", "Research Scientist working on technology transfer"),
            ("Industry", "industry", "Biotechnology and synthetic biology"),
            ("Current Work", "project", "Building tools to accelerate lab-to-market for deep tech startups"),
            ("Key Skills", "technology", "Fermentation, metabolic engineering, patent analysis"),
            ("Interests", "interest", "AI in biotech, circular economy, startup ecosystems"),
        ]

        cols = st.columns(2)
        for i, (label, category, value) in enumerate(templates):
            with cols[i % 2]:
                if st.button(f"Add: {label}", key=f"tpl_{i}", use_container_width=True):
                    db.add_knowledge(category, label, value, user_id=user_id)
                    st.success(f"Added: {label}")
                    st.rerun()

    with tab_view:
        st.subheader("Your Context")

        if not knowledge:
            st.info("No context yet. Add info about yourself in the 'Add Context' tab.")
            return

        for entry in knowledge:
            with st.expander(f"**{entry.key}**"):
                st.markdown(entry.value)
                st.caption(f"Category: {entry.category}")
                if st.button("Delete", key=f"del_{entry.id}"):
                    db.delete_knowledge(entry.id)
                    st.rerun()

        st.divider()
        st.subheader("What the AI Sees")
        context_text = "\n".join(
            f"{e.category}: {e.key} = {e.value}" for e in knowledge
        )
        st.code(context_text, language=None)
        st.caption("This is the context that gets sent to the AI when generating content.")
