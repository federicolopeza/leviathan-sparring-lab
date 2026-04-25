from __future__ import annotations

from app.models import NotificationTemplate
from jinja2 import Environment, select_autoescape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

jinja_env = Environment(autoescape=select_autoescape(default=True))


async def get_template_by_code(db: AsyncSession, code: str) -> NotificationTemplate | None:
    result = await db.execute(select(NotificationTemplate).where(NotificationTemplate.code == code))
    return result.scalar_one_or_none()


def render_template(template: NotificationTemplate, vars: dict[str, object]) -> tuple[str, str]:
    subject = jinja_env.from_string(template.subject_template).render(**vars)
    body = jinja_env.from_string(template.body_template).render(**vars)
    return subject, body
