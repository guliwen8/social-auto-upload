from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterator

from conf import BASE_DIR

from .models import (
    Account,
    AccountStatus,
    Asset,
    AssetType,
    ApiKey,
    ApiKeyStatus,
    AuditEvent,
    ContentDraft,
    DraftStatus,
    PublishContentType,
    PublishPlan,
    PublishPlanStatus,
    Task,
    TaskErrorType,
    TaskRun,
    TaskRunStatus,
    TaskStatus,
    User,
    UserRole,
    Workspace,
    WorkspaceMember,
    AuthSession,
    ApprovalAction,
    ApprovalRecord,
    AiSettings,
)

DATA_DIR = Path(BASE_DIR) / "data"
DB_PATH = DATA_DIR / "platform.db"
API_KEY_PATH = DATA_DIR / "platform_api_key.txt"


def utcnow() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()

        def ensure_column(table: str, column: str, definition: str) -> None:
            columns = connection.execute(f"PRAGMA table_info({table})").fetchall()
            existing = {row["name"] for row in columns}
            if column in existing:
                return
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_records (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                action TEXT NOT NULL,
                actor_user_id TEXT NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_settings (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                email TEXT NOT NULL,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workspace_members (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                token TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                name TEXT NOT NULL,
                key TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                account_name TEXT NOT NULL,
                account_file TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                path TEXT NOT NULL,
                sha256 TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS drafts (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                asset_ids_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS publish_plans (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                content_type TEXT NOT NULL,
                account_name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                draft_id TEXT,
                asset_ids_json TEXT NOT NULL DEFAULT '[]',
                schedule_at TEXT,
                status TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                publish_plan_id TEXT NOT NULL,
                status TEXT NOT NULL,
                scheduled_at TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                last_error_type TEXT NOT NULL DEFAULT 'none',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS task_runs (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                error_message TEXT,
                error_type TEXT NOT NULL DEFAULT 'none'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS account_locks (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                account_name TEXT NOT NULL,
                last_run_at TEXT NOT NULL,
                cooldown_seconds INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS failure_circuits (
                id TEXT PRIMARY KEY,
                scope_type TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                window_started_at TEXT NOT NULL,
                failure_count INTEGER NOT NULL,
                last_error_type TEXT NOT NULL,
                open_until TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_policies (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                policy_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_counters (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                day TEXT NOT NULL,
                count INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                details_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # 轻量迁移：已有 DB 的表补齐新增列
        ensure_column("tasks", "last_error_type", "TEXT NOT NULL DEFAULT 'none'")
        ensure_column("task_runs", "error_type", "TEXT NOT NULL DEFAULT 'none'")
        ensure_column("publish_plans", "draft_id", "TEXT")
        ensure_column("publish_plans", "asset_ids_json", "TEXT NOT NULL DEFAULT '[]'")
        ensure_column("users", "password_hash", "TEXT NOT NULL DEFAULT ''")
        ensure_column("publish_plans", "created_by", "TEXT")


def ensure_default_scope() -> tuple[str, str]:
    initialize_database()
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM tenants ORDER BY created_at LIMIT 1")
        tenant_row = cursor.fetchone()
        if tenant_row:
            tenant_id = tenant_row["id"]
        else:
            tenant_id = generate_id("tenant")
            cursor.execute(
                "INSERT INTO tenants (id, name, created_at) VALUES (?, ?, ?)",
                (tenant_id, "default", utcnow().isoformat()),
            )

        cursor.execute(
            "SELECT id FROM workspaces WHERE tenant_id = ? ORDER BY created_at LIMIT 1",
            (tenant_id,),
        )
        workspace_row = cursor.fetchone()
        if workspace_row:
            workspace_id = workspace_row["id"]
        else:
            workspace_id = generate_id("workspace")
            cursor.execute(
                "INSERT INTO workspaces (id, tenant_id, name, created_at) VALUES (?, ?, ?, ?)",
                (workspace_id, tenant_id, "default", utcnow().isoformat()),
            )

        cursor.execute(
            "SELECT id FROM users WHERE tenant_id = ? ORDER BY created_at LIMIT 1",
            (tenant_id,),
        )
        user_row = cursor.fetchone()
        if user_row:
            user_id = user_row["id"]
        else:
            user_id = generate_id("user")
            cursor.execute(
                "INSERT INTO users (id, tenant_id, email, display_name, password_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, tenant_id, "owner@local", "Owner", "", utcnow().isoformat()),
            )

        cursor.execute(
            """
            SELECT id FROM workspace_members
            WHERE tenant_id = ? AND workspace_id = ? AND user_id = ?
            LIMIT 1
            """,
            (tenant_id, workspace_id, user_id),
        )
        member_row = cursor.fetchone()
        if not member_row:
            cursor.execute(
                """
                INSERT INTO workspace_members (id, tenant_id, workspace_id, user_id, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    generate_id("member"),
                    tenant_id,
                    workspace_id,
                    user_id,
                    UserRole.OWNER.value,
                    utcnow().isoformat(),
                ),
            )

    return tenant_id, workspace_id


def _to_workspace(row: sqlite3.Row) -> Workspace:
    return Workspace(
        id=row["id"],
        tenant_id=row["tenant_id"],
        name=row["name"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _to_api_key(row: sqlite3.Row) -> ApiKey:
    return ApiKey(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workspace_id=row["workspace_id"],
        name=row["name"],
        key=row["key"],
        status=ApiKeyStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        tenant_id=row["tenant_id"],
        email=row["email"],
        display_name=row["display_name"],
        password_hash=row["password_hash"] or "",
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _to_auth_session(row: sqlite3.Row) -> AuthSession:
    return AuthSession(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workspace_id=row["workspace_id"],
        user_id=row["user_id"],
        token=row["token"],
        expires_at=datetime.fromisoformat(row["expires_at"]),
        revoked_at=datetime.fromisoformat(row["revoked_at"]) if row["revoked_at"] else None,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _to_approval_record(row: sqlite3.Row) -> ApprovalRecord:
    return ApprovalRecord(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workspace_id=row["workspace_id"],
        plan_id=row["plan_id"],
        action=ApprovalAction(row["action"]),
        actor_user_id=row["actor_user_id"],
        comment=row["comment"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _to_ai_settings(row: sqlite3.Row) -> AiSettings:
    return AiSettings(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workspace_id=row["workspace_id"],
        user_id=row["user_id"],
        provider=row["provider"],
        base_url=row["base_url"],
        api_key=row["api_key"],
        model=row["model"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _to_workspace_member(row: sqlite3.Row) -> WorkspaceMember:
    return WorkspaceMember(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workspace_id=row["workspace_id"],
        user_id=row["user_id"],
        role=UserRole(row["role"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _to_publish_plan(row: sqlite3.Row) -> PublishPlan:
    return PublishPlan(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workspace_id=row["workspace_id"],
        platform=row["platform"],
        content_type=PublishContentType(row["content_type"]),
        account_name=row["account_name"],
        payload=json.loads(row["payload_json"]),
        draft_id=row["draft_id"],
        asset_ids=json.loads(row["asset_ids_json"] or "[]"),
        schedule_at=datetime.fromisoformat(row["schedule_at"]) if row["schedule_at"] else None,
        status=PublishPlanStatus(row["status"]),
        created_by=row["created_by"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _to_account(row: sqlite3.Row) -> Account:
    return Account(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workspace_id=row["workspace_id"],
        platform=row["platform"],
        account_name=row["account_name"],
        account_file=row["account_file"],
        status=AccountStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _to_asset(row: sqlite3.Row) -> Asset:
    return Asset(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workspace_id=row["workspace_id"],
        asset_type=AssetType(row["asset_type"]),
        path=row["path"],
        sha256=row["sha256"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _to_draft(row: sqlite3.Row) -> ContentDraft:
    return ContentDraft(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workspace_id=row["workspace_id"],
        title=row["title"],
        description=row["description"],
        tags=json.loads(row["tags_json"]),
        asset_ids=json.loads(row["asset_ids_json"]),
        status=DraftStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        publish_plan_id=row["publish_plan_id"],
        status=TaskStatus(row["status"]),
        scheduled_at=datetime.fromisoformat(row["scheduled_at"]) if row["scheduled_at"] else None,
        attempts=row["attempts"],
        last_error=row["last_error"],
        last_error_type=TaskErrorType(row["last_error_type"] or TaskErrorType.NONE.value),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _to_task_run(row: sqlite3.Row) -> TaskRun:
    return TaskRun(
        id=row["id"],
        task_id=row["task_id"],
        status=TaskRunStatus(row["status"]),
        started_at=datetime.fromisoformat(row["started_at"]),
        finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
        error_message=row["error_message"],
        error_type=TaskErrorType(row["error_type"] or TaskErrorType.NONE.value),
    )


def list_publish_plans() -> list[PublishPlan]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM publish_plans ORDER BY created_at DESC"
        ).fetchall()
    return [_to_publish_plan(row) for row in rows]


def ensure_default_api_key(tenant_id: str, workspace_id: str) -> ApiKey:
    initialize_database()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM api_keys
            WHERE tenant_id = ? AND workspace_id = ? AND status = ?
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (tenant_id, workspace_id, ApiKeyStatus.ACTIVE.value),
        ).fetchone()
        if row:
            api_key = _to_api_key(row)
            API_KEY_PATH.write_text(api_key.key, encoding="utf-8")
            return api_key

        key_value = f"api_{uuid.uuid4().hex}"
        api_key = ApiKey(
            id=generate_id("key"),
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            name="default",
            key=key_value,
            status=ApiKeyStatus.ACTIVE,
            created_at=utcnow(),
        )
        connection.execute(
            """
            INSERT INTO api_keys (id, tenant_id, workspace_id, name, key, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                api_key.id,
                api_key.tenant_id,
                api_key.workspace_id,
                api_key.name,
                api_key.key,
                api_key.status.value,
                api_key.created_at.isoformat(),
            ),
        )
        API_KEY_PATH.write_text(api_key.key, encoding="utf-8")
        return api_key


def validate_api_key(key_value: str) -> ApiKey | None:
    if not key_value:
        return None
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM api_keys WHERE key = ? AND status = ? LIMIT 1",
            (key_value, ApiKeyStatus.ACTIVE.value),
        ).fetchone()
    return _to_api_key(row) if row else None


def list_api_keys(tenant_id: str, workspace_id: str) -> list[ApiKey]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM api_keys
            WHERE tenant_id = ? AND workspace_id = ?
            ORDER BY created_at DESC
            """,
            (tenant_id, workspace_id),
        ).fetchall()
    return [_to_api_key(row) for row in rows]


def create_workspace(tenant_id: str, name: str) -> Workspace:
    initialize_database()
    workspace = Workspace(
        id=generate_id("workspace"),
        tenant_id=tenant_id,
        name=name,
        created_at=utcnow(),
    )
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO workspaces (id, tenant_id, name, created_at) VALUES (?, ?, ?, ?)",
            (workspace.id, workspace.tenant_id, workspace.name, workspace.created_at.isoformat()),
        )
    return workspace


def get_workspace(workspace_id: str) -> Workspace | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM workspaces WHERE id = ? LIMIT 1", (workspace_id,)).fetchone()
    return _to_workspace(row) if row else None


def list_user_workspaces(tenant_id: str, user_id: str) -> list[Workspace]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT w.*
            FROM workspace_members m
            JOIN workspaces w ON w.id = m.workspace_id
            WHERE m.tenant_id = ? AND m.user_id = ?
            ORDER BY w.created_at ASC
            """,
            (tenant_id, user_id),
        ).fetchall()
    return [_to_workspace(row) for row in rows]


def add_approval_record(
    tenant_id: str,
    workspace_id: str,
    plan_id: str,
    action: ApprovalAction,
    actor_user_id: str,
    comment: str = "",
) -> ApprovalRecord:
    initialize_database()
    record = ApprovalRecord(
        id=generate_id("approval"),
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        plan_id=plan_id,
        action=action,
        actor_user_id=actor_user_id,
        comment=comment or "",
        created_at=utcnow(),
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO approval_records
            (id, tenant_id, workspace_id, plan_id, action, actor_user_id, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.tenant_id,
                record.workspace_id,
                record.plan_id,
                record.action.value,
                record.actor_user_id,
                record.comment,
                record.created_at.isoformat(),
            ),
        )
    return record


def list_approval_records(
    tenant_id: str,
    workspace_id: str,
    plan_id: str | None = None,
    limit: int = 200,
) -> list[ApprovalRecord]:
    initialize_database()
    with get_connection() as connection:
        if plan_id:
            rows = connection.execute(
                """
                SELECT * FROM approval_records
                WHERE tenant_id = ? AND workspace_id = ? AND plan_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (tenant_id, workspace_id, plan_id, int(limit)),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM approval_records
                WHERE tenant_id = ? AND workspace_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (tenant_id, workspace_id, int(limit)),
            ).fetchall()
    return [_to_approval_record(row) for row in rows]


def upsert_ai_settings(
    tenant_id: str,
    workspace_id: str,
    user_id: str,
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
) -> AiSettings:
    initialize_database()
    now = utcnow()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM ai_settings
            WHERE tenant_id = ? AND workspace_id = ? AND user_id = ?
            LIMIT 1
            """,
            (tenant_id, workspace_id, user_id),
        ).fetchone()
        if row:
            connection.execute(
                """
                UPDATE ai_settings
                SET provider = ?, base_url = ?, api_key = ?, model = ?, updated_at = ?
                WHERE id = ?
                """,
                (provider, base_url, api_key, model, now.isoformat(), row["id"]),
            )
            row = connection.execute("SELECT * FROM ai_settings WHERE id = ?", (row["id"],)).fetchone()
            return _to_ai_settings(row)

        settings_id = generate_id("ai")
        connection.execute(
            """
            INSERT INTO ai_settings
            (id, tenant_id, workspace_id, user_id, provider, base_url, api_key, model, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                settings_id,
                tenant_id,
                workspace_id,
                user_id,
                provider,
                base_url,
                api_key,
                model,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        row = connection.execute("SELECT * FROM ai_settings WHERE id = ?", (settings_id,)).fetchone()
        return _to_ai_settings(row)


def get_ai_settings(
    tenant_id: str,
    workspace_id: str,
    user_id: str,
) -> AiSettings | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM ai_settings
            WHERE tenant_id = ? AND workspace_id = ? AND user_id = ?
            LIMIT 1
            """,
            (tenant_id, workspace_id, user_id),
        ).fetchone()
    return _to_ai_settings(row) if row else None


def create_api_key(
    tenant_id: str,
    workspace_id: str,
    name: str,
) -> ApiKey:
    initialize_database()
    api_key = ApiKey(
        id=generate_id("key"),
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        name=name,
        key=f"api_{uuid.uuid4().hex}",
        status=ApiKeyStatus.ACTIVE,
        created_at=utcnow(),
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO api_keys (id, tenant_id, workspace_id, name, key, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                api_key.id,
                api_key.tenant_id,
                api_key.workspace_id,
                api_key.name,
                api_key.key,
                api_key.status.value,
                api_key.created_at.isoformat(),
            ),
        )
    return api_key


def revoke_api_key(api_key_id: str) -> ApiKey:
    initialize_database()
    with get_connection() as connection:
        connection.execute(
            "UPDATE api_keys SET status = ? WHERE id = ?",
            (ApiKeyStatus.REVOKED.value, api_key_id),
        )
        row = connection.execute("SELECT * FROM api_keys WHERE id = ?", (api_key_id,)).fetchone()
    if not row:
        raise RuntimeError(f"API key not found: {api_key_id}")
    return _to_api_key(row)


def rotate_api_key(api_key_id: str) -> ApiKey:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM api_keys WHERE id = ?", (api_key_id,)).fetchone()
        if not row:
            raise RuntimeError(f"API key not found: {api_key_id}")
        old_key = _to_api_key(row)
        connection.execute(
            "UPDATE api_keys SET status = ? WHERE id = ?",
            (ApiKeyStatus.REVOKED.value, api_key_id),
        )
    return create_api_key(old_key.tenant_id, old_key.workspace_id, f"{old_key.name}-rotated")


def create_account(
    tenant_id: str,
    workspace_id: str,
    platform: str,
    account_name: str,
    account_file: str,
    status: AccountStatus = AccountStatus.UNKNOWN,
) -> Account:
    initialize_database()
    now = utcnow()
    account = Account(
        id=generate_id("account"),
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        platform=platform,
        account_name=account_name,
        account_file=account_file,
        status=status,
        created_at=now,
        updated_at=now,
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO accounts
            (id, tenant_id, workspace_id, platform, account_name, account_file, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account.id,
                account.tenant_id,
                account.workspace_id,
                account.platform,
                account.account_name,
                account.account_file,
                account.status.value,
                account.created_at.isoformat(),
                account.updated_at.isoformat(),
            ),
        )
    return account


def list_accounts() -> list[Account]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM accounts ORDER BY created_at DESC").fetchall()
    return [_to_account(row) for row in rows]


def create_asset(
    tenant_id: str,
    workspace_id: str,
    asset_type: AssetType,
    path: str,
    sha256: str | None = None,
) -> Asset:
    initialize_database()
    asset = Asset(
        id=generate_id("asset"),
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        asset_type=asset_type,
        path=path,
        sha256=sha256,
        created_at=utcnow(),
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO assets (id, tenant_id, workspace_id, asset_type, path, sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset.id,
                asset.tenant_id,
                asset.workspace_id,
                asset.asset_type.value,
                asset.path,
                asset.sha256,
                asset.created_at.isoformat(),
            ),
        )
    return asset


def list_assets(tenant_id: str, workspace_id: str) -> list[Asset]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM assets
            WHERE tenant_id = ? AND workspace_id = ?
            ORDER BY created_at DESC
            """,
            (tenant_id, workspace_id),
        ).fetchall()
    return [_to_asset(row) for row in rows]


def create_user(tenant_id: str, email: str, display_name: str) -> User:
    initialize_database()
    user = User(
        id=generate_id("user"),
        tenant_id=tenant_id,
        email=email,
        display_name=display_name,
        password_hash="",
        created_at=utcnow(),
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (id, tenant_id, email, display_name, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user.id,
                user.tenant_id,
                user.email,
                user.display_name,
                user.password_hash,
                user.created_at.isoformat(),
            ),
        )
    return user


def set_user_password_hash(user_id: str, password_hash: str) -> User:
    initialize_database()
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id),
        )
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise RuntimeError(f"User not found: {user_id}")
    return _to_user(row)


def get_user_by_email(tenant_id: str, email: str) -> User | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE tenant_id = ? AND email = ? LIMIT 1",
            (tenant_id, email),
        ).fetchone()
    return _to_user(row) if row else None


def get_user(user_id: str) -> User | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ? LIMIT 1", (user_id,)).fetchone()
    return _to_user(row) if row else None


def create_auth_session(
    tenant_id: str,
    workspace_id: str,
    user_id: str,
    token: str,
    expires_at: datetime,
) -> AuthSession:
    initialize_database()
    session = AuthSession(
        id=generate_id("sess"),
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        revoked_at=None,
        created_at=utcnow(),
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO auth_sessions (id, tenant_id, workspace_id, user_id, token, expires_at, revoked_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.id,
                session.tenant_id,
                session.workspace_id,
                session.user_id,
                session.token,
                session.expires_at.isoformat(),
                None,
                session.created_at.isoformat(),
            ),
        )
    return session


def revoke_auth_session(token: str) -> None:
    initialize_database()
    with get_connection() as connection:
        connection.execute(
            "UPDATE auth_sessions SET revoked_at = ? WHERE token = ?",
            (utcnow().isoformat(), token),
        )


def get_auth_session(token: str, now: datetime | None = None) -> AuthSession | None:
    initialize_database()
    current = now or utcnow()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM auth_sessions
            WHERE token = ? AND revoked_at IS NULL
            LIMIT 1
            """,
            (token,),
        ).fetchone()
    if not row:
        return None
    session = _to_auth_session(row)
    if current >= session.expires_at:
        return None
    return session


def list_users(tenant_id: str) -> list[User]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM users WHERE tenant_id = ? ORDER BY created_at ASC",
            (tenant_id,),
        ).fetchall()
    return [_to_user(row) for row in rows]


def add_workspace_member(
    tenant_id: str,
    workspace_id: str,
    user_id: str,
    role: UserRole,
) -> WorkspaceMember:
    initialize_database()
    member = WorkspaceMember(
        id=generate_id("member"),
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        role=role,
        created_at=utcnow(),
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO workspace_members (id, tenant_id, workspace_id, user_id, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                member.id,
                member.tenant_id,
                member.workspace_id,
                member.user_id,
                member.role.value,
                member.created_at.isoformat(),
            ),
        )
    return member


def list_workspace_members(tenant_id: str, workspace_id: str) -> list[WorkspaceMember]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM workspace_members
            WHERE tenant_id = ? AND workspace_id = ?
            ORDER BY created_at ASC
            """,
            (tenant_id, workspace_id),
        ).fetchall()
    return [_to_workspace_member(row) for row in rows]


def get_workspace_member(tenant_id: str, workspace_id: str, user_id: str) -> WorkspaceMember | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM workspace_members
            WHERE tenant_id = ? AND workspace_id = ? AND user_id = ?
            LIMIT 1
            """,
            (tenant_id, workspace_id, user_id),
        ).fetchone()
    return _to_workspace_member(row) if row else None


def get_default_workspace_member(tenant_id: str, workspace_id: str) -> WorkspaceMember | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM workspace_members
            WHERE tenant_id = ? AND workspace_id = ?
            ORDER BY CASE role
                WHEN 'owner' THEN 1
                WHEN 'admin' THEN 2
                WHEN 'editor' THEN 3
                ELSE 4
            END, created_at ASC
            LIMIT 1
            """,
            (tenant_id, workspace_id),
        ).fetchone()
    return _to_workspace_member(row) if row else None


def create_draft(
    tenant_id: str,
    workspace_id: str,
    title: str,
    description: str,
    tags: list[str],
    asset_ids: list[str],
    status: DraftStatus = DraftStatus.DRAFT,
) -> ContentDraft:
    initialize_database()
    now = utcnow()
    draft = ContentDraft(
        id=generate_id("draft"),
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        title=title,
        description=description,
        tags=tags,
        asset_ids=asset_ids,
        status=status,
        created_at=now,
        updated_at=now,
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO drafts
            (id, tenant_id, workspace_id, title, description, tags_json, asset_ids_json, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft.id,
                draft.tenant_id,
                draft.workspace_id,
                draft.title,
                draft.description,
                json.dumps(draft.tags, ensure_ascii=False),
                json.dumps(draft.asset_ids, ensure_ascii=False),
                draft.status.value,
                draft.created_at.isoformat(),
                draft.updated_at.isoformat(),
            ),
        )
    return draft


def list_drafts(tenant_id: str, workspace_id: str) -> list[ContentDraft]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM drafts
            WHERE tenant_id = ? AND workspace_id = ?
            ORDER BY updated_at DESC
            """,
            (tenant_id, workspace_id),
        ).fetchall()
    return [_to_draft(row) for row in rows]


def get_draft(draft_id: str) -> ContentDraft | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    return _to_draft(row) if row else None


def get_assets_by_ids(asset_ids: list[str]) -> list[Asset]:
    initialize_database()
    if not asset_ids:
        return []
    placeholders = ",".join(["?"] * len(asset_ids))
    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT * FROM assets WHERE id IN ({placeholders})",
            tuple(asset_ids),
        ).fetchall()
    return [_to_asset(row) for row in rows]


def get_account(account_id: str) -> Account | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return _to_account(row) if row else None


def update_account_status(account_id: str, status: AccountStatus) -> Account:
    initialize_database()
    now = utcnow().isoformat()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE accounts
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, now, account_id),
        )
        row = connection.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if not row:
        raise RuntimeError(f"Account not found: {account_id}")
    return _to_account(row)


def get_publish_plan(plan_id: str) -> PublishPlan | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM publish_plans WHERE id = ?",
            (plan_id,),
        ).fetchone()
    return _to_publish_plan(row) if row else None


