"""Search History page - view and rerun past searches."""
from __future__ import annotations

import json

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


def history_page(db: DatabaseManager, user_id: int = 1) -> None:
    st.title("Search History")
    st.caption("View and rerun past searches")

    history = db.get_search_history(limit=50)

    if not history:
        st.info("No search history yet. Run your first search from the Find Opportunities page!")
        return

    for entry in history:
        domains = json.loads(entry.domains) if entry.domains else []
        keywords = json.loads(entry.keywords_used) if entry.keywords_used else []

        with st.expander(
            f"Search: {entry.query[:60]} | {entry.results_count} results | Avg score: {entry.avg_score:.1f}"
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Query:** {entry.query}")
                st.markdown(f"**Domains:** {', '.join(domains) if domains else 'N/A'}")
                st.markdown(f"**Keywords:** {', '.join(keywords[:10]) if keywords else 'N/A'}")

            with col2:
                st.metric("Results", entry.results_count)
                st.metric("Avg Score", f"{entry.avg_score:.1f}")
                st.metric("Duration", f"{entry.duration_seconds:.1f}s")

            st.caption(f"Searched at: {entry.searched_at.strftime('%Y-%m-%d %H:%M') if entry.searched_at else 'Unknown'}")

            if st.button("Rerun Search", key=f"rerun_{entry.id}"):
                st.session_state.current_page = "search"
                st.rerun()

    st.divider()
    st.subheader("Export History")

    if st.button("Export as JSON"):
        export_data = []
        for entry in history:
            export_data.append({
                "query": entry.query,
                "domains": json.loads(entry.domains) if entry.domains else [],
                "keywords": json.loads(entry.keywords_used) if entry.keywords_used else [],
                "results_count": entry.results_count,
                "avg_score": entry.avg_score,
                "duration_seconds": entry.duration_seconds,
                "searched_at": entry.searched_at.isoformat() if entry.searched_at else None,
            })
        st.download_button(
            "Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name="search_history.json",
            mime="application/json",
        )
