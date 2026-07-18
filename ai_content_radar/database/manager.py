"""Database connection and session management."""
from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Generator, Optional

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, joinedload, sessionmaker

from ai_content_radar.config.settings import config
from ai_content_radar.models.database import (
    Author,
    Base,
    CacheEntry,
    Comment,
    Domain,
    Keyword,
    KeywordRanking,
    LearningEvent,
    PersonalKnowledge,
    Post,
    Ranking,
    SearchHistory,
    User,
    UserAction,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections, sessions, and CRUD operations."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or config.database_url
        self.engine = create_engine(
            self.database_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {},
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self) -> None:
        Base.metadata.drop_all(self.engine)

    # --- Users ---
    def get_or_create_user(self, name: str, email: str = "") -> User:
        with self.session() as s:
            user = None
            if email:
                user = s.query(User).filter_by(email=email).first()
            if not user:
                user = s.query(User).filter_by(name=name).first()
            if not user:
                user = User(name=name, email=email)
                s.add(user)
                s.flush()
            return user

    def get_user_by_id(self, user_id: int):
        with self.session() as s:
            return s.query(User).filter_by(id=user_id).first()

    def get_all_users(self) -> list:
        with self.session() as s:
            return s.query(User).all()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self.SessionLocal()
        session.expire_on_commit = False
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # --- Domains ---
    def get_or_create_domain(self, name: str, description: str = "") -> Domain:
        with self.session() as s:
            domain = s.query(Domain).filter_by(name=name).first()
            if not domain:
                domain = Domain(name=name, description=description)
                s.add(domain)
                s.flush()
            return domain

    def get_active_domains(self) -> list[Domain]:
        with self.session() as s:
            return s.query(Domain).filter_by(is_active=True).all()

    # --- Keywords ---
    def add_keyword(
        self,
        term: str,
        domain: str,
        weight: float = 1.0,
        is_custom: bool = False,
        aliases: Optional[list[str]] = None,
        synonyms: Optional[list[str]] = None,
    ) -> Keyword:
        with self.session() as s:
            existing = s.query(Keyword).filter_by(term=term.lower(), domain=domain).first()
            if existing:
                return existing
            kw = Keyword(
                term=term.lower(),
                domain=domain,
                weight=weight,
                is_custom=is_custom,
                aliases=json.dumps(aliases or []),
                synonyms=json.dumps(synonyms or []),
            )
            s.add(kw)
            s.flush()
            return kw

    def get_keywords(
        self, domain: Optional[str] = None, active_only: bool = True
    ) -> list[Keyword]:
        with self.session() as s:
            query = s.query(Keyword)
            if domain:
                query = query.filter_by(domain=domain)
            return query.all()

    def search_keywords(self, text: str) -> list[Keyword]:
        with self.session() as s:
            text_lower = text.lower()
            return s.query(Keyword).filter(
                (Keyword.term.contains(text_lower))
                | (Keyword.aliases.contains(text_lower))
                | (Keyword.synonyms.contains(text_lower))
            ).all()

    # --- Authors ---
    def get_or_create_author(
        self, name: str, title: str = "", organization: str = "", profile_url: str = ""
    ) -> Author:
        with self.session() as s:
            author = s.query(Author).filter_by(name=name).first()
            if not author:
                author = Author(
                    name=name,
                    title=title,
                    organization=organization,
                    profile_url=profile_url,
                )
                s.add(author)
                s.flush()
            else:
                if title:
                    author.title = title
                if organization:
                    author.organization = organization
                if profile_url:
                    author.profile_url = profile_url
            return author

    # --- Posts ---
    def add_post(self, post_data: dict[str, Any]) -> Optional[Post]:
        with self.session() as s:
            existing = s.query(Post).filter_by(url=post_data.get("url", "")).first()
            if existing:
                return None

            author_data = post_data.pop("author", None)
            author_id = None
            if author_data:
                author = self.get_or_create_author(**author_data)
                author_id = author.id

            post = Post(
                url=post_data.get("url", ""),
                title=post_data.get("title", ""),
                text=post_data.get("text", ""),
                author_id=author_id,
                date_posted=post_data.get("date_posted"),
                engagement_likes=post_data.get("engagement_likes", 0),
                engagement_comments=post_data.get("engagement_comments", 0),
                engagement_shares=post_data.get("engagement_shares", 0),
                media_images=json.dumps(post_data.get("media_images", [])),
                media_videos=json.dumps(post_data.get("media_videos", [])),
                hashtags=json.dumps(post_data.get("hashtags", [])),
                mentioned_companies=json.dumps(post_data.get("mentioned_companies", [])),
                mentioned_orgs=json.dumps(post_data.get("mentioned_orgs", [])),
                mentioned_tech=json.dumps(post_data.get("mentioned_tech", [])),
                source=post_data.get("source", "linkedin"),
                raw_data=json.dumps(post_data.get("raw_data", {})),
            )
            s.add(post)
            s.flush()
            return post

    def get_posts(self, limit: int = 100, offset: int = 0) -> list[Post]:
        with self.session() as s:
            return s.query(Post).options(
                joinedload(Post.author_rel),
                joinedload(Post.ranking),
            ).order_by(Post.date_collected.desc()).offset(offset).limit(limit).all()

    def get_post_by_id(self, post_id: int) -> Optional[Post]:
        with self.session() as s:
            return s.query(Post).options(
                joinedload(Post.author_rel),
                joinedload(Post.ranking),
            ).filter_by(id=post_id).first()

    def get_unranked_posts(self) -> list[Post]:
        with self.session() as s:
            return (
                s.query(Post)
                .options(joinedload(Post.author_rel))
                .filter(~Post.id.in_(s.query(Ranking.post_id)))
                .all()
            )

    # --- Rankings ---
    def add_ranking(self, ranking_data: dict[str, Any]) -> Ranking:
        with self.session() as s:
            existing = s.query(Ranking).filter_by(post_id=ranking_data["post_id"]).first()
            if existing:
                for k, v in ranking_data.items():
                    setattr(existing, k, v)
                existing.ranked_at = datetime.utcnow()
                return existing
            ranking = Ranking(**ranking_data)
            s.add(ranking)
            s.flush()
            return ranking

    def get_ranking_for_post(self, post_id: int):
        with self.session() as s:
            return s.query(Ranking).filter_by(post_id=post_id).first()

    def get_ranked_posts(self, min_score: int = 0, limit: int = 100) -> list[tuple]:
        with self.session() as s:
            return (
                s.query(Post, Ranking)
                .options(joinedload(Post.author_rel))
                .join(Ranking, Post.id == Ranking.post_id)
                .filter(Ranking.score >= min_score)
                .order_by(Ranking.score.desc())
                .limit(limit)
                .all()
            )

    def add_keyword_ranking(self, post_id: int, keyword_id: int, score: float, matched_in: str = "text") -> None:
        with self.session() as s:
            kr = KeywordRanking(
                post_id=post_id,
                keyword_id=keyword_id,
                match_score=score,
                matched_in=matched_in,
            )
            s.add(kr)

    # --- Comments ---
    def add_comment(self, comment_data: dict[str, Any]):
        with self.session() as s:
            comment = Comment(**comment_data)
            s.add(comment)
            s.flush()
            return comment

    def get_comments_for_post(self, post_id: int, user_id: Optional[int] = None):
        with self.session() as s:
            query = s.query(Comment).filter_by(post_id=post_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            return query.all()

    def update_comment(self, comment_id: int, **kwargs: Any) -> Optional[Comment]:
        with self.session() as s:
            comment = s.query(Comment).filter_by(id=comment_id).first()
            if comment:
                for k, v in kwargs.items():
                    setattr(comment, k, v)
            return comment

    # --- User Actions ---
    def record_action(self, post_id: int, action: str, comment_id: Optional[int] = None, notes: str = "", user_id: int = 1):
        with self.session() as s:
            ua = UserAction(
                user_id=user_id,
                post_id=post_id,
                comment_id=comment_id,
                action=action,
                notes=notes,
            )
            s.add(ua)
            s.flush()
            return ua

    def get_actions(self, action_type: Optional[str] = None, limit: int = 100, user_id: Optional[int] = None):
        with self.session() as s:
            query = s.query(UserAction)
            if user_id:
                query = query.filter_by(user_id=user_id)
            if action_type:
                query = query.filter_by(action=action_type)
            return query.order_by(UserAction.timestamp.desc()).limit(limit).all()

    def get_action_counts(self) -> dict[str, int]:
        with self.session() as s:
            results = s.query(UserAction.action, func.count(UserAction.id)).group_by(UserAction.action).all()
            return {action: count for action, count in results}

    # --- Personal Knowledge ---
    def add_knowledge(self, category: str, key: str, value: str, weight: float = 1.0, user_id: int = 1):
        with self.session() as s:
            pk = PersonalKnowledge(
                user_id=user_id,
                category=category,
                key=key,
                value=value,
                relevance_weight=weight,
            )
            s.add(pk)
            s.flush()
            return pk

    def get_knowledge(self, category: Optional[str] = None, user_id: Optional[int] = None):
        with self.session() as s:
            query = s.query(PersonalKnowledge)
            if user_id:
                query = query.filter_by(user_id=user_id)
            if category:
                query = query.filter_by(category=category)
            return query.all()

    def delete_knowledge(self, knowledge_id: int) -> bool:
        with self.session() as s:
            pk = s.query(PersonalKnowledge).filter_by(id=knowledge_id).first()
            if pk:
                s.delete(pk)
                return True
            return False

    # --- Search History ---
    def add_search_history(self, search_data: dict[str, Any]) -> SearchHistory:
        with self.session() as s:
            sh = SearchHistory(
                query=search_data.get("query", ""),
                domains=json.dumps(search_data.get("domains", [])),
                keywords_used=json.dumps(search_data.get("keywords_used", [])),
                results_count=search_data.get("results_count", 0),
                avg_score=search_data.get("avg_score", 0.0),
                duration_seconds=search_data.get("duration_seconds", 0.0),
            )
            s.add(sh)
            s.flush()
            return sh

    def get_search_history(self, limit: int = 50) -> list[SearchHistory]:
        with self.session() as s:
            return s.query(SearchHistory).order_by(SearchHistory.searched_at.desc()).limit(limit).all()

    # --- Cache ---
    def get_cache(self, cache_key: str) -> Optional[str]:
        with self.session() as s:
            entry = s.query(CacheEntry).filter_by(cache_key=cache_key).first()
            if entry:
                if entry.expires_at and entry.expires_at < datetime.utcnow():
                    s.delete(entry)
                    return None
                return entry.data
            return None

    def set_cache(self, cache_key: str, data: str, cache_type: str = "generic", ttl_hours: Optional[int] = None) -> None:
        with self.session() as s:
            existing = s.query(CacheEntry).filter_by(cache_key=cache_key).first()
            ttl = ttl_hours or config.cache.ttl_hours
            expires = datetime.utcnow() + timedelta(hours=ttl)
            if existing:
                existing.data = data
                existing.expires_at = expires
            else:
                entry = CacheEntry(
                    cache_key=cache_key,
                    cache_type=cache_type,
                    data=data,
                    expires_at=expires,
                )
                s.add(entry)

    def clear_expired_cache(self) -> int:
        with self.session() as s:
            count = s.query(CacheEntry).filter(CacheEntry.expires_at < datetime.utcnow()).delete()
            return count

    # --- Learning Events ---
    def record_learning_event(
        self, event_type: str, post_id: Optional[int] = None,
        keyword: Optional[str] = None, domain: Optional[str] = None,
        author_id: Optional[int] = None, score_delta: float = 0.0,
        metadata_json: Optional[dict] = None,
    ) -> LearningEvent:
        with self.session() as s:
            le = LearningEvent(
                event_type=event_type,
                post_id=post_id,
                keyword=keyword,
                domain=domain,
                author_id=author_id,
                score_delta=score_delta,
                metadata_json=json.dumps(metadata_json or {}),
            )
            s.add(le)
            s.flush()
            return le

    def get_learning_stats(self) -> dict[str, Any]:
        with self.session() as s:
            total_actions = s.query(func.count(UserAction.id)).scalar() or 0
            approved = s.query(func.count(UserAction.id)).filter_by(action="approved").scalar() or 0
            rejected = s.query(func.count(UserAction.id)).filter_by(action="rejected").scalar() or 0
            return {
                "total_actions": total_actions,
                "approved": approved,
                "rejected": rejected,
                "approval_rate": approved / total_actions if total_actions > 0 else 0,
            }

    # --- Analytics ---
    def get_analytics(self) -> dict[str, Any]:
        with self.session() as s:
            total_posts = s.query(func.count(Post.id)).scalar() or 0
            total_ranked = s.query(func.count(Ranking.id)).scalar() or 0
            total_comments = s.query(func.count(Comment.id)).scalar() or 0
            total_actions = s.query(func.count(UserAction.id)).scalar() or 0
            approved = s.query(func.count(UserAction.id)).filter_by(action="approved").scalar() or 0
            rejected = s.query(func.count(UserAction.id)).filter_by(action="rejected").scalar() or 0
            favorites = s.query(func.count(UserAction.id)).filter_by(action="favorite").scalar() or 0

            top_domains = (
                s.query(Ranking.reason, func.count(Ranking.id))
                .group_by(Ranking.reason)
                .order_by(func.count(Ranking.id).desc())
                .limit(10)
                .all()
            )

            avg_score = s.query(func.avg(Ranking.score)).scalar() or 0
            max_score = s.query(func.max(Ranking.score)).scalar() or 0

            return {
                "total_posts": total_posts,
                "total_ranked": total_ranked,
                "total_comments": total_comments,
                "total_actions": total_actions,
                "approved": approved,
                "rejected": rejected,
                "favorites": favorites,
                "avg_score": round(avg_score, 1),
                "max_score": max_score,
                "top_domains": top_domains,
            }
