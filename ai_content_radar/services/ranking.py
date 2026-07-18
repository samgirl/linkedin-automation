"""Ranking engine with explainable scoring."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.taxonomy import KeywordTaxonomy

logger = logging.getLogger(__name__)


class RankingEngine:
    """Ranks posts based on multiple factors with explainable output."""

    WEIGHTS = {
        "keyword_match": 0.25,
        "quality": 0.20,
        "freshness": 0.15,
        "engagement": 0.10,
        "opportunity": 0.15,
        "novelty": 0.10,
        "relevance": 0.05,
    }

    def __init__(self, db: DatabaseManager, taxonomy: KeywordTaxonomy, learning_engine: Optional[Any] = None):
        self.db = db
        self.taxonomy = taxonomy
        self._learning_engine = learning_engine

    def rank_post(self, post_id: int) -> Optional[dict[str, Any]]:
        post = self.db.get_post_by_id(post_id)
        if not post:
            return None

        scores = {
            "keyword_match_score": self._score_keyword_match(post),
            "quality_score": self._score_quality(post),
            "freshness_score": self._score_freshness(post),
            "engagement_score": self._score_engagement(post),
            "opportunity_score": self._score_opportunity(post),
            "novelty_score": self._score_novelty(post),
            "relevance_score": self._score_relevance(post),
        }

        total_score = sum(
            scores[f"{k}_score"] * self.WEIGHTS[k]
            for k in self.WEIGHTS
            if f"{k}_score" in scores
        )

        # Apply personalized boost from learning system
        personalization_boost = 0.0
        if self._learning_engine:
            personalization_boost = self._learning_engine.get_personalized_boost(post)

        final_score = min(100, max(0, int(total_score + personalization_boost)))

        reason = self._generate_reason(post, scores, final_score)
        if personalization_boost > 5:
            reason += f" (+{personalization_boost:.0f} personalization boost)"

        ranking_data = {
            "post_id": post_id,
            "score": final_score,
            "reason": reason,
            **scores,
        }

        self.db.add_ranking(ranking_data)
        return ranking_data

    def rank_all_unranked(self) -> list[dict[str, Any]]:
        unranked = self.db.get_unranked_posts()
        results = []
        for post in unranked:
            result = self.rank_post(post.id)
            if result:
                result["post"] = post
                result["ranking"] = self.db.get_ranking_for_post(post.id)
                results.append(result)
        results.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"Ranked {len(results)} posts")
        return results

    def get_ranked_posts(self, min_score: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        ranked = self.db.get_ranked_posts(min_score=min_score, limit=limit)
        results = []
        for post, ranking in ranked:
            results.append({
                "post": post,
                "ranking": ranking,
            })
        return results

    def _score_keyword_match(self, post: Any) -> float:
        text = f"{post.title} {post.text}".lower()
        hashtags = json.loads(post.hashtags) if post.hashtags else []
        tech = json.loads(post.mentioned_tech) if post.mentioned_tech else []
        orgs = json.loads(post.mentioned_orgs) if post.mentioned_orgs else []

        all_keywords = self.taxonomy.get_all_keywords_flat()
        matched_count = 0
        weighted_score = 0.0

        for kw in all_keywords:
            term = kw["term"].lower()
            weight = kw.get("weight", 1.0)

            if term in text:
                matched_count += 1
                weighted_score += weight
                self.db.add_keyword_ranking(
                    post.id, 0, weight, "text"
                )
            elif term in " ".join(hashtags).lower():
                matched_count += 1
                weighted_score += weight * 1.2
            elif any(term in t.lower() for t in tech + orgs):
                matched_count += 1
                weighted_score += weight * 1.1

            for alias in kw.get("aliases", []):
                if alias.lower() in text:
                    matched_count += 1
                    weighted_score += weight * 0.9

        if matched_count == 0:
            return 0.0

        density = min(matched_count / 5.0, 1.0)
        weight_factor = min(weighted_score / max(matched_count, 1) / 1.2, 1.0)
        return (density * 0.6 + weight_factor * 0.4) * 100

    def _score_quality(self, post: Any) -> float:
        text = post.text or ""
        text_length = len(text)

        length_score = 0.0
        if text_length > 500:
            length_score = 100
        elif text_length > 200:
            length_score = 70
        elif text_length > 100:
            length_score = 40
        else:
            length_score = 10

        technical_indicators = [
            "research", "study", "data", "evidence", "analysis",
            "methodology", "framework", "implementation", "results",
            "innovation", "patent", "technology", "process",
            "engineering", "science", "biotech", "manufacturing",
        ]
        tech_count = sum(1 for word in technical_indicators if word.lower() in text.lower())
        tech_score = min(tech_count / 5, 1.0) * 100

        questions = text.count("?")
        question_score = min(questions / 3, 1.0) * 80

        has_hashtags = len(json.loads(post.hashtags) if post.hashtags else []) > 0
        has_media = bool(json.loads(post.media_images) if post.media_images else [])

        structure_score = 0
        if has_hashtags:
            structure_score += 30
        if has_media:
            structure_score += 20
        if "\n" in text:
            structure_score += 20
        if any(c in text for c in ["•", "-", "1.", "2."]):
            structure_score += 15

        return (
            length_score * 0.3
            + tech_score * 0.3
            + question_score * 0.2
            + structure_score * 0.2
        )

    def _score_freshness(self, post: Any) -> float:
        if not post.date_posted:
            return 50.0

        now = datetime.utcnow()
        posted = post.date_posted
        if isinstance(posted, str):
            try:
                posted = datetime.fromisoformat(posted.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, AttributeError):
                return 50.0

        age = now - posted
        hours = age.total_seconds() / 3600

        if hours < 6:
            return 100.0
        elif hours < 24:
            return 90.0
        elif hours < 48:
            return 75.0
        elif hours < 168:
            return 60.0
        elif hours < 720:
            return 40.0
        else:
            return 20.0

    def _score_engagement(self, post: Any) -> float:
        likes = post.engagement_likes or 0
        comments = post.engagement_comments or 0
        shares = post.engagement_shares or 0

        like_score = min(likes / 100, 1.0) * 40
        comment_score = min(comments / 20, 1.0) * 40
        share_score = min(shares / 10, 1.0) * 20

        return like_score + comment_score + share_score

    def _score_opportunity(self, post: Any) -> float:
        text = (post.text or "").lower()

        question_indicators = [
            "any suggestions", "how do you", "what do you think",
            "looking for", "seeking", "recommend", "advice",
            "experience with", "thoughts on", "what are",
            "does anyone", "has anyone", "can someone",
            "what's your", "how would you", "interested in",
        ]
        question_count = sum(1 for q in question_indicators if q in text)
        question_score = min(question_count / 3, 1.0) * 100

        contribution_indicators = [
            "sharing", "announce", "excited to", "just launched",
            "looking for feedback", "open to", "collaborate",
            "partnership", "join", "opportunity",
        ]
        contrib_count = sum(1 for c in contribution_indicators if c in text)
        contrib_score = min(contrib_count / 3, 1.0) * 80

        discussion_indicators = [
            "debate", "perspective", "opinion", "view",
            "differ", "contrast", "alternative", "vs",
            "future of", "trend", "prediction",
        ]
        disc_count = sum(1 for d in discussion_indicators if d in text)
        disc_score = min(disc_count / 2, 1.0) * 70

        return (question_score * 0.4 + contrib_score * 0.3 + disc_score * 0.3)

    def _score_novelty(self, post: Any) -> float:
        text = (post.text or "").lower()

        trending_terms = [
            "generative ai", "llm", "chatgpt", "gpt-4", "claude",
            "synthetic biology", "precision fermentation", "digital twin",
            "carbon credit", "net zero", "circular economy",
            "agentic ai", "rag", "fine-tuning",
        ]
        trending_count = sum(1 for t in trending_terms if t in text)
        trending_score = min(trending_count / 3, 1.0) * 60

        unique_phrases = set()
        words = text.split()
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if phrase not in unique_phrases:
                unique_phrases.add(phrase)
        diversity_score = min(len(unique_phrases) / max(len(words), 1) / 0.5, 1.0) * 40

        return trending_score + diversity_score

    def _score_relevance(self, post: Any) -> float:
        knowledge = self.db.get_knowledge()
        if not knowledge:
            return 50.0

        text = (post.text or "").lower()
        matched = 0

        for pk in knowledge:
            if pk.value.lower() in text or pk.key.lower() in text:
                matched += 1

        return min(matched / max(len(knowledge), 1) / 0.3, 1.0) * 100

    def _generate_reason(self, post: Any, scores: dict[str, float], total: int) -> str:
        reasons = []

        if scores["keyword_match_score"] > 60:
            reasons.append("Strong keyword alignment")
        elif scores["keyword_match_score"] > 30:
            reasons.append("Moderate keyword match")

        if scores["quality_score"] > 70:
            reasons.append("High-quality discussion")
        elif scores["quality_score"] > 40:
            reasons.append("Good content quality")

        if scores["freshness_score"] > 80:
            reasons.append("Very recent post")
        elif scores["freshness_score"] > 50:
            reasons.append("Recently posted")

        if scores["engagement_score"] > 60:
            reasons.append("Strong engagement")
        elif scores["engagement_score"] > 30:
            reasons.append("Active discussion")

        if scores["opportunity_score"] > 60:
            reasons.append("Excellent opportunity to contribute")
        elif scores["opportunity_score"] > 30:
            reasons.append("Good conversation potential")

        if scores["novelty_score"] > 60:
            reasons.append("Covers emerging trends")
        elif scores["novelty_score"] > 30:
            reasons.append("Relevant to current trends")

        if not reasons:
            if total >= 70:
                reasons.append("Well-rounded opportunity")
            elif total >= 50:
                reasons.append("Moderate relevance")
            else:
                reasons.append("Lower priority match")

        return ". ".join(reasons[:4]) + f" (Score: {total}/100)"
