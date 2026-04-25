from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from jinja2 import Environment
from melispy_shared import AuditLog, verify_chain
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crud import (
    create_api_key,
    get_api_key,
    get_current_branding,
    get_user,
    list_api_keys,
    list_users,
    revoke_api_key,
    soft_delete_user,
    upsert_branding,
)
from app.deps.auth import Principal, get_current_principal, require_admin
from app.deps.db import get_auth_db, get_db
from app.models import ApiKey, AuthUser, Branding
from app.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyResponse,
    AuditLogListResponse,
    AuditLogResponse,
    BrandingRequest,
    BrandingResponse,
    InternalActionRequest,
    InternalActionResponse,
    UserDetail,
    UserListResponse,
    UserSummary,
)

router = APIRouter(prefix="/v1/admin", tags=["admin"])
logger = structlog.get_logger()

DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthDbSession = Annotated[AsyncSession, Depends(get_auth_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]
ClusterInternalHeader = Annotated[str | None, Header(alias="X-Cluster-Internal")]
ForwardedUserHeader = Annotated[str | None, Header(alias="X-Forwarded-User")]


def _page(page: int) -> int:
    return max(page, 1)


def _per_page(per_page: int) -> int:
    return min(max(per_page, 1), 100)


def _user_summary(user: AuthUser) -> UserSummary:
    return UserSummary.model_validate(
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "last_seen_at": user.last_seen_at,
        }
    )


def _user_detail(user: AuthUser) -> UserDetail:
    # V-T4-007 INTENTIONAL VULN: bio field returned raw without HTML escaping
    return UserDetail.model_validate(
        {
            **_user_summary(user).model_dump(),
            "bio": user.bio,
            "deleted_at": user.deleted_at,
        }
    )


def _api_key_response(api_key: ApiKey) -> ApiKeyResponse:
    return ApiKeyResponse.model_validate(
        {
            "id": api_key.id,
            "user_id": api_key.user_id,
            "name": api_key.name,
            "scopes": api_key.scope_string.split(),
            "created_at": api_key.created_at,
            "revoked_at": api_key.revoked_at,
        }
    )


def _branding_response(branding: Branding | None) -> BrandingResponse:
    if branding is None:
        return BrandingResponse(
            id=None,
            welcome_message="",
            rendered_html="",
            updated_by_user_id=None,
            updated_at=None,
        )
    return BrandingResponse.model_validate(
        {
            "id": branding.id,
            "welcome_message": branding.welcome_message,
            "rendered_html": branding.rendered_html,
            "updated_by_user_id": branding.updated_by_user_id,
            "updated_at": branding.updated_at,
        }
    )


async def _require_admin_principal(principal: Principal) -> Principal:
    return await require_admin(principal)


