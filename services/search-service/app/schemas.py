from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SearchResult(BaseModel):
    id: str
    org_id: str | None = None
    title: str
    body_excerpt: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
    page: int
    per_page: int
    total: int


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    query: str = Field(min_length=1)


class SavedSearchCreateResponse(BaseModel):
    saved_search_id: str
    name: str
    query: str


class SavedSearchResponse(BaseModel):
    id: str
    user_id: str
    name: str
    query: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthLiveResponse(BaseModel):
    status: str


class HealthReadyResponse(BaseModel):
    status: str
    build_hash: str
    git_sha: str
    service_version: str
