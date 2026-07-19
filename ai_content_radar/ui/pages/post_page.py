"""Post page - AI writes LinkedIn posts based on your expertise."""
from __future__ import annotations

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


def post_page(db: DatabaseManager, user_id: int = 1) -> None:
    st.title("Create Post")

    knowledge = db.get_knowledge(user_id=user_id)
    if not knowledge:
        st.warning("Set up your profile first so posts sound like you.")
        if st.button("Go to Profile"):
            st.session_state.current_page = "profile"
            st.rerun()
        return

    with st.expander("Your context", expanded=False):
        for k in knowledge:
            st.caption(f"**{k.key}**: {k.value[:150]}")

    st.divider()

    topic = st.text_area(
        "What should the post be about?",
        placeholder="e.g. Why most tech transfer offices fail at commercialization",
        height=100,
        key="post_topic",
    )

    col1, col2 = st.columns(2)
    with col1:
        tone = st.selectbox("Tone", [
            "Professional & insightful",
            "Casual & approachable",
            "Technical & detailed",
            "Thought leadership",
            "Contrarian / hot take",
        ])
    with col2:
        length = st.selectbox("Length", [
            "Short (100-150 words)",
            "Medium (150-250 words)",
            "Long (250-400 words)",
        ])

    st.divider()

    if st.button("Generate Post", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Enter a topic first.")
            return
        with st.spinner("Writing your post..."):
            try:
                post_text = _generate_post(db, topic, tone, length, user_id=user_id)
                st.session_state["generated_post"] = post_text
            except Exception as e:
                st.error(f"Failed: {e}")

    if "generated_post" in st.session_state:
        st.subheader("Your Post")
        edited = st.text_area(
            "Edit before copying",
            value=st.session_state["generated_post"],
            height=350,
            key="edit_post",
        )
        st.caption(f"{len(edited)} characters, ~{len(edited.split())} words")

        st.code(edited, language=None)
        st.info("Copy the text above and paste it into LinkedIn.")

        if st.button("Generate Another", use_container_width=True):
            with st.spinner("Writing..."):
                try:
                    st.session_state["generated_post"] = _generate_post(
                        db, topic, tone, length, user_id=user_id
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")


def _build_context(db: DatabaseManager, user_id: int = 1) -> str:
    knowledge = db.get_knowledge(user_id=user_id)
    if not knowledge:
        return "No personal context available."
    lines = []
    for k in knowledge:
        lines.append(f"{k.category}: {k.key} = {k.value}")
    return "\n".join(lines)


def _generate_post(db: DatabaseManager, topic: str, tone: str, length: str, user_id: int = 1) -> str:
    from ai_content_radar.config.settings import config

    context = _build_context(db, user_id=user_id)

    if "Short" in length:
        word_count = "100-150"
    elif "Long" in length:
        word_count = "250-400"
    else:
        word_count = "150-250"

    prompt = f"""Write a LinkedIn post for this person.

THEIR BACKGROUND:
{context}

TOPIC: {topic.strip()}

TONE: {tone}
LENGTH: {word_count} words

RULES:
- Write in first person, as if THEY are posting on THEIR LinkedIn
- Start with a hook that makes people stop scrolling (question, bold statement, surprising fact)
- Be specific and grounded in THEIR actual work and field
- Share a real insight, observation, or opinion - not generic fluff
- Use short paragraphs and line breaks for mobile readability
- End with a question or call to action to drive engagement
- Include 3-5 relevant hashtags at the end
- NEVER use: "I'm excited to announce", "Thrilled to share", "I'm pleased to", "In today's fast-paced world", "Let's dive in", "Here's the thing"
- NEVER make up projects or achievements - only reference what is in their context
- Sound like a real person sharing a genuine perspective, not a content marketing bot
- NO emojis in the post body (hashtags only)

Generate ONLY the post text, nothing else."""

    return _call_ai(config, prompt)


def _call_ai(config, prompt: str) -> str:
    if config.ai.provider == "gemini":
        return _call_gemini(config, prompt)
    elif config.ai.provider == "openai":
        return _call_openai(config, prompt)
    else:
        return _call_gemini(config, prompt)


def _call_gemini(config, prompt: str) -> str:
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
                "maxOutputTokens": config.ai.max_tokens,
            },
        },
        timeout=60.0,
    )
    if response.status_code == 200:
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()
    raise Exception(f"Gemini error {response.status_code}: {response.text[:200]}")


def _call_openai(config, prompt: str) -> str:
    import openai
    client = openai.OpenAI(api_key=config.ai.api_key)
    response = client.chat.completions.create(
        model=config.ai.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=config.ai.temperature,
        max_tokens=config.ai.max_tokens,
    )
    return response.choices[0].message.content.strip()
