"""Post page - AI writes LinkedIn posts based on your expertise and context."""
from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


def post_page(db: DatabaseManager, user_id: int = 1) -> None:
    st.title("Create Post")

    # --- Chrome status ---
    from ai_content_radar.services.linkedin import get_status, launch_chrome, _is_cdp_running
    chrome_ok = _is_cdp_running()
    chrome_info = get_status()

    if chrome_ok:
        st.success(chrome_info["message"])
    else:
        st.warning(chrome_info["message"])
        if st.button("Launch Chrome", type="primary"):
            with st.spinner("Launching Chrome..."):
                status = launch_chrome()
            if status in ("launched", "already_running"):
                st.success("Chrome launched! Log into LinkedIn there.")
                st.rerun()
            else:
                st.error("Failed: " + str(status))

    # --- Personal context ---
    knowledge = db.get_knowledge(user_id=user_id)
    if not knowledge:
        st.warning(
            "Add your context first so posts sound like YOU. "
            "Go to **My Context** in the sidebar."
        )
    else:
        with st.expander("Your context (" + str(len(knowledge)) + " entries)", expanded=False):
            for k in knowledge:
                st.caption(k.category + ": " + k.key + " = " + k.value[:120])

    st.divider()

    # --- Topic (optional) ---
    st.subheader("What should the post be about?")
    topic = st.text_input(
        "Topic or idea (optional - leave blank for AI to pick based on your expertise)",
        placeholder="e.g. Why tech transfer in biotech is broken, or why AI won't replace wet labs",
        key="post_topic",
    )

    tone = st.selectbox("Tone", [
        "Professional & insightful",
        "Casual & approachable",
        "Technical & detailed",
        "Thought leadership",
    ])

    # --- Photos ---
    photos = st.file_uploader(
        "Photos (optional)",
        type=["png", "jpg", "jpeg", "gif"],
        accept_multiple_files=True,
        key="post_photos",
    )

    # --- Generate ---
    st.divider()
    col1, col2 = st.columns([1, 4])
    with col1:
        generate_clicked = st.button("Generate Post", type="primary", use_container_width=True)

    if generate_clicked:
        if not knowledge:
            st.error("Add your context in **My Context** first.")
        else:
            with st.spinner("Writing your post..."):
                try:
                    post_text = _generate_post(db, topic, tone, user_id=user_id)
                    st.session_state["generated_post"] = post_text
                except Exception as e:
                    st.error("Failed: " + str(e))

    # --- Preview & Post ---
    if "generated_post" in st.session_state:
        st.subheader("Preview & Edit")
        edited = st.text_area(
            "Edit before posting",
            value=st.session_state["generated_post"],
            height=300,
            key="edit_post",
        )
        st.caption(str(len(edited)) + " characters")

        # Save uploaded photos to temp files
        photo_paths = []
        if photos:
            for photo in photos:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(photo.name).suffix)
                tmp.write(photo.read())
                tmp.close()
                photo_paths.append(tmp.name)

        col_post, col_again = st.columns([1, 1])
        with col_post:
            if st.button("Post to LinkedIn", type="primary", use_container_width=True):
                if not chrome_ok:
                    st.error("Chrome is not connected. Launch Chrome first.")
                else:
                    _do_post(edited, photo_paths, db)
        with col_again:
            if st.button("Generate Another", use_container_width=True):
                with st.spinner("Writing..."):
                    try:
                        st.session_state["generated_post"] = _generate_post(db, topic, tone, user_id=user_id)
                        st.rerun()
                    except Exception as e:
                        st.error("Failed: " + str(e))


def _build_context(db: DatabaseManager, user_id: int = 1) -> str:
    knowledge = db.get_knowledge(user_id=user_id)
    if not knowledge:
        return "No personal context available."
    lines = []
    for k in knowledge:
        lines.append(k.category + ": " + k.key + " = " + k.value)
    return "\n".join(lines)


def _generate_post(db: DatabaseManager, topic: str, tone: str, user_id: int = 1) -> str:
    from ai_content_radar.config.settings import config

    context = _build_context(db, user_id=user_id)

    topic_line = ""
    if topic.strip():
        topic_line = "\nThe post should be about: " + topic.strip()

    prompt = """Write a LinkedIn post for this person.

THEIR BACKGROUND AND EXPERTISE:
""" + context + topic_line + """

TONE: """ + tone + """

RULES:
- Write in first person, as if this person is posting on their own LinkedIn
- 150-300 words
- Start with a hook that makes people stop scrolling
- Be specific and grounded in THEIR actual work and field
- Share a real insight, observation, or opinion — not generic fluff
- End with a question or call to action to drive engagement
- Use short paragraphs and line breaks for mobile readability
- Include 2-3 relevant hashtags at the end
- Do NOT use: "I'm excited to announce", "Thrilled to share", "I'm pleased to", "In today's fast-paced world"
- Do NOT make up projects or achievements — only reference what is in their context above
- Sound like a real person sharing a genuine perspective, not a content marketing bot

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
    raise Exception("Gemini error " + str(response.status_code) + ": " + response.text[:200])


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


def _do_post(post_text: str, photo_paths: list[str], db: DatabaseManager) -> None:
    from ai_content_radar.services.linkedin import _is_cdp_running, get_driver, create_post

    if not _is_cdp_running():
        st.error("Chrome is not connected.")
        return

    try:
        driver = get_driver()
    except Exception as e:
        st.error("Could not connect to Chrome: " + str(e))
        return

    with st.spinner("Posting to LinkedIn..."):
        result = create_post(driver, post_text, photo_paths if photo_paths else None)

    if result["success"]:
        st.success(result["message"])
        db.add_post({
            "url": "linkedin.com/feed (my post)",
            "title": "LinkedIn Post",
            "text": post_text,
            "source": "my_post",
        })
    else:
        st.error(result["message"])
