"""Comment Helper page - paste a LinkedIn post, get AI-generated comment options."""
from __future__ import annotations

import streamlit as st

from ai_content_radar.database.manager import DatabaseManager


COMMENT_STYLES = {
    "professional": "Professional & Insightful",
    "different_angle": "Different Angle",
    "question": "Question-Based",
    "counter": "Respectful Counter-Point",
    "curiosity": "Curiosity-Driven",
}


def comment_helper_page(db: DatabaseManager, user_id: int = 1) -> None:
    st.title("Comment Helper")
    st.caption("Paste a LinkedIn post and get AI-generated comment options")

    knowledge = db.get_knowledge(user_id=user_id)
    if not knowledge:
        st.warning("Set up your profile first so comments sound like you.")
        if st.button("Go to Profile"):
            st.session_state.current_page = "profile"
            st.rerun()
        return

    post_text = st.text_area(
        "Paste the LinkedIn post here",
        placeholder="Paste the full text of a LinkedIn post you want to comment on...",
        height=200,
        key="comment_post_text",
    )

    col1, col2 = st.columns(2)
    with col1:
        author_name = st.text_input("Author name (optional)", placeholder="e.g. Sarah Chen")
    with col2:
        author_title = st.text_input("Author title (optional)", placeholder="e.g. CEO at BioTech Inc")

    st.divider()

    if st.button("Generate Comments", type="primary", use_container_width=True):
        if not post_text.strip():
            st.error("Paste a LinkedIn post first.")
            return

        comments = []
        progress = st.progress(0, text="Generating comments...")

        styles = ["professional", "different_angle", "question"]
        for i, style in enumerate(styles):
            progress.progress(i / len(styles), text=f"Generating {COMMENT_STYLES[style]}...")
            try:
                comment = _generate_comment(
                    db, post_text, author_name, author_title, style, user_id=user_id
                )
                if comment:
                    comments.append((style, comment))
            except Exception as e:
                st.warning(f"Failed to generate {COMMENT_STYLES[style]}: {e}")

        progress.progress(1.0, text="Done!")
        st.session_state["generated_comments"] = comments
        st.rerun()

    if "generated_comments" in st.session_state and st.session_state["generated_comments"]:
        st.subheader("Generated Comments")
        st.info("Copy any comment below and paste it into LinkedIn.")

        for style, comment_text in st.session_state["generated_comments"]:
            label = COMMENT_STYLES.get(style, style)
            with st.expander(label, expanded=True):
                st.text_area(
                    f"comment_{style}",
                    comment_text,
                    height=120,
                    disabled=True,
                    key=f"disp_{style}",
                )
                st.caption(f"{len(comment_text.split())} words")

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
        lines.append(f"{k.category}: {k.key} = {k.value}")
    return "\n".join(lines)


def _generate_comment(
    db: DatabaseManager,
    post_text: str,
    author_name: str,
    author_title: str,
    style: str,
    user_id: int = 1,
) -> str:
    from ai_content_radar.config.settings import config

    context = _build_context(db, user_id=user_id)

    author_line = ""
    if author_name:
        author_line = f"\nAuthor: {author_name}"
        if author_title:
            author_line += f", {author_title}"

    style_instructions = {
        "professional": """Write a professional, insightful comment that:
- Adds a unique perspective or insight from YOUR work
- Connects ideas from adjacent fields
- References specific elements from the post
- Sounds like a real professional, not a bot
- Shows genuine engagement with the topic""",

        "different_angle": """Write a comment that takes a DIFFERENT angle:
- Focus on implementation challenges, practical implications, or overlooked aspects
- Connect to real-world experience or adjacent problems
- Be specific, not generic
- Bring something the original post didn't cover""",

        "question": """Write a QUESTION-BASED comment that:
- Asks a thoughtful, specific question that demonstrates genuine interest
- Shows you understand the topic deeply
- References specific points from the post
- The question should advance the conversation, not just ask for more info""",

        "counter": """Write a RESPECTFUL COUNTER-POINT comment that:
- Acknowledges the original point first
- Offers an alternative viewpoint grounded in experience or evidence
- Is constructive, not contrarian
- Adds nuance to the discussion""",

        "curiosity": """Write a CURIOSITY-DRIVEN comment that:
- Expresses genuine intellectual curiosity
- Connects to adjacent fields or unexpected intersections
- Explores implications or "what if" scenarios
- References your own observations or explorations""",
    }

    style_inst = style_instructions.get(style, style_instructions["professional"])

    prompt = f"""Write a LinkedIn comment for this post.
{author_line}

Content:
{post_text[:2000]}

YOUR BACKGROUND AND EXPERTISE:
{context}

INSTRUCTIONS:
{style_inst}

RULES:
- Maximum 100 words
- NEVER start with: "Great post", "Interesting", "Thanks for sharing", "Valuable insights", "Excellent", "Love this", "So true", "Well said", "Brilliant"
- NEVER summarize the post
- Add YOUR unique perspective based on YOUR work
- Sound like a real professional, not a content marketing bot
- Use natural, professional language
- Reference specific elements from the post

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