def create_publish_plan(
    tenant_id: str,
    workspace_id: str,
    platform: str,
    content_type: PublishContentType,
    account_name: str,
    payload: dict,
    draft_id: str | None,
    asset_ids: list[str],
    schedule_at: datetime | None,
    status: PublishPlanStatus = PublishPlanStatus.ACTIVE,
    created_by: str | None = None,
) -> PublishPlan:
    initialize_database()
    now = utcnow()
    plan = PublishPlan(
        id=generate_id("plan"),
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        platform=platform,
        content_type=content_type,
        account_name=account_name,
        payload=payload,
        draft_id=draft_id,
        asset_ids=asset_ids,
        schedule_at=schedule_at,
        status=status,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO publish_plans
            (id, tenant_id, workspace_id, platform, content_type, account_name, payload_json, draft_id, asset_ids_json, schedule_at, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan.id,
                plan.tenant_id,
                plan.workspace_id,
                plan.platform,
                plan.content_type.value,
                plan.account_name,
                json.dumps(plan.payload, ensure_ascii=False),
                plan.draft_id,
                json.dumps(plan.asset_ids, ensure_ascii=False),
                plan.schedule_at.isoformat() if plan.schedule_at else None,
                plan.status.value,
                plan.created_by,
                plan.created_at.isoformat(),
                plan.updated_at.isoformat(),
            ),
        )
    return plan


