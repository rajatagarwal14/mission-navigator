import json
from datetime import datetime, timedelta
from collections import Counter
from typing import List

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.conversation import ChatSession, ChatMessage
from models.analytics import QueryLog, ResourceClick
from schemas.analytics import AnalyticsOverview, TopQuestion, TopResource, UsageTrendPoint


class AnalyticsService:
    async def get_overview(self, db: AsyncSession) -> AnalyticsOverview:
        """Get overview metrics."""
        # Total sessions
        total = await db.execute(select(func.count(ChatSession.id)))
        total_sessions = total.scalar() or 0

        # Messages today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_msgs = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.created_at >= today_start)
        )
        messages_today = today_msgs.scalar() or 0

        # Unique users (sessions) in last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        unique = await db.execute(
            select(func.count(ChatSession.id)).where(ChatSession.started_at >= week_ago)
        )
        unique_users_7d = unique.scalar() or 0

        # Crisis alerts
        crisis = await db.execute(
            select(func.count(ChatSession.id)).where(ChatSession.crisis_flagged == True)
        )
        crisis_alerts = crisis.scalar() or 0

        return AnalyticsOverview(
            total_sessions=total_sessions,
            messages_today=messages_today,
            unique_users_7d=unique_users_7d,
            crisis_alerts=crisis_alerts,
        )

    async def get_top_questions(self, db: AsyncSession, limit: int = 10) -> List[TopQuestion]:
        """Get most frequently asked questions."""
        result = await db.execute(
            select(QueryLog.query_text).order_by(QueryLog.created_at.desc()).limit(500)
        )
        queries = [r[0] for r in result.all()]

        # Simple frequency-based clustering (group similar short queries)
        counter = Counter()
        for q in queries:
            # Normalize: lowercase, strip punctuation
            normalized = q.lower().strip().rstrip("?.,!")
            if len(normalized) > 10:
                counter[normalized] += 1

        top = counter.most_common(limit)
        return [TopQuestion(question=q, count=c) for q, c in top]

    async def get_top_resources(self, db: AsyncSession, limit: int = 10) -> List[TopResource]:
        """Get most cited and clicked resources."""
        # Citations from query logs
        result = await db.execute(select(QueryLog.resources_cited).where(QueryLog.resources_cited.isnot(None)))
        citation_counter = Counter()
        for row in result.all():
            try:
                resources = json.loads(row[0])
                for r in resources:
                    citation_counter[r] += 1
            except (json.JSONDecodeError, TypeError):
                pass

        # Clicks
        click_result = await db.execute(
            select(ResourceClick.resource_name, func.count(ResourceClick.id))
            .group_by(ResourceClick.resource_name)
        )
        click_counts = dict(click_result.all())

        # Merge
        all_resources = set(citation_counter.keys()) | set(click_counts.keys())
        resources = []
        for name in all_resources:
            resources.append(TopResource(
                name=name,
                citations=citation_counter.get(name, 0),
                clicks=click_counts.get(name, 0),
            ))

        resources.sort(key=lambda r: r.citations + r.clicks, reverse=True)
        return resources[:limit]

    async def get_usage_trend(self, db: AsyncSession, days: int = 30) -> List[UsageTrendPoint]:
        """Get daily usage trend."""
        points = []
        for i in range(days - 1, -1, -1):
            date = datetime.utcnow().date() - timedelta(days=i)
            day_start = datetime.combine(date, datetime.min.time())
            day_end = day_start + timedelta(days=1)

            sessions_count = await db.execute(
                select(func.count(ChatSession.id)).where(
                    and_(ChatSession.started_at >= day_start, ChatSession.started_at < day_end)
                )
            )
            messages_count = await db.execute(
                select(func.count(ChatMessage.id)).where(
                    and_(ChatMessage.created_at >= day_start, ChatMessage.created_at < day_end)
                )
            )

            points.append(UsageTrendPoint(
                date=date.isoformat(),
                sessions=sessions_count.scalar() or 0,
                messages=messages_count.scalar() or 0,
            ))

        return points

    async def log_resource_click(self, db: AsyncSession, session_id: str, resource_name: str, resource_url: str = None):
        click = ResourceClick(
            session_id=session_id,
            resource_name=resource_name,
            resource_url=resource_url,
        )
        db.add(click)
        await db.commit()


analytics_service = AnalyticsService()
