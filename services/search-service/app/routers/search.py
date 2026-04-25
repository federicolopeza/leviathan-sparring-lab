from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, delete, func, or_, select, text
from sqlalchemy.engine import RowMapping

from app.deps import DbSession, Principal, get_current_principal
from app.models import IndexedDocument, SavedSearch
from app.schemas import (
    SavedSearchCreate,
    SavedSearchCreateResponse,
    SavedSearchResponse,
    SearchResponse,
    SearchResult,
)

router = APIRouter(prefix="/v1/search", tags=["search"])
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def _tenant_scope(statement: Select[tuple[IndexedDocument]], principal: Principal) -> Select[Any]:
    if principal.org_id is None:
        return statement
    return statement.where(or_(IndexedDocument.org_id == principal.org_id, IndexedDocument.org_id.is_(None)))


def _excerpt(body: str, limit: int = 160) -> str:
    compact = " ".join(body.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _document_result(document: IndexedDocument) -> SearchResult:
    return SearchResult(
        id=document.id,
        org_id=document.org_id,
        title=document.title,
        body_excerpt=_excerpt(document.body),
        score=1.0,
    )


def _mapping_result(row: RowMapping) -> SearchResult:
    body = str(row.get("body", ""))
    return SearchResult(
        id=str(row.get("id", "")),
        org_id=str(row["org_id"]) if row.get("org_id") is not None else None,
        title=str(row.get("title", "")),
        body_excerpt=_excerpt(body),
        score=1.0,
    )


async def _owned_saved_search(
    db: AsyncSession,
    principal: Principal,
    saved_search_id: str,
) -> SavedSearch:
    result = await db.execute(
        select(SavedSearch).where(
            SavedSearch.id == saved_search_id,
            SavedSearch.user_id == principal.user_id,
        )
    )
    saved_search = result.scalar_one_or_none()
    if saved_search is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return saved_search


@router.get("", response_model=SearchResponse)
async def search_documents(
    principal: CurrentPrincipal,
    db: DbSession,
    q: Annotated[str, Query(min_length=1)] = "",
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SearchResponse:
    like_query = f"%{q}%"
    base = select(IndexedDocument).where(
        or_(IndexedDocument.title.like(like_query), IndexedDocument.body.like(like_query))
    )
    base = _tenant_scope(base, principal)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(IndexedDocument.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    documents = result.scalars().all()
    return SearchResponse(
        results=[_document_result(document) for document in documents],
        page=page,
        per_page=per_page,
        total=int(total or 0),
    )


@router.post("/saved", response_model=SavedSearchCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    payload: SavedSearchCreate,
    principal: CurrentPrincipal,
    db: DbSession,
) -> SavedSearchCreateResponse:
    saved_search = SavedSearch(user_id=principal.user_id, name=payload.name, query=payload.query)
    db.add(saved_search)
    await db.commit()
    await db.refresh(saved_search)
    return SavedSearchCreateResponse(
        saved_search_id=saved_search.id,
        name=saved_search.name,
        query=saved_search.query,
    )


@router.get("/saved", response_model=list[SavedSearchResponse])
async def list_saved_searches(principal: CurrentPrincipal, db: DbSession) -> list[SavedSearchResponse]:
    result = await db.execute(
        select(SavedSearch)
        .where(SavedSearch.user_id == principal.user_id)
        .order_by(SavedSearch.created_at.desc())
    )
    return [SavedSearchResponse.model_validate(saved_search) for saved_search in result.scalars()]


@router.post("/saved/{saved_search_id}/run", response_model=SearchResponse)
async def run_saved_search(
    saved_search_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> SearchResponse:
    saved_search = await _owned_saved_search(db, principal, saved_search_id)
    original_query = saved_search.query
    raw_sql = (  # V-T4-008 INTENTIONAL VULN: raw SQL concat from stored query
        f"SELECT * FROM indexed_documents WHERE title LIKE '%{original_query}%' "
        f"OR body LIKE '%{original_query}%'"
    )
    result = await db.execute(text(raw_sql))
    rows = result.mappings().all()
    return SearchResponse(
        results=[_mapping_result(row) for row in rows],
        page=1,
        per_page=len(rows),
        total=len(rows),
    )


@router.delete("/saved/{saved_search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    saved_search_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> None:
    await _owned_saved_search(db, principal, saved_search_id)
    await db.execute(
        delete(SavedSearch).where(
            SavedSearch.id == saved_search_id,
            SavedSearch.user_id == principal.user_id,
        )
    )
    await db.commit()
