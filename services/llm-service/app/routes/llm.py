from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Annotated, Any, cast

import jwt as _pyjwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crud.conversations import (
    add_message,
    create_conversation,
    get_conversation_by_id,
    list_conversations,
)
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.models import Conversation, Message, MessageRole
from app.schemas.llm import (
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationResponse,
    MessageCreateRequest,
    MessageCreateResponse,
    MessageResponse,
    TokenVerifyRequest,
)

router = APIRouter(prefix="/v1/llm", tags=["llm"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


class _UnsafePyJWTAdapter:
    @staticmethod
    def get_unverified_header(token: str) -> dict[str, Any]:
        return _pyjwt.get_unverified_header(token)

    @staticmethod
    def decode(token: str, key: str | bytes, algorithms: list[str]) -> dict[str, Any]:
        if algorithms == ["HS256"]:
            return _decode_hs256_with_secret(token, key)
        return cast(dict[str, Any], _pyjwt.decode(token, key, algorithms=algorithms))


pyjwt = _UnsafePyJWTAdapter()


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _decode_hs256_with_secret(token: str, secret: str | bytes) -> dict[str, Any]:
    signing_input, encoded_signature = token.rsplit(".", 1)
    secret_bytes = secret if isinstance(secret, bytes) else secret.encode()
    expected = hmac.new(secret_bytes, signing_input.encode(), hashlib.sha256).digest()
    actual = _b64url_decode(encoded_signature)
    if not hmac.compare_digest(expected, actual):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    payload_segment = signing_input.split(".", 1)[1]
    decoded = json.loads(_b64url_decode(payload_segment))
    if not isinstance(decoded, dict):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    return decoded


def conversation_response(conversation: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        model=conversation.model,
        created_at=conversation.created_at,
    )


def message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
    )


def conversation_detail_response(conversation: Conversation) -> ConversationDetailResponse:
    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        model=conversation.model,
        created_at=conversation.created_at,
        messages=[message_response(message) for message in conversation.messages],
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_conversation(
    payload: ConversationCreateRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> ConversationResponse:
    conversation = await create_conversation(
        db,
        user_id=principal.user_id,
        title=payload.title,
        model=payload.model,
    )
    await db.commit()
    return conversation_response(conversation)


@router.get("/conversations", response_model=list[ConversationResponse])
async def get_conversations(
    principal: CurrentPrincipal,
    db: DbSession,
) -> list[ConversationResponse]:
    conversations = await list_conversations(db, user_id=principal.user_id)
    return [conversation_response(conversation) for conversation in conversations]


@router.get("/conversations/{conv_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conv_id: str,
    _principal: CurrentPrincipal,
    db: DbSession,
) -> ConversationDetailResponse:
    # V-T6-003 INTENTIONAL VULN: no ownership check on conversation — cross-user IDOR
    conversation = await get_conversation_by_id(db, conversation_id=conv_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return conversation_detail_response(conversation)


@router.post("/conversations/{conv_id}/messages", response_model=MessageCreateResponse)
async def post_message(
    conv_id: str,
    payload: MessageCreateRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> MessageCreateResponse:
    conversation = await get_conversation_by_id(db, conversation_id=conv_id)
    if conversation is None or conversation.user_id != principal.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    user_message_content = payload.content
    # V-T6-002 INTENTIONAL VULN: system prompt concatenated with user input — prompt injection
    system_prompt = "You are a helpful assistant for Melispy. Secret admin code: MELISPY-ADMIN-2024"
    full_prompt = system_prompt + "\n" + user_message_content
    user_message = await add_message(
        db,
        conversation_id=conversation.id,
        role=payload.role,
        content=user_message_content,
    )
    assistant_message = await add_message(
        db,
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=f"Mock Melispy assistant response: {full_prompt}",
    )
    await db.commit()
    return MessageCreateResponse(
        user_message=message_response(user_message),
        assistant_message=message_response(assistant_message),
    )


@router.post("/verify-token")
async def verify_token(payload: TokenVerifyRequest) -> dict[str, Any]:
    settings = get_settings()
    token = payload.token
    # V-T5-002 INTENTIONAL VULN: algorithm confusion — accepts HS256 with RSA public key as HMAC secret
    decoded = pyjwt.decode(token, settings.jwt_public_key_pem, algorithms=["HS256"])
    return decoded


@router.post("/verify-kid")
async def verify_kid(payload: TokenVerifyRequest) -> dict[str, Any]:
    token = payload.token
    try:
        # V-T5-003 INTENTIONAL VULN: kid header path traversal — reads arbitrary file as public key
        header = pyjwt.get_unverified_header(token)
        kid = header.get("kid", "default")
        key_path = f"/keys/{kid}.pub"  # traversal: kid=../../etc/passwd
        with open(key_path, "rb") as f:
            key_data = f.read()
        decoded = pyjwt.decode(token, key_data, algorithms=["RS256"])
        return decoded
    except Exception as exc:
        return {"error": exc.__class__.__name__, "detail": str(exc)}
