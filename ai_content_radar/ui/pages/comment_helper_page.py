"""Comment Helper page - paste a LinkedIn post, get AI-generated comment options."""
from __future__ import annotations

import re

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


COMMENT_TYPES = {
    "professional": "Professional & Insightful",
    "alternative": "Different Angle",
    "question": "Question-Based",
    "counter_perspective": "Counter-Perspective",
    "curiosity": "Curiosity-Driven",
}


def comment_helper_page(db: DatabaseManager, user_id: int = 1) -> None:
    st.title("Comment Helper")
    st.caption("Paste a LinkedIn post and get AI-generated comment options")

    knowledge = db.get_knowledge(user_id=user_id)
    if not knowledge:
        st.warning(
            "Add your context first so comments sound like YOU. "
            "Go to **My Context** in the sidebar."
        )

    st.divider()

    post_text = st.text_area(
        "Paste the LinkedIn post text here",
        placeholder="Paste the full text of a LinkedIn post you want to comment on...",
        height=200,
        key="comment_post_text",
    )

    col1, col2 = st.columns(2)
    with col1:
        author_name = st.text_input("Author name (optional)", placeholder="e.g. Sarah Chen", key="comment_author")
    with col2:
        author_title = st.text_input("Author title (optional)", placeholder="e.g. CEO at BioTech Inc", key="comment_title")

    comment_type = st.selectbox(
        "Comment style",
        options=list(COMMENT_TYPES.keys()),
        format_func=lambda x: COMMENT_TYPES[x],
        key="comment_type",
    )

    st.divider()

    if st.button("Generate Comments", type="primary", use_container_width=True):
        if not post_text.strip():
            st.error("Paste a LinkedIn post first.")
            return

        comments = []
        progress = st.progress(0, text="Generating comments...")

        for i, ctype in enumerate(["professional", "alternative", "question"]):
            progress.progress((i) / 3, text=f"Generating {COMMENT_TYPES[ctype]}...")
            try:
                comment = _generate_comment(
                    db, post_text, author_name, author_title,
                    ctype, user_id=user_id,
                )
                if comment:
                    comments.append((ctype, comment))
            except Exception as e:
                st.warning(f"Failed to generate {COMMENT_TYPES[ctype]}: {e}")

        progress.progress(1.0, text="Done!")
        st.session_state["generated_comments"] = comments
        st.rerun()

    if "generated_comments" in st.session_state and st.session_state["generated_comments"]:
        st.subheader("Generated Comments")
        st.info("Copy any comment below and paste it into LinkedIn.")

        for ctype, comment_text in st.session_state["generated_comments"]:
            label = COMMENT_TYPES.get(ctype, ctype)
            with st.expander(label, expanded=True):
                st.text_area(
                    f"comment_{ctype}",
                    comment_text,
                    height=120,
                    disabled=True,
                    key=f"disp_comment_{ctype}",
                )
                st.caption(str(len(comment_text.split())) + " words")

        st.divider()
        if st.button("Generate Different Comments", use_container_width=True):
            del st.session_state["generated_comments"]
            st.rerun()


def _build_context(db: DatabaseManager, user_id: int = 1) -> str:
    knowledge = db.get_knowledge(user_id=user_id)
    if not knowledge:
        return "No personal context available."
    lines = []
    for k in knowledge:
        lines.append(k.category + ": " + k.key + " = " + k.value)
    return "\n".join(lines)


def _generate_comment(
    db: DatabaseManager,
    post_text: str,
    author_name: str,
    author_title: str,
    comment_type: str,
    user_id: int = 1,
) -> str:
    from ai_content_radar.config.settings import config

    context = _build_context(db, user_id=user_id)

    author_line = ""
    if author_name:
        author_line = "\nAuthor: " + author_name
        if author_title:
            author_line += ", " + author_title

    type_instructions = {
        "professional": """Write a professional, insightful comment that:
- Adds a unique perspective or insight from your work
- Connects ideas from adjacent fields
- References specific elements from the post
- Sounds like a real professional, not a bot""",
        "alternative": """Write a comment that takes a DIFFERENT angle:
- Focus on implementation, challenges, or implications
- Connect to real-world experience or adjacent problems
- Be specific, not generic
- Sound authentic""",
        "question": """Write a QUESTION-BASED comment that:
- Asks a thoughtful, specific question that demonstrates genuine interest
- Shows you understand the topic
- References specific points from the post
- Connects to your own work or observations""",
        "counter_perspective": """Write a COUNTER-PERSPECTIVE comment that:
- Respectfully offers an alternative viewpoint
- Acknowledges the original point before offering your perspective
- Grounds your counter-point in experience or evidence
- Is constructive, not contrarian""",
        "curiosity": """Write a CURIOSITY-DRIVEN comment that:
- Expresses genuine intellectual curiosity
- Connects to adjacent fields or unexpected intersections
- Asks "what if" or explores implications
- References your own explorations or observations""",
    }

    type_inst = type_instructions.get(comment_type, type_instructions["professional"])

    prompt = """Write a LinkedIn comment for this post.

POST:""" + author_line + """

Content:
""" + post_text[:2000] + """

YOUR BACKGROUND AND EXPERTISE:
""" + context + """

INSTRUCTIONS:
""" + type_inst + """

RULES:
- Maximum 120 words
- Never summarize the post
- Never use: "Great post", "Interesting", "Thanks for sharing", "Valuable insights", "Excellent", "Love this", "So true"
- Add a unique perspective or insight from your work
- Sound like a real professional, not a content marketing bot
- Use natural, professional language

Generate ONLY the comment text, nothing else."""

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
