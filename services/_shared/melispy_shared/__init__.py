"""Shared Python primitives for Melispy services."""

from melispy_shared.audit import AuditEntry, emit_audit, verify_chain
from melispy_shared.auth import (
    issue_jwt,
    legacy_verify,
    verify_jwt,
    verify_jwt_kid_path,
    verify_jwt_unsafe_alg_confusion,
)
from melispy_shared.db import SessionLocal, engine, get_db, with_tenant
from melispy_shared.models import AuditLog, Base, TenantMixin, TimestampMixin, UUIDPKMixin
from melispy_shared.policies import OPAClient
from melispy_shared.rate_limit import RateLimitMiddleware, check_rate_limit
from melispy_shared.tracing import RequestIdMiddleware, configure_logging, request_id_var

__version__ = "0.1.0"

__all__ = [
    "AuditEntry",
    "AuditLog",
    "Base",
    "OPAClient",
    "RateLimitMiddleware",
    "RequestIdMiddleware",
    "SessionLocal",
    "TenantMixin",
    "TimestampMixin",
    "UUIDPKMixin",
    "__version__",
    "check_rate_limit",
    "configure_logging",
    "emit_audit",
    "engine",
    "get_db",
    "issue_jwt",
    "legacy_verify",
    "request_id_var",
    "verify_chain",
    "verify_jwt",
    "verify_jwt_kid_path",
    "verify_jwt_unsafe_alg_confusion",
    "with_tenant",
]