def update_publish_plan_status(plan_id: str, status: PublishPlanStatus) -> PublishPlan:
    initialize_database()
    now = utcnow().isoformat()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE publish_plans
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, now, plan_id),
        )
        row = connection.execute("SELECT * FROM publish_plans WHERE id = ?", (plan_id,)).fetchone()
    if not row:
        raise RuntimeError(f"Publish plan not found: {plan_id}")
    return _to_publish_plan(row)


def create_task(
    publish_plan_id: str,
    scheduled_at: datetime | None,
    status: TaskStatus = TaskStatus.QUEUED,
) -> Task:
    initialize_database()
    now = utcnow()
    task = Task(
        id=generate_id("task"),
        publish_plan_id=publish_plan_id,
        status=status,
        scheduled_at=scheduled_at,
        attempts=0,
        last_error=None,
        last_error_type=TaskErrorType.NONE,
        created_at=now,
        updated_at=now,
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO tasks (id, publish_plan_id, status, scheduled_at, attempts, last_error, last_error_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.id,
                task.publish_plan_id,
                task.status.value,
                task.scheduled_at.isoformat() if task.scheduled_at else None,
                task.attempts,
                task.last_error,
                task.last_error_type.value,
                task.created_at.isoformat(),
                task.updated_at.isoformat(),
            ),
        )
    return task


