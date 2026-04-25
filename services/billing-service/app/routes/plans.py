from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.plans import list_plans
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.models import Plan
from app.schemas.billing import PlanResponse

router = APIRouter(prefix="/v1/billing/plans", tags=["billing-plans"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def plan_response(plan: Plan) -> PlanResponse:
    return PlanResponse.model_validate(
        {
            "id": plan.id,
            "code": plan.code,
            "name": plan.name,
            "monthly_price_cents": plan.monthly_price_cents,
            "currency": plan.currency,
            "description": plan.description,
            "features": plan.features,
        }
    )


@router.get("", response_model=list[PlanResponse])
async def get_plans(_principal: CurrentPrincipal, db: DbSession) -> list[PlanResponse]:
    plans = await list_plans(db)
    await db.commit()
    return [plan_response(plan) for plan in plans]
