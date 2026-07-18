"""Settings page - configure AI providers, models, and preferences."""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from ai_content_radar.config.settings import BASE_DIR, config
from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.taxonomy import KeywordTaxonomy


def settings_page(db: DatabaseManager, taxonomy: KeywordTaxonomy) -> None:
    st.title("Settings")
    st.caption("Configure AI Content Radar")

    tab_ai, tab_db, tab_export = st.tabs(["AI Provider", "Database", "Export"])

    # --- AI Provider Tab ---
    with tab_ai:
        st.subheader("AI Provider Configuration")

        provider = st.selectbox(
            "AI Provider",
            ["gemini", "openai", "openrouter", "ollama"],
            index=["gemini", "openai", "openrouter", "ollama"].index(config.ai.provider),
        )

        if provider == "gemini":
            api_key = st.text_input(
                "Gemini API Key (FREE at aistudio.google.com/apikey)",
                value=config.ai.gemini_api_key,
                type="password",
            )
            model = st.text_input(
                "Model",
                value=config.ai.gemini_model,
            )
        elif provider == "openai":
            api_key = st.text_input(
                "OpenAI API Key",
                value=config.ai.openai_api_key,
                type="password",
            )
            model = st.text_input(
                "Model",
                value=config.ai.openai_model,
            )
        elif provider == "openrouter":
            api_key = st.text_input(
                "OpenRouter API Key",
                value=config.ai.openrouter_api_key,
                type="password",
            )
            model = st.text_input(
                "Model",
                value=config.ai.openrouter_model,
            )
        elif provider == "ollama":
            api_key = ""
            base_url = st.text_input(
                "Ollama Base URL",
                value=config.ai.ollama_base_url,
            )
            model = st.text_input(
                "Model",
                value=config.ai.ollama_model,
            )

        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=config.ai.temperature,
                step=0.1,
            )
        with col2:
            max_tokens = st.slider(
                "Max Tokens",
                min_value=100,
                max_value=2000,
                value=config.ai.max_tokens,
                step=50,
            )

        max_comment_words = st.slider(
            "Max Comment Words",
            min_value=50,
            max_value=300,
            value=config.ai.max_comment_words,
            step=10,
        )

        if st.button("Save AI Settings", type="primary"):
            env_path = BASE_DIR / ".env"
            env_content = _read_env(env_path)

            env_content = _update_env(env_content, "AI_PROVIDER", provider)
            env_content = _update_env(env_content, "AI_TEMPERATURE", str(temperature))
            env_content = _update_env(env_content, "AI_MAX_TOKENS", str(max_tokens))
            env_content = _update_env(env_content, "MAX_COMMENT_WORDS", str(max_comment_words))

            if provider == "gemini":
                env_content = _update_env(env_content, "GEMINI_API_KEY", api_key)
                env_content = _update_env(env_content, "GEMINI_MODEL", model)
            elif provider == "openai":
                env_content = _update_env(env_content, "OPENAI_API_KEY", api_key)
                env_content = _update_env(env_content, "OPENAI_MODEL", model)
            elif provider == "openrouter":
                env_content = _update_env(env_content, "OPENROUTER_API_KEY", api_key)
                env_content = _update_env(env_content, "OPENROUTER_MODEL", model)
            elif provider == "ollama":
                env_content = _update_env(env_content, "OLLAMA_BASE_URL", base_url)
                env_content = _update_env(env_content, "OLLAMA_MODEL", model)

            env_path.write_text(env_content, encoding="utf-8")
            st.success("Settings saved! Restart the app to apply changes.")

        # Test connection
        st.divider()
        st.subheader("Test Connection")
        if st.button("Test AI Connection"):
            with st.spinner("Testing..."):
                try:
                    from ai_content_radar.ai_engine.comment_engine import CommentEngine
                    engine = CommentEngine(db)
                    test_prompt = "Say 'Connection successful' in exactly 3 words."
                    result = engine._call_ai(test_prompt)
                    if result:
                        st.success(f"Connection successful! Response: {result[:100]}")
                    else:
                        st.error("No response from AI provider.")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    # --- Database Tab ---
    with tab_db:
        st.subheader("Database Configuration")

        st.text_input("Database URL", value=config.database_url, disabled=True)

        st.divider()
        st.subheader("Database Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Expired Cache"):
                count = db.clear_expired_cache()
                st.success(f"Cleared {count} expired cache entries")
        with col2:
            if st.button("Rebuild Tables"):
                db.drop_tables()
                db.create_tables()
                st.success("Tables rebuilt")

        st.divider()
        st.subheader("Database Stats")
        try:
            analytics = db.get_analytics()
            st.json(analytics)
        except Exception as e:
            st.error(f"Failed to get stats: {e}")

    # --- Export Tab ---
    with tab_export:
        st.subheader("Export Data")

        export_type = st.selectbox(
            "Export Format",
            ["CSV", "JSON", "Markdown"],
        )

        export_content = st.selectbox(
            "Content to Export",
            ["Approved Comments", "All Posts", "Rankings", "Search History", "Knowledge Base"],
        )

        if st.button("Generate Export", type="primary"):
            data = _get_export_data(db, export_content)
            if data:
                formatted = _format_export(data, export_type)
                file_ext = export_type.lower()
                st.download_button(
                    f"Download {export_type}",
                    data=formatted,
                    file_name=f"export_{export_content.lower().replace(' ', '_')}.{file_ext}",
                    mime="text/plain" if export_type == "Markdown" else "application/json" if export_type == "JSON" else "text/csv",
                )
            else:
                st.info("No data to export.")


