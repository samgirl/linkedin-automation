"""AI Comment Generation Engine with modular prompt system."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader

from ai_content_radar.config.settings import PROMPTS_DIR, config
from ai_content_radar.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE_DIR = PROMPTS_DIR


def _ensure_prompts() -> None:
    PROMPT_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    if not (PROMPT_TEMPLATE_DIR / "professional_comment.j2").exists():
        _create_default_prompts()


def _create_default_prompts() -> None:
    prompts = {
        "professional_comment.j2": """You are a thoughtful early-career professional working on adjacent problems in technology transfer, deep tech, and innovation.

Generate a professional comment for this LinkedIn post.

POST:
Author: {{ author_name }}, {{ author_title }} at {{ organization }}
Content: {{ post_text }}
Keywords matched: {{ matched_keywords | join(', ') }}
Domains: {{ matched_domains | join(', ') }}

PERSONAL CONTEXT:
{{ personal_context }}

RULES:
- Maximum {{ max_words }} words
- Never summarize the post
- Never use: "Great post", "Interesting", "Thanks for sharing", "Valuable insights", "Excellent", "Love this", "So true"
- Add a unique perspective or insight from your work
- Connect ideas from adjacent fields
- Be intellectually curious, not performative
- Use natural, professional language
- Reference specific elements from the post
- Sound like a real professional, not a bot

VOICE:
- Early-career professional working on related problems
- Uses phrases like "We're exploring...", "This overlaps with...", "I wonder if..."
- Does not overclaim expertise
- Avoids fake authority and certainty

Generate ONLY the comment text, nothing else.""",
        "alternative_comment.j2": """You are a thoughtful early-career professional. Generate an ALTERNATIVE comment for this LinkedIn post that takes a different angle than a standard professional response.

POST:
Author: {{ author_name }}, {{ author_title }} at {{ organization }}
Content: {{ post_text }}
Keywords matched: {{ matched_keywords | join(', ') }}
Domains: {{ matched_domains | join(', ') }}

PERSONAL CONTEXT:
{{ personal_context }}

RULES:
- Maximum {{ max_words }} words
- Take a different angle - perhaps focusing on implementation, challenges, or implications
- Never use: "Great post", "Interesting", "Thanks for sharing", "Valuable insights", "Excellent"
- Connect to real-world experience or adjacent problems
- Be specific, not generic
- Sound authentic

VOICE: Early-career professional exploring adjacent problems.

Generate ONLY the comment text.""",
        "question_comment.j2": """You are a intellectually curious professional. Generate a QUESTION-BASED comment for this LinkedIn post.

POST:
Author: {{ author_name }}, {{ author_title }} at {{ organization }}
Content: {{ post_text }}
Keywords matched: {{ matched_keywords | join(', ') }}
Domains: {{ matched_domains | join(', ') }}

PERSONAL CONTEXT:
{{ personal_context }}

RULES:
- Maximum {{ max_words }} words
- Ask a thoughtful, specific question that demonstrates genuine interest
- Never ask generic questions
- Never use: "Great post", "Interesting", "Thanks for sharing"
- The question should show you understand the topic
- Reference specific points from the post
- Connect to your own work or observations

VOICE: Professional who is genuinely curious and working on related problems.

Generate ONLY the comment text.""",
        "counter_perspective.j2": """You are a thoughtful professional who brings diverse perspectives. Generate a COUNTER-PERSPECTIVE comment for this LinkedIn post.

POST:
Author: {{ author_name }}, {{ author_title }} at {{ organization }}
Content: {{ post_text }}
Keywords matched: {{ matched_keywords | join(', ') }}
Domains: {{ matched_domains | join(', ') }}

PERSONAL CONTEXT:
{{ personal_context }}

RULES:
- Maximum {{ max_words }} words
- Respectfully offer an alternative viewpoint or raise considerations
- Never be confrontational or dismissive
- Never use: "Great post", "Interesting", "Thanks for sharing"
- Acknowledge the original point before offering your perspective
- Ground your counter-point in experience or evidence
- Be constructive, not contrarian

