from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class PublishContentType(StrEnum):
    VIDEO = "video"
    NOTE = "note"


class PublishPlanStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskRunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TaskErrorType(StrEnum):
    NONE = "none"
    LOGIN_REQUIRED = "login_required"
    CAPTCHA = "captcha"
    RATE_LIMITED = "rate_limited"
    DAILY_LIMIT = "daily_limit"
    CIRCUIT_OPEN = "circuit_open"
    PAGE_CHANGED = "page_changed"
    INVALID_PARAMS = "invalid_params"
    COOLDOWN = "cooldown"
    UNKNOWN = "unknown"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class ApiKeyStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class UserRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


@dataclass(slots=True)
class Workspace:
    id: str
    tenant_id: str
    name: str
    created_at: datetime


@dataclass(slots=True)
class ApiKey:
    id: str
    tenant_id: str
    workspace_id: str
    name: str
    key: str
    status: ApiKeyStatus
    created_at: datetime


@dataclass(slots=True)
class User:
    id: str
    tenant_id: str
    email: str
    display_name: str
    password_hash: str
    created_at: datetime


@dataclass(slots=True)
class AuthSession:
    id: str
    tenant_id: str
    workspace_id: str
    user_id: str
    token: str
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime


class ApprovalAction(StrEnum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(slots=True)
class ApprovalRecord:
    id: str
    tenant_id: str
    workspace_id: str
    plan_id: str
    action: ApprovalAction
    actor_user_id: str
    comment: str
    created_at: datetime


@dataclass(slots=True)
class AiSettings:
    id: str
    tenant_id: str
    workspace_id: str
    user_id: str
    provider: str
    base_url: str
    api_key: str
    model: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class WorkspaceMember:
    id: str
    tenant_id: str
    workspace_id: str
    user_id: str
    role: UserRole
    created_at: datetime


@dataclass(slots=True)
class Account:
    id: str
    tenant_id: str
    workspace_id: str
    platform: str
    account_name: str
    account_file: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime


class AssetType(StrEnum):
    VIDEO = "video"
    IMAGE = "image"


@dataclass(slots=True)
class Asset:
    id: str
    tenant_id: str
    workspace_id: str
    asset_type: AssetType
    path: str
    sha256: str | None
    created_at: datetime


class DraftStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


@dataclass(slots=True)
class ContentDraft:
    id: str
    tenant_id: str
    workspace_id: str
    title: str
    description: str
    tags: list[str]
    asset_ids: list[str]
    status: DraftStatus
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class PublishPlan:
    id: str
    tenant_id: str
    workspace_id: str
    platform: str
    content_type: PublishContentType
    account_name: str
    payload: dict[str, Any]
    draft_id: str | None
    asset_ids: list[str]
    schedule_at: datetime | None
    status: PublishPlanStatus
    created_by: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class Task:
    id: str
    publish_plan_id: str
    status: TaskStatus
    scheduled_at: datetime | None
    attempts: int
    last_error: str | None
    last_error_type: TaskErrorType
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class TaskRun:
    id: str
    task_id: str
    status: TaskRunStatus
    started_at: datetime
    finished_at: datetime | None
    error_message: str | None
    error_type: TaskErrorType


@dataclass(slots=True)
class AuditEvent:
    id: str
    event_type: str
    target_type: str
    target_id: str
    details: dict[str, Any]
    created_at: datetime