def get_task(task_id: str) -> Task | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return _to_task(row) if row else None


def get_task_by_publish_plan_id(plan_id: str) -> Task | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM tasks WHERE publish_plan_id = ? ORDER BY created_at DESC LIMIT 1",
            (plan_id,),
        ).fetchone()
    return _to_task(row) if row else None


def list_tasks() -> list[Task]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    return [_to_task(row) for row in rows]


def list_due_tasks(now: datetime | None = None) -> list[Task]:
    initialize_database()
    current_time = (now or utcnow()).isoformat()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM tasks
            WHERE status = ?
              AND (scheduled_at IS NULL OR scheduled_at = '' OR scheduled_at <= ?)
            ORDER BY created_at ASC
            """,
            (TaskStatus.QUEUED.value, current_time),
        ).fetchall()
    return [_to_task(row) for row in rows]


def enforce_account_cooldown(
    platform: str,
    account_name: str,
    cooldown_seconds: int,
    now: datetime | None = None,
) -> tuple[bool, datetime]:
    """
    返回 (allowed, next_allowed_at)。
    - allowed=True：允许执行，同时会把 last_run_at 更新为 now
    - allowed=False：不允许执行，next_allowed_at 表示下次允许时间
    """
    initialize_database()
    current = now or utcnow()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM account_locks
            WHERE platform = ? AND account_name = ?
            LIMIT 1
            """,
            (platform, account_name),
        ).fetchone()

        if not row:
            lock_id = generate_id("lock")
            connection.execute(
                """
                INSERT INTO account_locks
                (id, platform, account_name, last_run_at, cooldown_seconds, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lock_id,
                    platform,
                    account_name,
                    current.isoformat(),
                    cooldown_seconds,
                    current.isoformat(),
                    current.isoformat(),
                ),
            )
            return True, current

        last_run_at = datetime.fromisoformat(row["last_run_at"])
        effective_cooldown = int(row["cooldown_seconds"] or cooldown_seconds)
        next_allowed_at = last_run_at + timedelta(seconds=effective_cooldown)
        if current < next_allowed_at:
            return False, next_allowed_at

        connection.execute(
            """
            UPDATE account_locks
            SET last_run_at = ?, cooldown_seconds = ?, updated_at = ?
            WHERE id = ?
            """,
            (current.isoformat(), cooldown_seconds, current.isoformat(), row["id"]),
        )
        return True, current


def check_and_track_failure_circuit(
    scope_type: str,
    scope_key: str,
    error_type: TaskErrorType,
    *,
    threshold: int,
    window_seconds: int,
    open_seconds: int,
    now: datetime | None = None,
) -> tuple[bool, datetime | None, int]:
    """
    返回 (allowed, open_until, failure_count)。
    - allowed=True：当前未熔断，可继续执行
    - allowed=False：当前熔断打开，open_until 表示恢复时间
    """
    initialize_database()
    current = now or utcnow()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM failure_circuits
            WHERE scope_type = ? AND scope_key = ?
            LIMIT 1
            """,
            (scope_type, scope_key),
        ).fetchone()

        if not row:
            circuit_id = generate_id("circuit")
            open_until = current + timedelta(seconds=open_seconds) if threshold <= 1 else None
            connection.execute(
                """
                INSERT INTO failure_circuits
                (id, scope_type, scope_key, window_started_at, failure_count, last_error_type, open_until, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    circuit_id,
                    scope_type,
                    scope_key,
                    current.isoformat(),
                    1,
                    error_type.value,
                    open_until.isoformat() if open_until else None,
                    current.isoformat(),
                    current.isoformat(),
                ),
            )
            return open_until is None, open_until, 1

        window_started_at = datetime.fromisoformat(row["window_started_at"])
        open_until = datetime.fromisoformat(row["open_until"]) if row["open_until"] else None
        if open_until and current < open_until:
            return False, open_until, int(row["failure_count"])

        if current > window_started_at + timedelta(seconds=window_seconds):
            failure_count = 1
            window_started_at = current
        else:
            failure_count = int(row["failure_count"]) + 1

        new_open_until = current + timedelta(seconds=open_seconds) if failure_count >= threshold else None
        connection.execute(
            """
            UPDATE failure_circuits
            SET window_started_at = ?, failure_count = ?, last_error_type = ?, open_until = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                window_started_at.isoformat(),
                failure_count,
                error_type.value,
                new_open_until.isoformat() if new_open_until else None,
                current.isoformat(),
                row["id"],
            ),
        )
        return new_open_until is None, new_open_until, failure_count


