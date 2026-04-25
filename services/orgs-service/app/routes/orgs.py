from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.orgs import count_members, create_org, list_orgs_for_user
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.deps.membership import require_org_membership, require_owner
from app.models import Org
from app.schemas.orgs import OrgCreate, OrgDetailResponse, OrgResponse, OrgUpdate

router = APIRouter(prefix="/v1/orgs", tags=["orgs"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def _org_response(org: Org) -> OrgResponse:
    return OrgResponse.model_validate(
        {
            "id": org.id,
            "name": org.name,
            "plan": org.plan,
            "region": org.region,
            "owner_user_id": org.owner_user_id,
            "created_at": org.created_at,
            "updated_at": org.updated_at,
        }
    )


async def _org_detail(db: AsyncSession, org: Org) -> OrgDetailResponse:
    base = _org_response(org).model_dump()
    base["member_count"] = await count_members(db, org.id)
    return OrgDetailResponse.model_validate(base)


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrgCreate,
    principal: CurrentPrincipal,
    db: DbSession,
) -> OrgResponse:
    org = await create_org(
        db,
        name=payload.name,
        plan=payload.plan,
        region=payload.region,
        owner_user_id=principal.user_id,
    )
    await db.commit()
    return _org_response(org)


@router.get("/me", response_model=list[OrgResponse])
async def get_my_orgs(principal: CurrentPrincipal, db: DbSession) -> list[OrgResponse]:
    orgs = await list_orgs_for_user(db, principal.user_id)
    return [_org_response(org) for org in orgs]


@router.get("/{org_id}", response_model=OrgDetailResponse)
async def get_organization(
    org_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> OrgDetailResponse:
    # TODO Phase 2: V-T3-001 INTENTIONAL — drop tenant scope check
    org, _membership = await require_org_membership(db, org_id=org_id, user_id=principal.user_id)
    return await _org_detail(db, org)


@router.patch("/{org_id}", response_model=OrgResponse)
async def patch_organization(
    org_id: str,
    payload: OrgUpdate,
    principal: CurrentPrincipal,
    db: DbSession,
) -> OrgResponse:
    org, _membership = await require_owner(db, org_id=org_id, user_id=principal.user_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(org, field, value)
    await db.commit()
    await db.refresh(org)
    return _org_response(org)