def _read_env(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _update_env(content: str, key: str, value: str) -> str:
    lines = content.split("\n")
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def _get_export_data(db: DatabaseManager, content_type: str) -> list[dict]:
    import json

    if content_type == "Approved Comments":
        actions = db.get_actions(action_type="approved", limit=1000)
        data = []
        for action in actions:
            post = db.get_post_by_id(action.post_id)
            comments = db.get_comments_for_post(action.post_id)
            if post and comments:
                data.append({
                    "url": post.url,
                    "author": post.author_rel.name if post.author_rel else "",
                    "post_text": post.text[:200],
                    "comment": comments[0].text if comments else "",
                    "score": post.ranking.score if hasattr(post, 'ranking') and post.ranking else 0,
                })
        return data
    elif content_type == "All Posts":
        posts = db.get_posts(limit=1000)
        return [{"url": p.url, "title": p.title, "text": p.text[:200]} for p in posts]
    elif content_type == "Rankings":
        ranked = db.get_ranked_posts(min_score=0, limit=1000)
        return [{"url": p.url, "score": r.score, "reason": r.reason} for p, r in ranked]
    elif content_type == "Search History":
        history = db.get_search_history(limit=100)
        return [{"query": h.query, "results": h.results_count, "avg_score": h.avg_score} for h in history]
    elif content_type == "Knowledge Base":
        knowledge = db.get_knowledge()
        return [{"category": k.category, "key": k.key, "value": k.value} for k in knowledge]
    return []


def _format_export(data: list[dict], fmt: str) -> str:
    import json

    if fmt == "JSON":
        return json.dumps(data, indent=2)
    elif fmt == "Markdown":
        lines = []
        for item in data:
            lines.append("---")
            for k, v in item.items():
                lines.append(f"**{k}:** {v}")
            lines.append("")
        return "\n".join(lines)
    elif fmt == "CSV":
        if not data:
            return ""
        headers = list(data[0].keys())
        lines = [",".join(headers)]
        for item in data:
            row = [str(item.get(h, "")).replace(",", ";") for h in headers]
            lines.append(",".join(row))
        return "\n".join(lines)
    return str(data)