def get_open_failure_circuit(
    scope_type: str,
    scope_key: str,
    now: datetime | None = None,
) -> tuple[bool, datetime | None, int]:
    initialize_database()
    current = now or utcnow()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM failure_circuits
            WHERE scope_type = ? AND scope_key = ?
            LIMIT 1
            """,
            (scope_type, scope_key),
        ).fetchone()
    if not row or not row["open_until"]:
        return False, None, int(row["failure_count"]) if row else 0
    open_until = datetime.fromisoformat(row["open_until"])
    return current < open_until, open_until, int(row["failure_count"])


def reset_failure_circuit(scope_type: str, scope_key: str) -> None:
    initialize_database()
    now = utcnow()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE failure_circuits
            SET failure_count = 0, open_until = NULL, updated_at = ?
            WHERE scope_type = ? AND scope_key = ?
            """,
            (now.isoformat(), scope_type, scope_key),
        )


def upsert_risk_policy(
    tenant_id: str,
    workspace_id: str,
    scope_type: str,
    scope_key: str,
    policy: dict,
) -> dict:
    initialize_database()
    now = utcnow()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM risk_policies
            WHERE tenant_id = ? AND workspace_id = ? AND scope_type = ? AND scope_key = ?
            LIMIT 1
            """,
            (tenant_id, workspace_id, scope_type, scope_key),
        ).fetchone()
        if row:
            connection.execute(
                """
                UPDATE risk_policies
                SET policy_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (json.dumps(policy, ensure_ascii=False), now.isoformat(), row["id"]),
            )
            policy_id = row["id"]
            created_at = row["created_at"]
        else:
            policy_id = generate_id("policy")
            created_at = now.isoformat()
            connection.execute(
                """
                INSERT INTO risk_policies
                (id, tenant_id, workspace_id, scope_type, scope_key, policy_json, updated_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    policy_id,
                    tenant_id,
                    workspace_id,
                    scope_type,
                    scope_key,
                    json.dumps(policy, ensure_ascii=False),
                    now.isoformat(),
                    created_at,
                ),
            )
    return {
        "id": policy_id,
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "scope_type": scope_type,
        "scope_key": scope_key,
        "policy": policy,
        "updated_at": now.isoformat(),
        "created_at": created_at,
    }


def get_risk_policy(
    tenant_id: str,
    workspace_id: str,
    scope_type: str,
    scope_key: str,
) -> dict | None:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM risk_policies
            WHERE tenant_id = ? AND workspace_id = ? AND scope_type = ? AND scope_key = ?
            LIMIT 1
            """,
            (tenant_id, workspace_id, scope_type, scope_key),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "tenant_id": row["tenant_id"],
        "workspace_id": row["workspace_id"],
        "scope_type": row["scope_type"],
        "scope_key": row["scope_key"],
        "policy": json.loads(row["policy_json"] or "{}"),
        "updated_at": row["updated_at"],
        "created_at": row["created_at"],
    }


