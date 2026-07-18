"""Learning system - tracks user actions and builds preference model."""
from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Optional

from ai_content_radar.database.manager import DatabaseManager
from ai_content_radar.services.embeddings import (
    EmbeddingStore,
    cosine_similarity,
    generate_embedding,
    generate_embeddings_batch,
)

logger = logging.getLogger(__name__)


class LearningEngine:
    """Learns user preferences from actions and improves ranking over time."""

    ACTION_WEIGHTS = {
        "approved": 1.0,
        "favorite": 1.5,
        "copied": 1.2,
        "edited": 0.8,
        "rejected": -0.8,
        "ignored": -0.3,
        "unfavorite": -0.5,
    }

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.embedding_store = EmbeddingStore(db)

    def record_action(self, post_id: int, action: str, comment_id: Optional[int] = None, notes: str = "") -> dict[str, Any]:
        """Record a user action and update preference model."""
        self.db.record_action(post_id, action, comment_id, notes)
        self.db.record_learning_event(
            event_type=action,
            post_id=post_id,
            metadata_json={"comment_id": comment_id},
        )

        post = self.db.get_post_by_id(post_id)
        if post:
            self._update_preferences(post, action)

        stats = self.get_preference_summary()
        logger.info(f"Recorded action '{action}' for post {post_id}. Preferences updated.")
        return stats

    def _update_preferences(self, post: Any, action: str) -> None:
        """Update the preference model based on an action."""
        weight = self.ACTION_WEIGHTS.get(action, 0.0)
        if weight == 0:
            return

        text = f"{post.title or ''} {post.text}"
        embedding = generate_embedding(text)
        if embedding:
            key = f"post:{post.id}"
            self.embedding_store.store(key, embedding)

        self._update_keyword_preferences(post, weight)
        self._update_domain_preferences(post, weight)
        self._update_author_preferences(post, weight)

    def _update_keyword_preferences(self, post: Any, weight: float) -> None:
        """Adjust keyword weights based on user actions."""
        hashtags = json.loads(post.hashtags) if post.hashtags else []
        tech = json.loads(post.mentioned_tech) if post.mentioned_tech else []

        all_terms = hashtags + tech
        for term in all_terms:
            self.db.record_learning_event(
                event_type="keyword_preference",
                keyword=term,
                score_delta=weight,
                metadata_json={"term": term},
            )

    def _update_domain_preferences(self, post: Any, weight: float) -> None:
        """Adjust domain preferences based on user actions."""
        from ai_content_radar.services.taxonomy import KeywordTaxonomy
        taxonomy = KeywordTaxonomy()
        text = f"{post.title or ''} {post.text}".lower()

        for domain in taxonomy.domains:
            keywords = taxonomy.get_domain_keywords(domain)
            matched = any(kw["term"].lower() in text for kw in keywords)
            if matched:
                self.db.record_learning_event(
                    event_type="domain_preference",
                    domain=domain,
                    score_delta=weight,
                )

    def _update_author_preferences(self, post: Any, weight: float) -> None:
        """Track author quality based on user actions."""
        if post.author_rel:
            post.author_rel.quality_score = min(1.0, max(0.0,
                post.author_rel.quality_score + weight * 0.1
            ))
            post.author_rel.post_count += 1

    def get_preference_summary(self) -> dict[str, Any]:
        """Get a summary of learned preferences."""
        stats = self.db.get_learning_stats()
        keyword_prefs = self._get_keyword_preferences()
        domain_prefs = self._get_domain_preferences()
        author_prefs = self._get_author_preferences()

        return {
            "total_actions": stats["total_actions"],
            "approval_rate": stats["approval_rate"],
            "top_keywords": keyword_prefs[:10],
            "top_domains": domain_prefs[:10],
            "top_authors": author_prefs[:10],
            "embedding_count": len(self.embedding_store.get_all()),
        }

    def _get_keyword_preferences(self) -> list[tuple[str, float]]:
        """Get ranked keyword preferences from learning events."""
        from sqlalchemy import func
        with self.db.session() as s:
            from ai_content_radar.models.database import LearningEvent
            results = (
                s.query(LearningEvent.keyword, func.sum(LearningEvent.score_delta))
                .filter(LearningEvent.event_type == "keyword_preference")
                .filter(LearningEvent.keyword.isnot(None))
                .group_by(LearningEvent.keyword)
                .order_by(func.sum(LearningEvent.score_delta).desc())
                .limit(50)
                .all()
            )
            return [(kw, score) for kw, score in results if score > 0]

    def _get_domain_preferences(self) -> list[tuple[str, float]]:
        """Get ranked domain preferences from learning events."""
        from sqlalchemy import func
        with self.db.session() as s:
            from ai_content_radar.models.database import LearningEvent
            results = (
                s.query(LearningEvent.domain, func.sum(LearningEvent.score_delta))
                .filter(LearningEvent.event_type == "domain_preference")
                .filter(LearningEvent.domain.isnot(None))
                .group_by(LearningEvent.domain)
                .order_by(func.sum(LearningEvent.score_delta).desc())
                .limit(20)
                .all()
            )
            return [(dom, score) for dom, score in results if score > 0]

    def _get_author_preferences(self) -> list[tuple[str, float]]:
        """Get ranked author preferences."""
        from sqlalchemy import func
        with self.db.session() as s:
            from ai_content_radar.models.database import Author, UserAction
            results = (
                s.query(Author.name, func.count(UserAction.id))
                .join(UserAction, Author.id == UserAction.post_id)
                .filter(UserAction.action.in_(["approved", "favorite", "copied"]))
                .group_by(Author.name)
                .order_by(func.count(UserAction.id).desc())
                .limit(20)
                .all()
            )
            return results

    def get_similar_posts(self, post_id: int, top_k: int = 5) -> list[tuple[int, float]]:
        """Find posts similar to the given post based on embeddings."""
        query_embedding = self.embedding_store.get(f"post:{post_id}")
        if not query_embedding:
            post = self.db.get_post_by_id(post_id)
            if post:
                text = f"{post.title or ''} {post.text}"
                query_embedding = generate_embedding(text)
                if query_embedding:
                    self.embedding_store.store(f"post:{post_id}", query_embedding)

        if not query_embedding:
            return []

        candidates = [
            (key, emb)
            for key, emb in self.embedding_store.get_all()
            if key.startswith("post:") and key != f"post:{post_id}"
        ]

        if not candidates:
            return []

        results = []
        for key, emb in candidates:
            sim = cosine_similarity(query_embedding, emb)
            try:
                pid = int(key.split(":")[1])
                results.append((pid, sim))
            except (ValueError, IndexError):
                continue

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_personalized_boost(self, post: Any) -> float:
        """Calculate a personalized ranking boost based on learned preferences."""
        boost = 0.0

        keyword_prefs = dict(self._get_keyword_preferences())
        hashtags = json.loads(post.hashtags) if post.hashtags else []
        tech = json.loads(post.mentioned_tech) if post.mentioned_tech else []
        for term in hashtags + tech:
            if term in keyword_prefs:
                boost += min(keyword_prefs[term] * 5, 15)

        domain_prefs = dict(self._get_domain_preferences())
        text = f"{post.title or ''} {post.text}".lower()
        from ai_content_radar.services.taxonomy import KeywordTaxonomy
        taxonomy = KeywordTaxonomy()
        for domain in taxonomy.domains:
            keywords = taxonomy.get_domain_keywords(domain)
            matched = any(kw["term"].lower() in text for kw in keywords)
            if matched and domain in domain_prefs:
                boost += min(domain_prefs[domain] * 3, 10)

        try:
            if post.author_rel and post.author_rel.quality_score > 0.6:
                boost += post.author_rel.quality_score * 5
        except Exception:
            pass

        return min(boost, 25)

    def embed_post(self, post_id: int) -> bool:
        """Generate and store embedding for a post."""
        post = self.db.get_post_by_id(post_id)
        if not post:
            return False

        key = f"post:{post_id}"
        if self.embedding_store.contains(key):
            return True

        text = f"{post.title or ''} {post.text}"
        embedding = generate_embedding(text)
        if embedding:
            self.embedding_store.store(key, embedding)
            return True
        return False

    def embed_all_posts(self) -> int:
        """Generate embeddings for all posts that don't have them."""
        posts = self.db.get_posts(limit=5000)
        count = 0
        for post in posts:
            if self.embed_post(post.id):
                count += 1
        self.embedding_store.save_to_disk()
        logger.info(f"Embedded {count} posts")
        return count