@router.get("/users", response_model=UserListResponse)
async def get_users(
    auth_db: AuthDbSession,
    principal: CurrentPrincipal,
    page: int = 1,
    per_page: int = 50,
) -> UserListResponse:
    await _require_admin_principal(principal)
    normalized_page = _page(page)
    normalized_per_page = _per_page(per_page)
    users, total = await list_users(auth_db, page=normalized_page, per_page=normalized_per_page)
    return UserListResponse(
        items=[_user_summary(user) for user in users],
        page=normalized_page,
        per_page=normalized_per_page,
        total=total,
    )


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user_detail(
    user_id: str,
    auth_db: AuthDbSession,
    principal: CurrentPrincipal,
) -> UserDetail:
    await _require_admin_principal(principal)
    user = await get_user(auth_db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return _user_detail(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    auth_db: AuthDbSession,
    principal: CurrentPrincipal,
) -> Response:
    await _require_admin_principal(principal)
    user = await get_user(auth_db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    await soft_delete_user(auth_db, user)
    await auth_db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audit-log", response_model=AuditLogListResponse)
async def get_audit_log(
    db: DbSession,
    principal: CurrentPrincipal,
    page: int = 1,
    per_page: int = 50,
) -> AuditLogListResponse:
    await _require_admin_principal(principal)
    normalized_page = _page(page)
    normalized_per_page = _per_page(per_page)
    total_result = await db.execute(select(func.count()).select_from(AuditLog))
    total = int(total_result.scalar_one())
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.ts.desc(), AuditLog.id.desc())
        .offset((normalized_page - 1) * normalized_per_page)
        .limit(normalized_per_page)
    )
    rows = list(result.scalars().all())
    chain_valid = await verify_chain(db)
    return AuditLogListResponse(
        items=[
            AuditLogResponse.model_validate(
                {
                    "id": str(row.id),
                    "ts": row.ts,
                    "event_type": row.event_type,
                    "actor_id": row.actor_id,
                    "resource": row.resource,
                    "action": row.action,
                    "payload": row.payload,
                    "prev_hash": row.prev_hash,
                    "hmac": row.hmac,
                }
            )
            for row in rows
        ],
        page=normalized_page,
        per_page=normalized_per_page,
        total=total,
        chain_valid=chain_valid,
        chain_badge="valid" if chain_valid else "tampered",
    )


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def post_api_key(
    payload: ApiKeyCreateRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> ApiKeyCreateResponse:
    await _require_admin_principal(principal)
    try:
        api_key, raw_key = await create_api_key(
            db,
            user_id=principal.user_id,
            name=payload.name,
            scopes=payload.scopes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid request") from exc
    await db.commit()
    await db.refresh(api_key)
    return ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        scopes=api_key.scope_string.split(),
        key=raw_key,
        created_at=api_key.created_at,
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def get_api_keys(principal: CurrentPrincipal, db: DbSession) -> list[ApiKeyResponse]:
    await _require_admin_principal(principal)
    rows = await list_api_keys(db)
    return [_api_key_response(row) for row in rows]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> Response:
    await _require_admin_principal(principal)
    api_key = await get_api_key(db, key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    await revoke_api_key(db, api_key)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/branding", response_model=BrandingResponse)
async def post_branding(
    payload: BrandingRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> BrandingResponse:
    await _require_admin_principal(principal)
    # V-T4-009 INTENTIONAL VULN: Jinja2 autoescape=False on user-supplied template — SSTI possible.
    rendered_html = Environment(autoescape=False).from_string(payload.welcome_message).render()
    branding = await upsert_branding(
        db,
        welcome_message=payload.welcome_message,
        rendered_html=rendered_html,
        updated_by_user_id=principal.user_id,
    )
    await db.commit()
    await db.refresh(branding)
    return _branding_response(branding)


@router.get("/branding", response_model=BrandingResponse)
async def get_branding(db: DbSession) -> BrandingResponse:
    branding = await get_current_branding(db)
    return _branding_response(branding)


@router.post("/internal-action", response_model=InternalActionResponse)
async def post_internal_action(
    payload: InternalActionRequest,
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
    x_cluster_internal: ClusterInternalHeader = None,
    x_forwarded_user: ForwardedUserHeader = None,
) -> InternalActionResponse:
    settings = get_settings()
    if settings.CLUSTER_INTERNAL_HEADER_TRUST and x_forwarded_user and x_cluster_internal == "1":
        # V-T3-004 INTENTIONAL VULN: X-Forwarded-User trusted unconditionally when X-Cluster-Internal=1 present; both headers are spoofable.
        logger.warning(
            "spoofable_internal_admin_action",
            actor_user_id=x_forwarded_user,
            action=payload.action,
        )
        return InternalActionResponse(
            status="accepted",
            actor_user_id=x_forwarded_user,
            action=payload.action,
        )
    principal = await get_current_principal(authorization)
    await _require_admin_principal(principal)
    _ = db
    return InternalActionResponse(
        status="accepted",
        actor_user_id=principal.user_id,
        action=payload.action,
    )