def list_risk_policies(tenant_id: str, workspace_id: str) -> list[dict]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM risk_policies
            WHERE tenant_id = ? AND workspace_id = ?
            ORDER BY updated_at DESC
            """,
            (tenant_id, workspace_id),
        ).fetchall()
    result: list[dict] = []
    for row in rows:
        result.append(
            {
                "id": row["id"],
                "scope_type": row["scope_type"],
                "scope_key": row["scope_key"],
                "policy": json.loads(row["policy_json"] or "{}"),
                "updated_at": row["updated_at"],
            }
        )
    return result


def increment_daily_counter(
    tenant_id: str,
    workspace_id: str,
    scope_type: str,
    scope_key: str,
    day: str,
    delta: int = 1,
) -> int:
    initialize_database()
    now = utcnow()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM daily_counters
            WHERE tenant_id = ? AND workspace_id = ? AND scope_type = ? AND scope_key = ? AND day = ?
            LIMIT 1
            """,
            (tenant_id, workspace_id, scope_type, scope_key, day),
        ).fetchone()
        if row:
            new_count = int(row["count"]) + delta
            connection.execute(
                """
                UPDATE daily_counters
                SET count = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_count, now.isoformat(), row["id"]),
            )
            return new_count
        counter_id = generate_id("counter")
        connection.execute(
            """
            INSERT INTO daily_counters
            (id, tenant_id, workspace_id, scope_type, scope_key, day, count, updated_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                counter_id,
                tenant_id,
                workspace_id,
                scope_type,
                scope_key,
                day,
                delta,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        return delta


def get_daily_counter(
    tenant_id: str,
    workspace_id: str,
    scope_type: str,
    scope_key: str,
    day: str,
) -> int:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT count FROM daily_counters
            WHERE tenant_id = ? AND workspace_id = ? AND scope_type = ? AND scope_key = ? AND day = ?
            LIMIT 1
            """,
            (tenant_id, workspace_id, scope_type, scope_key, day),
        ).fetchone()
    return int(row["count"]) if row else 0


def update_task_status(
    task_id: str,
    status: TaskStatus,
    last_error: str | None = None,
    last_error_type: TaskErrorType | None = None,
) -> Task:
    initialize_database()
    now = utcnow().isoformat()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE tasks
            SET status = ?,
                last_error = ?,
                last_error_type = COALESCE(?, last_error_type),
                updated_at = ?,
                attempts = attempts + CASE WHEN ? = 'running' THEN 1 ELSE 0 END
            WHERE id = ?
            """,
            (status.value, last_error, last_error_type.value if last_error_type else None, now, status.value, task_id),
        )
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        raise RuntimeError(f"Task not found: {task_id}")
    return _to_task(row)


def update_task_schedule(task_id: str, scheduled_at: datetime | None) -> Task:
    initialize_database()
    now = utcnow().isoformat()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE tasks
            SET scheduled_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (scheduled_at.isoformat() if scheduled_at else None, now, task_id),
        )
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        raise RuntimeError(f"Task not found: {task_id}")
    return _to_task(row)


