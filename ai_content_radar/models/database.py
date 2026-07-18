"""SQLAlchemy ORM models for the database."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(200), nullable=False, index=True)
    domain = Column(String(100), nullable=False, index=True)
    weight = Column(Float, default=1.0)
    is_custom = Column(Boolean, default=False)
    aliases = Column(Text, default="[]")  # JSON array
    synonyms = Column(Text, default="[]")  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)

    keyword_rankings = relationship("KeywordRanking", back_populates="keyword")


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    title = Column(String(300), default="")
    organization = Column(String(300), default="")
    profile_url = Column(String(500), default="")
    quality_score = Column(Float, default=0.5)
    post_count = Column(Integer, default=0)
    avg_engagement = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("Post", back_populates="author_rel")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    title = Column(String(500), default="")
    text = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=True)
    date_posted = Column(DateTime, nullable=True)
    date_collected = Column(DateTime, default=datetime.utcnow)
    engagement_likes = Column(Integer, default=0)
    engagement_comments = Column(Integer, default=0)
    engagement_shares = Column(Integer, default=0)
    media_images = Column(Text, default="[]")
    media_videos = Column(Text, default="[]")
    hashtags = Column(Text, default="[]")
    mentioned_companies = Column(Text, default="[]")
    mentioned_orgs = Column(Text, default="[]")
    mentioned_tech = Column(Text, default="[]")
    source = Column(String(50), default="linkedin")
    is_duplicate = Column(Boolean, default=False)
    raw_data = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    author_rel = relationship("Author", back_populates="posts")
    ranking = relationship("Ranking", back_populates="post", uselist=False)
    comments = relationship("Comment", back_populates="post")
    actions = relationship("UserAction", back_populates="post")
    keyword_matches = relationship("KeywordRanking", back_populates="post")


class Ranking(Base):
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, unique=True, index=True)
    score = Column(Integer, default=0)
    reason = Column(Text, default="")
    keyword_match_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    novelty_score = Column(Float, default=0.0)
    opportunity_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    ranked_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="ranking")


class KeywordRanking(Base):
    __tablename__ = "keyword_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    match_score = Column(Float, default=0.0)
    matched_in = Column(String(50), default="text")  # text, title, hashtags, entities

    post = relationship("Post", back_populates="keyword_matches")
    keyword = relationship("Keyword", back_populates="keyword_rankings")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    comment_type = Column(String(50), default="professional")
    text = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    is_copied = Column(Boolean, default=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String(100), default="")
    prompt_version = Column(String(50), default="")

    post = relationship("Post", back_populates="comments")
    actions = relationship("UserAction", back_populates="comment")
    user = relationship("User", back_populates="comments")


class UserAction(Base):
    __tablename__ = "user_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    action = Column(String(50), nullable=False)  # approved, rejected, favorite, copied, ignored, edited
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, default="")

    post = relationship("Post", back_populates="actions")
    comment = relationship("Comment", back_populates="actions")
    user = relationship("User", back_populates="actions")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), default="", unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    knowledge = relationship("PersonalKnowledge", back_populates="user")
    actions = relationship("UserAction", back_populates="user")
    comments = relationship("Comment", back_populates="user")


class PersonalKnowledge(Base):
    __tablename__ = "personal_knowledge"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    key = Column(String(200), nullable=False)
    value = Column(Text, nullable=False)
    relevance_weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="knowledge")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    query = Column(Text, nullable=False)
    domains = Column(Text, default="[]")
    keywords_used = Column(Text, default="[]")
    results_count = Column(Integer, default=0)
    avg_score = Column(Float, default=0.0)
    searched_at = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Float, default=0.0)


class CacheEntry(Base):
    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(500), nullable=False, unique=True, index=True)
    cache_type = Column(String(50), nullable=False, index=True)
    data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)
    post_id = Column(Integer, nullable=True)
    keyword = Column(String(200), nullable=True)
    domain = Column(String(100), nullable=True)
    author_id = Column(Integer, nullable=True)
    score_delta = Column(Float, default=0.0)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
