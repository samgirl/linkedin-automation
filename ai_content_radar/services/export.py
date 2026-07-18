"""Export service - CSV, JSON, Markdown export for all data types."""
from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any

from ai_content_radar.database.manager import DatabaseManager

logger = logging.getLogger(__name__)


class ExportService:
    """Export data in multiple formats."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def export_approved_comments(self, fmt: str = "json") -> str:
        """Export all approved comments with their source posts."""
        actions = self.db.get_actions(action_type="approved", limit=10000)
        data = []
        for action in actions:
            post = self.db.get_post_by_id(action.post_id)
            if not post:
                continue
            comments = self.db.get_comments_for_post(post.id)
            ranking = None
            with self.db.session() as s:
                from ai_content_radar.models.database import Ranking
                ranking = s.query(Ranking).filter_by(post_id=post.id).first()

            data.append({
                "url": post.url,
                "title": post.title or "",
                "author": post.author_rel.name if post.author_rel else "",
                "author_title": post.author_rel.title if post.author_rel else "",
                "organization": post.author_rel.organization if post.author_rel else "",
                "post_text": post.text[:500],
                "comment": comments[0].text if comments else "",
                "comment_type": comments[0].comment_type if comments else "",
                "word_count": comments[0].word_count if comments else 0,
                "score": ranking.score if ranking else 0,
                "approved_at": action.timestamp.isoformat() if action.timestamp else "",
            })

        return self._format(data, fmt, "approved_comments")

    def export_all_posts(self, fmt: str = "json", limit: int = 5000) -> str:
        """Export all posts."""
        posts = self.db.get_posts(limit=limit)
        data = []
        for post in posts:
            ranking = None
            with self.db.session() as s:
                from ai_content_radar.models.database import Ranking
                ranking = s.query(Ranking).filter_by(post_id=post.id).first()

            data.append({
                "id": post.id,
                "url": post.url,
                "title": post.title or "",
                "text": post.text[:1000],
                "author": post.author_rel.name if post.author_rel else "",
                "organization": post.author_rel.organization if post.author_rel else "",
                "date_posted": post.date_posted.isoformat() if post.date_posted else "",
                "date_collected": post.date_collected.isoformat() if post.date_collected else "",
                "engagement_likes": post.engagement_likes,
                "engagement_comments": post.engagement_comments,
                "engagement_shares": post.engagement_shares,
                "source": post.source,
                "score": ranking.score if ranking else None,
            })

        return self._format(data, fmt, "all_posts")

    def export_rankings(self, fmt: str = "json", min_score: int = 0, limit: int = 1000) -> str:
        """Export post rankings with scores."""
        ranked = self.db.get_ranked_posts(min_score=min_score, limit=limit)
        data = []
        for post, ranking in ranked:
            data.append({
                "url": post.url,
                "title": post.title or "",
                "author": post.author_rel.name if post.author_rel else "",
                "score": ranking.score,
                "reason": ranking.reason,
                "keyword_match": ranking.keyword_match_score,
                "quality": ranking.quality_score,
                "freshness": ranking.freshness_score,
                "engagement": ranking.engagement_score,
                "opportunity": ranking.opportunity_score,
                "novelty": ranking.novelty_score,
                "relevance": ranking.relevance_score,
                "ranked_at": ranking.ranked_at.isoformat() if ranking.ranked_at else "",
            })

        return self._format(data, fmt, "rankings")

    def export_search_history(self, fmt: str = "json") -> str:
        """Export search history."""
        history = self.db.get_search_history(limit=1000)
        data = []
        for entry in history:
            data.append({
                "query": entry.query,
                "domains": json.loads(entry.domains) if entry.domains else [],
                "keywords": json.loads(entry.keywords_used) if entry.keywords_used else [],
                "results_count": entry.results_count,
                "avg_score": entry.avg_score,
                "duration_seconds": entry.duration_seconds,
                "searched_at": entry.searched_at.isoformat() if entry.searched_at else "",
            })

        return self._format(data, fmt, "search_history")

    def export_knowledge_base(self, fmt: str = "json") -> str:
        """Export personal knowledge base."""
        knowledge = self.db.get_knowledge()
        data = [{
            "category": k.category,
            "key": k.key,
            "value": k.value,
            "weight": k.relevance_weight,
            "created_at": k.created_at.isoformat() if k.created_at else "",
        } for k in knowledge]

        return self._format(data, fmt, "knowledge_base")

    def export_analytics(self, fmt: str = "json") -> str:
        """Export analytics summary."""
        analytics = self.db.get_analytics()
        data = [analytics]

        return self._format(data, fmt, "analytics")

    def export_all(self, fmt: str = "json") -> str:
        """Export everything as a combined file."""
        combined = {
            "exported_at": datetime.utcnow().isoformat(),
            "approved_comments": json.loads(self.export_approved_comments("json")),
            "rankings": json.loads(self.export_rankings("json")),
            "search_history": json.loads(self.export_search_history("json")),
            "knowledge_base": json.loads(self.export_knowledge_base("json")),
            "analytics": json.loads(self.export_analytics("json")),
        }

        if fmt == "json":
            return json.dumps(combined, indent=2)
        elif fmt == "markdown":
            return self._combined_to_markdown(combined)
        elif fmt == "csv":
            return self._combined_to_csv(combined)

        return json.dumps(combined, indent=2)

    def _format(self, data: list[dict], fmt: str, name: str) -> str:
        if fmt == "json":
            return json.dumps(data, indent=2, default=str)
        elif fmt == "csv":
            return self._to_csv(data)
        elif fmt == "markdown":
            return self._to_markdown(data, name)
        return json.dumps(data, indent=2, default=str)

    def _to_csv(self, data: list[dict]) -> str:
        if not data:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        for row in data:
            cleaned = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v for k, v in row.items()}
            writer.writerow(cleaned)
        return output.getvalue()

    def _to_markdown(self, data: list[dict], name: str) -> str:
        if not data:
            return f"# {name}\n\nNo data available.\n"

        lines = [f"# {name}", f"*Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}*", ""]

        for i, item in enumerate(data, 1):
            lines.append(f"## {i}. {item.get('title', item.get('key', item.get('query', '')))[:80]}")
            for k, v in item.items():
                if v and k not in ("title", "key", "query"):
                    lines.append(f"- **{k}:** {v}")
            lines.append("")

        return "\n".join(lines)

    def _combined_to_markdown(self, combined: dict) -> str:
        lines = [
            "# AI Content Radar - Export",
            f"*Exported: {combined['exported_at']}*",
            "",
        ]

        for section, items in combined.items():
            if section == "exported_at":
                continue
            lines.append(f"## {section.replace('_', ' ').title()}")
            if isinstance(items, list):
                for item in items[:20]:
                    lines.append(f"- {json.dumps(item, default=str)[:200]}")
            elif isinstance(items, dict):
                for k, v in items.items():
                    lines.append(f"- **{k}:** {v}")
            lines.append("")

        return "\n".join(lines)

    def _combined_to_csv(self, combined: dict) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Section", "Data"])
        for section, items in combined.items():
            if section == "exported_at":
                writer.writerow(["exported_at", items])
            else:
                writer.writerow([section, json.dumps(items, default=str)[:500]])
        return output.getvalue()