def create_task_run(task_id: str) -> TaskRun:
    initialize_database()
    task_run = TaskRun(
        id=generate_id("run"),
        task_id=task_id,
        status=TaskRunStatus.RUNNING,
        started_at=utcnow(),
        finished_at=None,
        error_message=None,
        error_type=TaskErrorType.NONE,
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO task_runs (id, task_id, status, started_at, finished_at, error_message, error_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_run.id,
                task_run.task_id,
                task_run.status.value,
                task_run.started_at.isoformat(),
                None,
                None,
                task_run.error_type.value,
            ),
        )
    return task_run


def finish_task_run(
    run_id: str,
    status: TaskRunStatus,
    error_message: str | None = None,
    error_type: TaskErrorType | None = None,
) -> TaskRun:
    initialize_database()
    finished_at = utcnow().isoformat()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE task_runs
            SET status = ?, finished_at = ?, error_message = ?, error_type = COALESCE(?, error_type)
            WHERE id = ?
            """,
            (status.value, finished_at, error_message, error_type.value if error_type else None, run_id),
        )
        row = connection.execute("SELECT * FROM task_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        raise RuntimeError(f"Task run not found: {run_id}")
    return _to_task_run(row)


def list_task_runs(task_id: str) -> list[TaskRun]:
    initialize_database()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM task_runs WHERE task_id = ? ORDER BY started_at DESC",
            (task_id,),
        ).fetchall()
    return [_to_task_run(row) for row in rows]


def create_audit_event(
    event_type: str,
    target_type: str,
    target_id: str,
    details: dict,
) -> AuditEvent:
    initialize_database()
    audit_event = AuditEvent(
        id=generate_id("audit"),
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        details=details,
        created_at=utcnow(),
    )
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_events (id, event_type, target_type, target_id, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                audit_event.id,
                audit_event.event_type,
                audit_event.target_type,
                audit_event.target_id,
                json.dumps(audit_event.details, ensure_ascii=False),
                audit_event.created_at.isoformat(),
            ),
        )
    return audit_event
