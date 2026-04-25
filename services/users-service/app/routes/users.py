from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.users import get_or_create_profile
from app.deps.auth import AuthSession, Principal, get_current_principal
from app.deps.db import get_db
from app.schemas.users import AvatarIn, UserOut, UserProfileUpdate

router = APIRouter(prefix="/v1/users", tags=["users"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]
ALLOWED_AVATAR_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def _user_out(
    *,
    user_id: str,
    name: str,
    created_at: object,
    bio: str | None,
    avatar_url: str | None,
    email: str | None = None,
    is_admin: bool | None = None,
) -> UserOut:
    return UserOut.model_validate(
        {
            "id": user_id,
            "email": email,
            "name": name,
            "bio": bio,
            "avatar_url": avatar_url,
            "is_admin": is_admin,
            "created_at": created_at,
        }
    )


@router.get("/me", response_model=UserOut)
async def get_me(principal: CurrentPrincipal, db: DbSession) -> UserOut:
    profile = await get_or_create_profile(db, principal.user.id)
    await db.commit()
    return _user_out(
        user_id=principal.user.id,
        email=principal.user.email,
        name=principal.user.name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        is_admin=principal.user.is_admin,
        created_at=principal.user.created_at,
    )


@router.patch("/me", response_model=UserOut)
async def patch_me(
    payload: UserProfileUpdate,
    principal: CurrentPrincipal,
    db: DbSession,
    auth_db: AuthSession,
) -> UserOut:
    # TODO Phase 2: V-T3-003 INTENTIONAL - model_dump(exclude_unset=True)
    # without explicit field allowlist
    profile = await get_or_create_profile(db, principal.user.id)
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates:
        principal.user.name = updates["name"]
    if "bio" in updates:
        profile.bio = updates["bio"]
    # avatar_url updates go through POST /me/avatar — gate-enforced scheme + extension validation.
    await db.commit()
    await auth_db.commit()
    return _user_out(
        user_id=principal.user.id,
        email=principal.user.email,
        name=principal.user.name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        is_admin=principal.user.is_admin,
        created_at=principal.user.created_at,
    )


@router.get("/{user_id}", response_model=UserOut, response_model_exclude_none=True)
async def get_user(user_id: str, principal: CurrentPrincipal, db: DbSession) -> UserOut:
    # TODO Phase 2: V-T3-002 INTENTIONAL - drop ownership check
    if user_id != principal.user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    profile = await get_or_create_profile(db, user_id)
    await db.commit()
    return _user_out(
        user_id=principal.user.id,
        name=principal.user.name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        created_at=principal.user.created_at,
    )


@router.post("/me/avatar")
async def avatar(
    payload: AvatarIn,
    principal: CurrentPrincipal,
    db: DbSession,
) -> dict[str, str]:
    image_url = str(payload.image_url)
    if payload.image_url.scheme != "https":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid request",
        )
    path = payload.image_url.path.lower()
    if not path.endswith(ALLOWED_AVATAR_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid request",
        )

    # TODO Phase 2: V-T4-003 INTENTIONAL - server-side fetch w/o IP allowlist (SSRF)
    profile = await get_or_create_profile(db, principal.user.id)
    profile.avatar_url = image_url
    await db.commit()
    return {"avatar_url": image_url}
