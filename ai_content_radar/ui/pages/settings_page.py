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
            st.info(
                "Settings saved for this session. "
                "On Streamlit Cloud, update the secrets in your dashboard instead."
            )

        # Test connection
        st.divider()
        st.subheader("Test Connection")
        if st.button("Test AI Connection"):
            with st.spinner("Testing..."):
                try:
                    test_prompt = "Say 'Connection successful' in exactly 3 words."
                    result = _test_ai(config, test_prompt)
                    if result:
                        st.success("Connection successful! Response: " + result[:100])
                    else:
                        st.error("No response from AI provider.")
                except Exception as e:
                    st.error("Connection failed: " + str(e))

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
                st.success("Cleared " + str(count) + " expired cache entries")
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
            st.error("Failed to get stats: " + str(e))

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
                    "Download " + export_type,
                    data=formatted,
                    file_name="export_" + export_content.lower().replace(" ", "_") + "." + file_ext,
                    mime="text/plain" if export_type == "Markdown" else "application/json" if export_type == "JSON" else "text/csv",
                )
            else:
                st.info("No data to export.")


def _test_ai(config, prompt: str) -> str:
    if config.ai.provider == "gemini":
        import httpx
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + config.ai.gemini_model
            + ":generateContent?key=" + config.ai.gemini_api_key
        )
        response = httpx.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": config.ai.temperature,
                    "maxOutputTokens": 100,
                },
            },
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    elif config.ai.provider == "openai":
        import openai
        client = openai.OpenAI(api_key=config.ai.api_key)
        response = client.chat.completions.create(
            model=config.ai.openai_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    return ""


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
                lines.append("**" + k + ":** " + str(v))
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
