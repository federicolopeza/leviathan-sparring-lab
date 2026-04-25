from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, status
from jinja2 import Environment
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.agent_runs import cancel_agent_run, create_agent_run, get_agent_run, list_agent_runs
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.schemas.agents import AgentRunCreateRequest, AgentRunRenderResponse, AgentRunResponse

router = APIRouter(prefix="/v1/agents", tags=["agents"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


@router.post("/runs", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
async def post_run(
    payload: AgentRunCreateRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> AgentRunResponse:
    run = await create_agent_run(
        db,
        user_id=principal.user_id,
        org_id=principal.org_id,
        name=payload.name,
        input_json=payload.input_json,
    )
    await db.commit()
    await db.refresh(run)
    return AgentRunResponse.model_validate(run)


@router.get("/runs", response_model=list[AgentRunResponse])
async def get_runs(principal: CurrentPrincipal, db: DbSession) -> list[AgentRunResponse]:
    runs = await list_agent_runs(db, user_id=principal.user_id)
    return [AgentRunResponse.model_validate(run) for run in runs]


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_run(
    run_id: str,
    _principal: CurrentPrincipal,
    db: DbSession,
) -> AgentRunResponse:
    # V-T5-001 INTENTIONAL VULN: no ownership check on run_id — IDOR across users
    run = await get_agent_run(db, run_id=run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return AgentRunResponse.model_validate(run)


@router.post("/runs/{run_id}/cancel", response_model=AgentRunResponse)
async def post_cancel_run(
    run_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> AgentRunResponse:
    run = await get_agent_run(db, run_id=run_id)
    if run is None or run.user_id != principal.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    run = await cancel_agent_run(db, run=run)
    await db.commit()
    await db.refresh(run)
    return AgentRunResponse.model_validate(run)


@router.post("/runs/{run_id}/render", response_model=AgentRunRenderResponse)
async def post_render_run(
    run_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> AgentRunRenderResponse:
    run = await get_agent_run(db, run_id=run_id)
    if run is None or run.user_id != principal.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    # V-T6-001 INTENTIONAL VULN: SSTI via Jinja2 render of user input, autoescape=False
    env = Environment(autoescape=False)  # noqa: S701
    template = env.from_string(cast(str, run.input_json.get("prompt", "")))
    rendered = template.render(user=principal.user_id)
    run.output_json = {"rendered": rendered}
    await db.commit()
    return AgentRunRenderResponse(run_id=run.id, rendered=rendered)
