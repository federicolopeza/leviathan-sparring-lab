from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Conversation, Message, MessageRole


async def create_conversation(
    db: AsyncSession,
    *,
    user_id: str,
    title: str,
    model: str,
) -> Conversation:
    conversation = Conversation(user_id=user_id, title=title, model=model)
    db.add(conversation)
    await db.flush()
    return conversation


async def list_conversations(db: AsyncSession, *, user_id: str) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation_by_id(db: AsyncSession, *, conversation_id: str) -> Conversation | None:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


async def add_message(
    db: AsyncSession,
    *,
    conversation_id: str,
    role: MessageRole,
    content: str,
) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    await db.flush()
    return message