VOICE: Collaborative professional who values diverse thinking.

Generate ONLY the comment text.""",
        "curiosity_comment.j2": """You are a deeply curious professional. Generate a CURIOSITY-DRIVEN comment for this LinkedIn post.

POST:
Author: {{ author_name }}, {{ author_title }} at {{ organization }}
Content: {{ post_text }}
Keywords matched: {{ matched_keywords | join(', ') }}
Domains: {{ matched_domains | join(', ') }}

PERSONAL CONTEXT:
{{ personal_context }}

RULES:
- Maximum {{ max_words }} words
- Express genuine intellectual curiosity about the topic
- Connect to adjacent fields or unexpected intersections
- Never use: "Great post", "Interesting", "Thanks for sharing"
- Ask "what if" or explore implications
- Reference your own explorations or observations
- Be specific and thoughtful

VOICE: Curious professional who sees connections others might miss.

Generate ONLY the comment text.""",
    }

    for filename, content in prompts.items():
        filepath = PROMPT_TEMPLATE_DIR / filename
        filepath.write_text(content, encoding="utf-8")
    logger.info(f"Created {len(prompts)} default prompt templates")


class CommentEngine:
    """Generates comments using AI with modular prompt system."""

    COMMENT_TYPES = {
        "professional": "professional_comment.j2",
        "alternative": "alternative_comment.j2",
        "question": "question_comment.j2",
        "counter_perspective": "counter_perspective.j2",
        "curiosity": "curiosity_comment.j2",
    }

    BANNED_PHRASES = [
        "great post", "interesting", "thanks for sharing", "valuable insights",
        "excellent", "love this", "so true", "well said", "brilliant",
        "inspiring", "amazing", "fantastic", "wonderful", "awesome",
        "couldn't agree more", "spot on", "nailed it",
    ]

    def __init__(self, db: DatabaseManager):
        self.db = db
        _ensure_prompts()
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(PROMPT_TEMPLATE_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_comment(
        self,
        post_id: int,
        comment_type: str = "professional",
        custom_context: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Optional[dict[str, Any]]:
        post = self.db.get_post_by_id(post_id)
        if not post:
            logger.error(f"Post {post_id} not found")
            return None

        context = self._build_context(post, custom_context, user_id=user_id)
        prompt = self._render_prompt(comment_type, context)

        if not prompt:
            logger.error(f"Failed to render prompt for type: {comment_type}")
            return None

        response = self._call_ai(prompt)
        if not response:
            return None

        cleaned = self._clean_response(response)
        if not self._validate_comment(cleaned):
            logger.warning(f"Generated comment failed validation, attempting regeneration")
            cleaned = self._regenerate_with_constraints(cleaned, context, comment_type)
            if not cleaned:
                return None

        word_count = len(cleaned.split())

        comment_data = {
            "post_id": post_id,
            "comment_type": comment_type,
            "text": cleaned,
            "word_count": word_count,
            "model_used": config.ai.active_model,
            "prompt_version": comment_type,
            "generated_at": datetime.utcnow(),
        }

        comment = self.db.add_comment(comment_data)
        return {
            "id": comment.id,
            "text": cleaned,
            "word_count": word_count,
            "comment_type": comment_type,
        }

    def generate_all_types(
        self, post_id: int, custom_context: Optional[str] = None
    ) -> dict[str, Any]:
        results = {}
        for comment_type in self.COMMENT_TYPES:
            result = self.generate_comment(post_id, comment_type, custom_context)
            if result:
                results[comment_type] = result
        return results

    def _build_context(self, post: Any, custom_context: Optional[str] = None, user_id: Optional[int] = None) -> dict[str, Any]:
        knowledge = self.db.get_knowledge(user_id=user_id)
        knowledge_text = "\n".join(
            f"- {pk.category}: {pk.key}: {pk.value}"
            for pk in knowledge
        ) if knowledge else "No personal context available."

        hashtags = json.loads(post.hashtags) if post.hashtags else []
        tech = json.loads(post.mentioned_tech) if post.mentioned_tech else []
        orgs = json.loads(post.mentioned_orgs) if post.mentioned_orgs else []

        return {
            "author_name": post.author_rel.name if post.author_rel else "Unknown",
            "author_title": post.author_rel.title if post.author_rel else "",
            "organization": post.author_rel.organization if post.author_rel else "",
            "post_text": post.text[:2000],
            "matched_keywords": hashtags + tech,
            "matched_domains": orgs,
            "personal_context": custom_context or knowledge_text,
            "max_words": config.ai.max_comment_words,
            "post_url": post.url,
            "engagement": {
                "likes": post.engagement_likes,
                "comments": post.engagement_comments,
                "shares": post.engagement_shares,
            },
        }

    def _render_prompt(self, comment_type: str, context: dict[str, Any]) -> Optional[str]:
        template_name = self.COMMENT_TYPES.get(comment_type)
        if not template_name:
            return None

        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return None

    def _call_ai(self, prompt: str) -> Optional[str]:
        try:
            if config.ai.provider == "openai":
                return self._call_openai(prompt)
            elif config.ai.provider == "openrouter":
                return self._call_openrouter(prompt)
            elif config.ai.provider == "ollama":
                return self._call_ollama(prompt)
            elif config.ai.provider == "gemini":
                return self._call_gemini(prompt)
            else:
                logger.error(f"Unknown AI provider: {config.ai.provider}")
                return None
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return None

    def _call_openai(self, prompt: str) -> Optional[str]:
        import openai
        client = openai.OpenAI(api_key=config.ai.api_key)
        response = client.chat.completions.create(
            model=config.ai.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=config.ai.temperature,
            max_tokens=config.ai.max_tokens,
        )
        return response.choices[0].message.content

    def _call_openrouter(self, prompt: str) -> Optional[str]:
        import httpx
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.ai.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.ai.openrouter_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": config.ai.temperature,
                "max_tokens": config.ai.max_tokens,
            },
            timeout=60.0,
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        return None

    def _call_ollama(self, prompt: str) -> Optional[str]:
        import httpx
        response = httpx.post(
            f"{config.ai.ollama_base_url}/api/generate",
            json={
                "model": config.ai.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": config.ai.temperature,
                    "num_predict": config.ai.max_tokens,
                },
            },
            timeout=120.0,
        )
        if response.status_code == 200:
            return response.json().get("response", "")
        return None

    def _call_gemini(self, prompt: str) -> Optional[str]:
        import httpx
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{config.ai.gemini_model}:generateContent?key={config.ai.gemini_api_key}"
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
                    return parts[0].get("text", "")
        else:
            logger.error(f"Gemini API error {response.status_code}: {response.text[:200]}")
        return None

    def _clean_response(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r'^["\']|["\']$', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        words = text.split()
        if len(words) > config.ai.max_comment_words:
            text = " ".join(words[:config.ai.max_comment_words])
            last_period = text.rfind(".")
            if last_period > len(text) * 0.5:
                text = text[:last_period + 1]
        return text

    def _validate_comment(self, text: str) -> bool:
        if not text or len(text) < 20:
            return False
        text_lower = text.lower()
        for phrase in self.BANNED_PHRASES:
            if text_lower.startswith(phrase):
                return False
        words = text.split()
        if len(words) > config.ai.max_comment_words:
            return False
        return True

    def _regenerate_with_constraints(
        self, current: str, context: dict[str, Any], comment_type: str
    ) -> Optional[str]:
        enhanced_context = {**context}
        enhanced_context["post_text"] = (
            context["post_text"]
            + "\n\nIMPORTANT: Do NOT start with any of these phrases: "
            + ", ".join(self.BANNED_PHRASES[:5])
            + ". Start directly with your insight."
        )
        prompt = self._render_prompt(comment_type, enhanced_context)
        if prompt:
            return self._call_ai(prompt)
        return None
