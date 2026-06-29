from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sau.models import (
    BilibiliVideoUploadRequest,
    DouyinNoteUploadRequest,
    DouyinVideoUploadRequest,
    KuaishouNoteUploadRequest,
    KuaishouVideoUploadRequest,
    TencentVideoUploadRequest,
    XiaohongshuNoteUploadRequest,
    XiaohongshuVideoUploadRequest,
    YouTubeVideoUploadRequest,
)
from sau.runtime import resolve_account_file
from sau.services import service as upload_service

from sau_ai.openai_compat import rewrite_for_platform

from .models import (
    AccountStatus,
    ApprovalAction,
    AssetType,
    PublishContentType,
    PublishPlanStatus,
    TaskErrorType,
    TaskStatus,
    TaskRunStatus,
    UserRole,
)
from .storage import (
    API_KEY_PATH,
    add_workspace_member,
    check_and_track_failure_circuit,
    create_asset,
    create_account,
    create_api_key,
    create_audit_event,
    create_publish_plan,
    create_task,
    create_task_run,
    create_draft,
    create_user,
    create_auth_session,
    create_workspace,
    enforce_account_cooldown,
    ensure_default_scope,
    ensure_default_api_key,
    finish_task_run,
    get_account,
    get_assets_by_ids,
    get_auth_session,
    get_default_workspace_member,
    get_draft,
    get_open_failure_circuit,
    get_publish_plan,
    get_task_by_publish_plan_id,
    get_task,
    get_user,
    get_user_by_email,
    get_workspace_member,
    get_daily_counter,
    get_workspace,
    list_accounts,
    list_assets,
    list_api_keys,
    list_due_tasks,
    list_drafts,
    list_publish_plans,
    list_task_runs,
    list_tasks,
    list_users,
    list_workspace_members,
    list_user_workspaces,
    get_ai_settings,
    revoke_api_key,
    revoke_auth_session,
    rotate_api_key,
    reset_failure_circuit,
    set_user_password_hash,
    upsert_risk_policy,
    get_risk_policy,
    list_risk_policies,
    increment_daily_counter,
    add_approval_record,
    list_approval_records,
    upsert_ai_settings,
    update_account_status,
    update_publish_plan_status,
    update_task_schedule,
    update_task_status,
)

DEFAULT_COOLDOWN_SECONDS = 60
ACCOUNT_FAILURE_THRESHOLD = 3
PLATFORM_FAILURE_THRESHOLD = 8
FAILURE_WINDOW_SECONDS = 600
ACCOUNT_CIRCUIT_OPEN_SECONDS = 600
PLATFORM_CIRCUIT_OPEN_SECONDS = 300
DEFAULT_DAILY_LIMIT = 50
STALE_RUNNING_TASK_TIMEOUT = timedelta(hours=2)
STALE_RUNNING_TASK_MESSAGE = "任务长时间停留在执行中且无结果回写，系统已自动清理；实际发布结果需人工核对"


def classify_error(exc: Exception) -> TaskErrorType:
    message = str(exc).lower()
    if "cooldown" in message:
        return TaskErrorType.COOLDOWN
    if "captcha" in message or "验证码" in message or "verify" in message:
        return TaskErrorType.CAPTCHA
    if "too many" in message or "rate limit" in message or "频繁" in message or "限流" in message:
        return TaskErrorType.RATE_LIMITED
    if "cookie" in message or "login" in message or "登录" in message:
        return TaskErrorType.LOGIN_REQUIRED
    if "timeout" in message or "locator" in message or "selector" in message:
        return TaskErrorType.PAGE_CHANGED
    if "file not found" in message or "invalid" in message or "argument" in message:
        return TaskErrorType.INVALID_PARAMS
    return TaskErrorType.UNKNOWN


def _parse_schedule(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None
    return datetime.fromisoformat(raw_value)


def _materialize_path_list(values: list[str] | None) -> list[Path]:
    return [Path(value) for value in values or []]


def role_allows(member_role: UserRole, required_role: UserRole) -> bool:
    ranking = {
        UserRole.VIEWER: 1,
        UserRole.EDITOR: 2,
        UserRole.ADMIN: 3,
        UserRole.OWNER: 4,
    }
    return ranking[member_role] >= ranking[required_role]


SESSION_TTL_DAYS = 7


def merge_policy(base: dict, override: dict | None) -> dict:
    if not override:
        return dict(base)
    merged = dict(base)
    merged.update({k: v for k, v in override.items() if v is not None})
    return merged


class PlatformApplicationService:
    """最小控制面应用服务。"""

    def _scope(self, data: dict[str, Any] | None = None, scope: dict[str, str] | None = None) -> dict[str, str]:
        base = scope or self.get_default_scope()
        if not data:
            return base
        return {
            "tenant_id": data.get("tenant_id") or base["tenant_id"],
            "workspace_id": data.get("workspace_id") or base["workspace_id"],
        }

    def get_default_scope(self) -> dict[str, str]:
        tenant_id, workspace_id = ensure_default_scope()
        return {
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
        }

    def ensure_bootstrap(self) -> dict[str, str]:
        scope = self.get_default_scope()
        api_key = ensure_default_api_key(scope["tenant_id"], scope["workspace_id"])
        return {
            **scope,
            "api_key_path": str(API_KEY_PATH),
            "api_key": api_key.key,
        }

    def _cleanup_stale_running_tasks(self) -> int:
        cutoff = datetime.now(UTC) - STALE_RUNNING_TASK_TIMEOUT
        cleaned_count = 0
        for task in list_tasks():
            if task.status != TaskStatus.RUNNING:
                continue
            if task.updated_at >= cutoff:
                continue
            update_task_status(
                task.id,
                TaskStatus.FAILED,
                last_error=STALE_RUNNING_TASK_MESSAGE,
                last_error_type=TaskErrorType.UNKNOWN,
            )
            for run in list_task_runs(task.id):
                if run.status == TaskRunStatus.RUNNING:
                    finish_task_run(
                        run.id,
                        TaskRunStatus.FAILED,
                        error_message=STALE_RUNNING_TASK_MESSAGE,
                        error_type=TaskErrorType.UNKNOWN,
                    )
            create_audit_event(
                event_type="task.cleaned_stale_running",
                target_type="task",
                target_id=task.id,
                details={
                    "publish_plan_id": task.publish_plan_id,
                    "previous_status": TaskStatus.RUNNING.value,
                    "updated_at": task.updated_at.isoformat(),
                    "timeout_seconds": int(STALE_RUNNING_TASK_TIMEOUT.total_seconds()),
                },
            )
            cleaned_count += 1
        return cleaned_count

    def list_api_keys(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scope = self._scope(scope=scope)
        keys = list_api_keys(scope["tenant_id"], scope["workspace_id"])
        result: list[dict[str, Any]] = []
        for item in keys:
            masked = item.key[:8] + "..." + item.key[-4:]
            result.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "status": item.status.value,
                    "key_masked": masked,
                    "created_at": item.created_at.isoformat(),
                }
            )
        return result

    def resolve_actor(self, scope: dict[str, str], user_id: str | None = None) -> dict[str, Any] | None:
        member = None
        if user_id:
            member = get_workspace_member(scope["tenant_id"], scope["workspace_id"], user_id)
        if not member:
            member = get_default_workspace_member(scope["tenant_id"], scope["workspace_id"])
        if not member:
            return None
        users = {item.id: item for item in list_users(scope["tenant_id"])}
        user = users.get(member.user_id)
        return {
            "user_id": member.user_id,
            "role": member.role.value,
            "email": user.email if user else "",
            "display_name": user.display_name if user else member.user_id,
        }

    def auth_register(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        from .auth import hash_password

        scoped = self._scope(data, scope)
        email = str(data["email"]).strip().lower()
        password = str(data["password"]).strip()
        display_name = str(data.get("display_name") or email).strip()
        if len(password) < 8:
            raise RuntimeError("password too short")

        existed = get_user_by_email(scoped["tenant_id"], email)
        if existed:
            raise RuntimeError("email already registered")

        user = create_user(scoped["tenant_id"], email, display_name)
        user = set_user_password_hash(user.id, hash_password(password))

        # 默认加入当前工作区：首个用户为 owner，否则 editor
        members = list_workspace_members(scoped["tenant_id"], scoped["workspace_id"])
        role = UserRole.OWNER if len(members) == 0 else UserRole.EDITOR
        add_workspace_member(
            tenant_id=scoped["tenant_id"],
            workspace_id=scoped["workspace_id"],
            user_id=user.id,
            role=role,
        )
        create_audit_event(
            event_type="auth.registered",
            target_type="user",
            target_id=user.id,
            details={"email": user.email, "role": role.value},
        )
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
            },
            "role": role.value,
        }

    def auth_login(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        from .auth import generate_session_token, verify_password

        scoped = self._scope(data, scope)
        email = str(data["email"]).strip().lower()
        password = str(data["password"]).strip()
        user = get_user_by_email(scoped["tenant_id"], email)
        if not user or not user.password_hash:
            raise RuntimeError("invalid credentials")
        if not verify_password(password, user.password_hash):
            raise RuntimeError("invalid credentials")

        member = get_workspace_member(scoped["tenant_id"], scoped["workspace_id"], user.id)
        if not member:
            # 对已有账号但没加入工作区的情况做兜底：默认 editor
            member = add_workspace_member(
                tenant_id=scoped["tenant_id"],
                workspace_id=scoped["workspace_id"],
                user_id=user.id,
                role=UserRole.EDITOR,
            )

        token = generate_session_token()
        expires_at = datetime.now(UTC).replace(microsecond=0) + timedelta(days=SESSION_TTL_DAYS)
        session = create_auth_session(
            tenant_id=scoped["tenant_id"],
            workspace_id=scoped["workspace_id"],
            user_id=user.id,
            token=token,
            expires_at=expires_at,
        )
        create_audit_event(
            event_type="auth.logged_in",
            target_type="user",
            target_id=user.id,
            details={"workspace_id": scoped["workspace_id"]},
        )
        return {
            "token": session.token,
            "expires_at": session.expires_at.isoformat(),
            "user": {"id": user.id, "email": user.email, "display_name": user.display_name},
            "role": member.role.value,
        }

    def auth_me(self, token: str) -> dict[str, Any] | None:
        session = get_auth_session(token)
        if not session:
            return None
        user = get_user(session.user_id)
        if not user:
            return None
        member = get_workspace_member(session.tenant_id, session.workspace_id, user.id)
        return {
            "tenant_id": session.tenant_id,
            "workspace_id": session.workspace_id,
            "user_id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": member.role.value if member else UserRole.VIEWER.value,
        }

    def auth_logout(self, token: str) -> None:
        revoke_auth_session(token)

    def auth_list_workspaces(self, token: str) -> list[dict[str, Any]]:
        session = get_auth_session(token)
        if not session:
            raise RuntimeError("unauthorized")
        workspaces = list_user_workspaces(session.tenant_id, session.user_id)
        return [asdict(item) for item in workspaces]

    def auth_switch_workspace(self, token: str, workspace_id: str) -> dict[str, Any]:
        from .auth import generate_session_token

        session = get_auth_session(token)
        if not session:
            raise RuntimeError("unauthorized")
        workspace = get_workspace(workspace_id)
        if not workspace or workspace.tenant_id != session.tenant_id:
            raise RuntimeError("workspace not found")
        member = get_workspace_member(session.tenant_id, workspace_id, session.user_id)
        if not member:
            raise RuntimeError("not a workspace member")

        revoke_auth_session(token)
        new_token = generate_session_token()
        expires_at = datetime.now(UTC).replace(microsecond=0) + timedelta(days=SESSION_TTL_DAYS)
        new_session = create_auth_session(
            tenant_id=session.tenant_id,
            workspace_id=workspace_id,
            user_id=session.user_id,
            token=new_token,
            expires_at=expires_at,
        )
        create_audit_event(
            event_type="auth.workspace_switched",
            target_type="auth_session",
            target_id=new_session.id,
            details={"workspace_id": workspace_id},
        )
        return {"token": new_session.token, "expires_at": new_session.expires_at.isoformat(), "workspace_id": workspace_id}

    def list_workspaces(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        # 仅用于 admin 侧管理：列出 tenant 下全部 workspace
        with_workspace: list[dict[str, Any]] = []
        # 复用 join：把所有用户 workspaces 的 union 拉出来（最小实现）
        for user in list_users(scoped["tenant_id"]):
            for ws in list_user_workspaces(scoped["tenant_id"], user.id):
                with_workspace.append(asdict(ws))
        # 去重
        dedup: dict[str, dict[str, Any]] = {}
        for ws in with_workspace:
            dedup[ws["id"]] = ws
        return list(dedup.values())

    def create_workspace(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(data, scope)
        name = str(data.get("name") or "workspace").strip()
        workspace = create_workspace(scoped["tenant_id"], name)
        create_audit_event(
            event_type="workspace.created",
            target_type="workspace",
            target_id=workspace.id,
            details={"name": workspace.name},
        )
        # 创建者（默认 workspace 的 owner）如果在当前 scope 有 actor，就补成员关系
        creator_id = data.get("__actor_user_id")
        if creator_id:
            add_workspace_member(
                tenant_id=scoped["tenant_id"],
                workspace_id=workspace.id,
                user_id=str(creator_id),
                role=UserRole.OWNER,
            )
        return asdict(workspace)

    def list_risk_policies(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        return list_risk_policies(scoped["tenant_id"], scoped["workspace_id"])

    def upsert_risk_policy(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(data, scope)
        scope_type = str(data["scope_type"]).strip()
        scope_key = str(data["scope_key"]).strip()
        policy = dict(data.get("policy") or {})
        result = upsert_risk_policy(
            tenant_id=scoped["tenant_id"],
            workspace_id=scoped["workspace_id"],
            scope_type=scope_type,
            scope_key=scope_key,
            policy=policy,
        )
        create_audit_event(
            event_type="risk_policy.upserted",
            target_type="risk_policy",
            target_id=result["id"],
            details={"scope_type": scope_type, "scope_key": scope_key},
        )
        return result

    def create_api_key(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(data, scope)
        name = str(data.get("name") or "unnamed").strip()
        api_key = create_api_key(scoped["tenant_id"], scoped["workspace_id"], name)
        create_audit_event(
            event_type="api_key.created",
            target_type="api_key",
            target_id=api_key.id,
            details={"name": api_key.name},
        )
        return {
            "id": api_key.id,
            "name": api_key.name,
            "key": api_key.key,
            "status": api_key.status.value,
            "created_at": api_key.created_at.isoformat(),
        }

    def revoke_api_key(self, api_key_id: str, scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(scope=scope)
        matching = {item.id: item for item in list_api_keys(scoped["tenant_id"], scoped["workspace_id"])}
        if api_key_id not in matching:
            raise RuntimeError(f"API key is outside current workspace: {api_key_id}")
        api_key = revoke_api_key(api_key_id)
        create_audit_event(
            event_type="api_key.revoked",
            target_type="api_key",
            target_id=api_key.id,
            details={"name": api_key.name},
        )
        return {
            "id": api_key.id,
            "name": api_key.name,
            "status": api_key.status.value,
        }

    def rotate_api_key(self, api_key_id: str, scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(scope=scope)
        matching = {item.id: item for item in list_api_keys(scoped["tenant_id"], scoped["workspace_id"])}
        if api_key_id not in matching:
            raise RuntimeError(f"API key is outside current workspace: {api_key_id}")
        api_key = rotate_api_key(api_key_id)
        create_audit_event(
            event_type="api_key.rotated",
            target_type="api_key",
            target_id=api_key.id,
            details={"name": api_key.name},
        )
        return {
            "id": api_key.id,
            "name": api_key.name,
            "key": api_key.key,
            "status": api_key.status.value,
            "created_at": api_key.created_at.isoformat(),
        }

    def create_asset(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(data, scope)
        tenant_id = scoped["tenant_id"]
        workspace_id = scoped["workspace_id"]
        asset_type = AssetType(str(data["asset_type"]).strip())
        path = str(data["path"]).strip()
        sha256 = data.get("sha256")

        asset = create_asset(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            asset_type=asset_type,
            path=path,
            sha256=sha256,
        )
        create_audit_event(
            event_type="asset.created",
            target_type="asset",
            target_id=asset.id,
            details={"asset_type": asset.asset_type.value, "path": asset.path},
        )
        return asdict(asset)

    def list_assets(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        return [asdict(asset) for asset in list_assets(scoped["tenant_id"], scoped["workspace_id"])]

    def create_draft(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(data, scope)
        tenant_id = scoped["tenant_id"]
        workspace_id = scoped["workspace_id"]
        title = str(data["title"]).strip()
        description = str(data.get("description", "")).strip()
        tags = list(data.get("tags") or [])
        asset_ids = list(data.get("asset_ids") or [])

        draft = create_draft(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            title=title,
            description=description,
            tags=tags,
            asset_ids=asset_ids,
        )
        create_audit_event(
            event_type="draft.created",
            target_type="draft",
            target_id=draft.id,
            details={"title": draft.title, "asset_ids": draft.asset_ids},
        )
        return asdict(draft)

    def list_drafts(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        return [asdict(draft) for draft in list_drafts(scoped["tenant_id"], scoped["workspace_id"])]

    def ai_rewrite(self, data: dict[str, Any]) -> dict[str, Any]:
        platform = str(data.get("platform") or "").strip() or "generic"
        title = str(data.get("title") or "").strip()
        description = str(data.get("description") or "").strip()
        tags = list(data.get("tags") or [])
        scoped = self._scope(data.get("__scope"))
        actor_user_id = str(data.get("__actor_user_id") or "").strip()
        settings = None
        if actor_user_id:
            settings = get_ai_settings(scoped["tenant_id"], scoped["workspace_id"], actor_user_id)
        if not settings:
            result = rewrite_for_platform(platform=platform, title=title, description=description, tags=tags)
        else:
            result = rewrite_for_platform(
                platform=platform,
                title=title,
                description=description,
                tags=tags,
                base_url=settings.base_url,
                api_key=settings.api_key,
                model=settings.model,
            )
        return {
            "title": result.title,
            "description": result.description,
            "tags": result.tags,
            "provider": result.provider,
        }

    def get_ai_settings(self, scope: dict[str, str], actor_user_id: str) -> dict[str, Any] | None:
        settings = get_ai_settings(scope["tenant_id"], scope["workspace_id"], actor_user_id)
        if not settings:
            return None
        masked = settings.api_key[:6] + "..." + settings.api_key[-4:] if settings.api_key else ""
        return {
            "provider": settings.provider,
            "base_url": settings.base_url,
            "model": settings.model,
            "api_key_masked": masked,
            "updated_at": settings.updated_at.isoformat(),
        }

    def upsert_ai_settings(self, data: dict[str, Any], scope: dict[str, str], actor_user_id: str) -> dict[str, Any]:
        provider = str(data.get("provider") or "openai_compat").strip()
        base_url = str(data.get("base_url") or "").strip()
        api_key = str(data.get("api_key") or "").strip()
        model = str(data.get("model") or "gpt-4.1-mini").strip()
        if not base_url or not api_key:
            raise RuntimeError("base_url and api_key are required")
        settings = upsert_ai_settings(
            tenant_id=scope["tenant_id"],
            workspace_id=scope["workspace_id"],
            user_id=actor_user_id,
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
        )
        create_audit_event(
            event_type="ai.settings_updated",
            target_type="ai_settings",
            target_id=settings.id,
            details={"provider": provider, "base_url": base_url, "model": model},
        )
        masked = settings.api_key[:6] + "..." + settings.api_key[-4:] if settings.api_key else ""
        return {
            "provider": settings.provider,
            "base_url": settings.base_url,
            "model": settings.model,
            "api_key_masked": masked,
            "updated_at": settings.updated_at.isoformat(),
        }

    def create_publish_plan(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(data, scope)
        tenant_id = scoped["tenant_id"]
        workspace_id = scoped["workspace_id"]
        platform = str(data["platform"]).strip()
        content_type = PublishContentType(str(data["content_type"]).strip())
        account_name = str(data["account_name"]).strip()
        payload = dict(data.get("payload") or {})
        draft_id = data.get("draft_id")
        asset_ids = list(data.get("asset_ids") or [])
        schedule_at = _parse_schedule(data.get("schedule_at"))
        created_by = data.get("__actor_user_id")
        require_approval = bool(data.get("require_approval", False))
        status = PublishPlanStatus.DRAFT if require_approval else PublishPlanStatus.ACTIVE

        if draft_id:
            draft = get_draft(str(draft_id))
            if not draft:
                raise RuntimeError(f"Draft not found: {draft_id}")
            if draft.tenant_id != tenant_id or draft.workspace_id != workspace_id:
                raise RuntimeError(f"Draft is outside current workspace: {draft_id}")
            payload = {
                "title": draft.title,
                "description": draft.description,
                "tags": draft.tags,
                **payload,
            }
            if not asset_ids:
                asset_ids = draft.asset_ids

        assets = get_assets_by_ids(asset_ids)
        if asset_ids and len(assets) != len(asset_ids):
            raise RuntimeError("Some assets do not exist")
        for asset in assets:
            if asset.tenant_id != tenant_id or asset.workspace_id != workspace_id:
                raise RuntimeError(f"Asset is outside current workspace: {asset.id}")

        if content_type == PublishContentType.VIDEO and assets and not payload.get("video_file"):
            first_video = next((asset for asset in assets if asset.asset_type == AssetType.VIDEO), None)
            if first_video:
                payload["video_file"] = first_video.path
        if content_type == PublishContentType.NOTE and assets and not payload.get("image_files"):
            payload["image_files"] = [asset.path for asset in assets if asset.asset_type == AssetType.IMAGE]

        plan = create_publish_plan(
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
            created_by=str(created_by) if created_by else None,
        )
        task = None
        if plan.status == PublishPlanStatus.ACTIVE:
            task = create_task(
                publish_plan_id=plan.id,
                scheduled_at=schedule_at,
                status=TaskStatus.QUEUED,
            )
        create_audit_event(
            event_type="publish_plan.created",
            target_type="publish_plan",
            target_id=plan.id,
            details={
                "task_id": task.id if task else None,
                "platform": platform,
                "content_type": content_type.value,
                "account_name": account_name,
                "draft_id": draft_id,
                "asset_ids": asset_ids,
                "status": plan.status.value,
            },
        )
        return {
            "publish_plan": asdict(plan),
            "task": asdict(task) if task else None,
        }

    def submit_publish_plan(
        self, plan_id: str, actor_user_id: str = "", comment: str = "", scope: dict[str, str] | None = None
    ) -> dict[str, Any]:
        scoped = self._scope(scope=scope)
        plan = get_publish_plan(plan_id)
        if not plan:
            raise RuntimeError(f"Publish plan not found: {plan_id}")
        if plan.tenant_id != scoped["tenant_id"] or plan.workspace_id != scoped["workspace_id"]:
            raise RuntimeError("Publish plan is outside current workspace")
        if plan.status != PublishPlanStatus.DRAFT:
            raise RuntimeError("Only draft plan can be submitted")
        plan = update_publish_plan_status(plan_id, PublishPlanStatus.PENDING_APPROVAL)
        add_approval_record(
            tenant_id=scoped["tenant_id"],
            workspace_id=scoped["workspace_id"],
            plan_id=plan_id,
            action=ApprovalAction.SUBMITTED,
            actor_user_id=actor_user_id or (plan.created_by or "unknown"),
            comment=comment,
        )
        create_audit_event(
            event_type="publish_plan.submitted",
            target_type="publish_plan",
            target_id=plan_id,
            details={"status": plan.status.value},
        )
        return asdict(plan)

    def approve_publish_plan(
        self, plan_id: str, comment: str = "", actor_user_id: str = "", scope: dict[str, str] | None = None
    ) -> dict[str, Any]:
        scoped = self._scope(scope=scope)
        plan = get_publish_plan(plan_id)
        if not plan:
            raise RuntimeError(f"Publish plan not found: {plan_id}")
        if plan.tenant_id != scoped["tenant_id"] or plan.workspace_id != scoped["workspace_id"]:
            raise RuntimeError("Publish plan is outside current workspace")
        if plan.status not in {PublishPlanStatus.PENDING_APPROVAL, PublishPlanStatus.DRAFT}:
            raise RuntimeError("Plan is not pending approval")
        plan = update_publish_plan_status(plan_id, PublishPlanStatus.ACTIVE)
        task = get_task_by_publish_plan_id(plan_id)
        if not task:
            task = create_task(
                publish_plan_id=plan.id,
                scheduled_at=plan.schedule_at,
                status=TaskStatus.QUEUED,
            )
        create_audit_event(
            event_type="publish_plan.approved",
            target_type="publish_plan",
            target_id=plan_id,
            details={"task_id": task.id, "status": plan.status.value},
        )
        add_approval_record(
            tenant_id=scoped["tenant_id"],
            workspace_id=scoped["workspace_id"],
            plan_id=plan_id,
            action=ApprovalAction.APPROVED,
            actor_user_id=actor_user_id or (plan.created_by or "unknown"),
            comment=comment,
        )
        return {"publish_plan": asdict(plan), "task": asdict(task)}

    def reject_publish_plan(
        self, plan_id: str, reason: str = "", actor_user_id: str = "", scope: dict[str, str] | None = None
    ) -> dict[str, Any]:
        scoped = self._scope(scope=scope)
        plan = get_publish_plan(plan_id)
        if not plan:
            raise RuntimeError(f"Publish plan not found: {plan_id}")
        if plan.tenant_id != scoped["tenant_id"] or plan.workspace_id != scoped["workspace_id"]:
            raise RuntimeError("Publish plan is outside current workspace")
        if plan.status != PublishPlanStatus.PENDING_APPROVAL:
            raise RuntimeError("Only pending plan can be rejected")
        plan = update_publish_plan_status(plan_id, PublishPlanStatus.REJECTED)
        create_audit_event(
            event_type="publish_plan.rejected",
            target_type="publish_plan",
            target_id=plan_id,
            details={"reason": reason, "status": plan.status.value},
        )
        add_approval_record(
            tenant_id=scoped["tenant_id"],
            workspace_id=scoped["workspace_id"],
            plan_id=plan_id,
            action=ApprovalAction.REJECTED,
            actor_user_id=actor_user_id or (plan.created_by or "unknown"),
            comment=reason,
        )
        return asdict(plan)

    def list_pending_publish_plans(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        items = [
            asdict(plan)
            for plan in list_publish_plans()
            if plan.tenant_id == scoped["tenant_id"]
            and plan.workspace_id == scoped["workspace_id"]
            and plan.status == PublishPlanStatus.PENDING_APPROVAL
        ]
        return items

    def list_pending_publish_plans_for_me(
        self, actor_user_id: str, actor_role: str, scope: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """
        “待我审批”只对 admin/owner 有意义；否则返回空列表。
        """
        if actor_role not in {UserRole.ADMIN.value, UserRole.OWNER.value}:
            return []
        return self.list_pending_publish_plans(scope=scope)

    def list_my_publish_plans(
        self, actor_user_id: str, status: str | None = None, scope: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        items = [
            asdict(plan)
            for plan in list_publish_plans()
            if plan.tenant_id == scoped["tenant_id"]
            and plan.workspace_id == scoped["workspace_id"]
            and plan.created_by == actor_user_id
        ]
        if status:
            items = [item for item in items if item.get("status") == status]
        return items

    def list_approval_records(self, plan_id: str | None = None, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        records = list_approval_records(scoped["tenant_id"], scoped["workspace_id"], plan_id=plan_id)
        return [asdict(item) for item in records]

    def register_account(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(data, scope)
        tenant_id = scoped["tenant_id"]
        workspace_id = scoped["workspace_id"]
        platform = str(data["platform"]).strip()
        account_name = str(data["account_name"]).strip()
        account_file = str(resolve_account_file(platform, account_name))
        account = create_account(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            platform=platform,
            account_name=account_name,
            account_file=account_file,
        )
        create_audit_event(
            event_type="account.registered",
            target_type="account",
            target_id=account.id,
            details={"platform": platform, "account_name": account_name},
        )
        return asdict(account)

    def list_accounts(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        return [
            asdict(account)
            for account in list_accounts()
            if account.tenant_id == scoped["tenant_id"] and account.workspace_id == scoped["workspace_id"]
        ]

    def create_user(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(data, scope)
        user = create_user(
            tenant_id=scoped["tenant_id"],
            email=str(data["email"]).strip(),
            display_name=str(data.get("display_name") or data["email"]).strip(),
        )
        create_audit_event(
            event_type="user.created",
            target_type="user",
            target_id=user.id,
            details={"email": user.email},
        )
        return asdict(user)

    def list_users(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        return [asdict(user) for user in list_users(scoped["tenant_id"])]

    def add_workspace_member(self, data: dict[str, Any], scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(data, scope)
        member = add_workspace_member(
            tenant_id=scoped["tenant_id"],
            workspace_id=scoped["workspace_id"],
            user_id=str(data["user_id"]).strip(),
            role=UserRole(str(data.get("role") or UserRole.EDITOR.value)),
        )
        create_audit_event(
            event_type="workspace_member.added",
            target_type="workspace_member",
            target_id=member.id,
            details={"user_id": member.user_id, "role": member.role.value},
        )
        return asdict(member)

    def list_workspace_members(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        return [
            asdict(member)
            for member in list_workspace_members(scoped["tenant_id"], scoped["workspace_id"])
        ]

    def check_account(self, account_id: str, scope: dict[str, str] | None = None) -> dict[str, Any]:
        scoped = self._scope(scope=scope)
        account = get_account(account_id)
        if not account:
            raise RuntimeError(f"Account not found: {account_id}")
        if account.tenant_id != scoped["tenant_id"] or account.workspace_id != scoped["workspace_id"]:
            raise RuntimeError(f"Account is outside current workspace: {account_id}")

        is_valid = asyncio.run(upload_service.check(account.platform, account.account_name))
        status = AccountStatus.ACTIVE if is_valid else AccountStatus.INVALID
        account = update_account_status(account_id, status)
        create_audit_event(
            event_type="account.checked",
            target_type="account",
            target_id=account.id,
            details={"platform": account.platform, "status": account.status.value},
        )
        return {
            "account": asdict(account),
            "is_valid": is_valid,
        }

    def list_publish_plans(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        scoped = self._scope(scope=scope)
        return [
            asdict(plan)
            for plan in list_publish_plans()
            if plan.tenant_id == scoped["tenant_id"] and plan.workspace_id == scoped["workspace_id"]
        ]

    def list_tasks(self, scope: dict[str, str] | None = None) -> list[dict[str, Any]]:
        self._cleanup_stale_running_tasks()
        scoped = self._scope(scope=scope)
        result: list[dict[str, Any]] = []
        for task in list_tasks():
            plan = get_publish_plan(task.publish_plan_id)
            if not plan:
                continue
            if plan.tenant_id == scoped["tenant_id"] and plan.workspace_id == scoped["workspace_id"]:
                result.append(asdict(task))
        return result

    def get_task(self, task_id: str, scope: dict[str, str] | None = None) -> dict[str, Any] | None:
        self._cleanup_stale_running_tasks()
        scoped = self._scope(scope=scope)
        task = get_task(task_id)
        if not task:
            return None
        plan = get_publish_plan(task.publish_plan_id)
        if not plan or plan.tenant_id != scoped["tenant_id"] or plan.workspace_id != scoped["workspace_id"]:
            return None
        return {
            "task": asdict(task),
            "publish_plan": asdict(plan) if plan else None,
            "runs": [asdict(run) for run in list_task_runs(task_id)],
        }

    def run_task(
        self,
        task_id: str,
        scope: dict[str, str] | None = None,
        *,
        bypass_protection: bool = False,
    ) -> dict[str, Any]:
        self._cleanup_stale_running_tasks()
        scoped = self._scope(scope=scope)
        task = get_task(task_id)
        if not task:
            raise RuntimeError(f"Task not found: {task_id}")

        plan = get_publish_plan(task.publish_plan_id)
        if not plan:
            raise RuntimeError(f"Publish plan not found: {task.publish_plan_id}")
        if plan.tenant_id != scoped["tenant_id"] or plan.workspace_id != scoped["workspace_id"]:
            raise RuntimeError(f"Task is outside current workspace: {task_id}")

        account_scope_key = f"{plan.platform}:{plan.account_name}"
        base_policy = {
            "cooldown_seconds": DEFAULT_COOLDOWN_SECONDS,
            "account_failure_threshold": ACCOUNT_FAILURE_THRESHOLD,
            "platform_failure_threshold": PLATFORM_FAILURE_THRESHOLD,
            "failure_window_seconds": FAILURE_WINDOW_SECONDS,
            "account_open_seconds": ACCOUNT_CIRCUIT_OPEN_SECONDS,
            "platform_open_seconds": PLATFORM_CIRCUIT_OPEN_SECONDS,
            "daily_limit": DEFAULT_DAILY_LIMIT,
        }
        platform_policy = get_risk_policy(scoped["tenant_id"], scoped["workspace_id"], "platform", plan.platform)
        account_policy = get_risk_policy(scoped["tenant_id"], scoped["workspace_id"], "account", account_scope_key)
        effective_policy = merge_policy(base_policy, platform_policy["policy"] if platform_policy else None)
        effective_policy = merge_policy(effective_policy, account_policy["policy"] if account_policy else None)

        day = datetime.now(UTC).date().isoformat()
        daily_count = get_daily_counter(scoped["tenant_id"], scoped["workspace_id"], "account", account_scope_key, day)
        daily_limit = int(effective_policy.get("daily_limit") or 0)
        if not bypass_protection and daily_limit and daily_count >= daily_limit:
            task = update_task_status(
                task_id,
                TaskStatus.QUEUED,
                last_error=f"daily limit reached: {daily_count}/{daily_limit}",
                last_error_type=TaskErrorType.DAILY_LIMIT,
            )
            create_audit_event(
                event_type="task.daily_limit",
                target_type="task",
                target_id=task_id,
                details={"count": daily_count, "limit": daily_limit},
            )
            return self.get_task(task.id, scope=scoped) or {"task": asdict(task)}
        account_open, account_open_until, account_failure_count = get_open_failure_circuit(
            "account", account_scope_key
        )
        platform_open, platform_open_until, platform_failure_count = get_open_failure_circuit(
            "platform", plan.platform
        )
        if not bypass_protection and (account_open or platform_open):
            open_until = account_open_until or platform_open_until
            update_task_schedule(task_id, open_until)
            task = update_task_status(
                task_id,
                TaskStatus.QUEUED,
                last_error=f"circuit open until {open_until.isoformat() if open_until else ''}",
                last_error_type=TaskErrorType.CIRCUIT_OPEN,
            )
            create_audit_event(
                event_type="task.circuit_open",
                target_type="task",
                target_id=task_id,
                details={
                    "publish_plan_id": plan.id,
                    "account_failure_count": account_failure_count,
                    "platform_failure_count": platform_failure_count,
                    "open_until": open_until.isoformat() if open_until else None,
                },
            )
            return self.get_task(task.id, scope=scoped) or {"task": asdict(task)}

        allowed, next_allowed_at = enforce_account_cooldown(
            platform=plan.platform,
            account_name=plan.account_name,
            cooldown_seconds=int(effective_policy.get("cooldown_seconds") or DEFAULT_COOLDOWN_SECONDS),
        )
        if not bypass_protection and not allowed:
            update_task_schedule(task_id, next_allowed_at)
            task = update_task_status(
                task_id,
                TaskStatus.QUEUED,
                last_error=f"cooldown: next allowed at {next_allowed_at.isoformat()}",
                last_error_type=TaskErrorType.COOLDOWN,
            )
            create_audit_event(
                event_type="task.cooldown",
                target_type="task",
                target_id=task_id,
                details={
                    "publish_plan_id": plan.id,
                    "next_allowed_at": next_allowed_at.isoformat(),
                },
            )
            return self.get_task(task.id, scope=scoped) or {"task": asdict(task)}

        update_task_status(task_id, TaskStatus.RUNNING)
        increment_daily_counter(scoped["tenant_id"], scoped["workspace_id"], "account", account_scope_key, day, delta=1)
        task_run = create_task_run(task_id)
        create_audit_event(
            event_type="task.started",
            target_type="task",
            target_id=task_id,
            details={"publish_plan_id": plan.id},
        )

        try:
            self._execute_plan(plan.platform, plan.content_type, plan.account_name, plan.payload)
            reset_failure_circuit("account", account_scope_key)
            reset_failure_circuit("platform", plan.platform)
            task = update_task_status(task_id, TaskStatus.SUCCEEDED)
            finish_task_run(task_run.id, TaskRunStatus.SUCCEEDED)
            create_audit_event(
                event_type="task.succeeded",
                target_type="task",
                target_id=task_id,
                details={"publish_plan_id": plan.id},
            )
        except Exception as exc:
            error_type = classify_error(exc)
            check_and_track_failure_circuit(
                "account",
                account_scope_key,
                error_type,
                threshold=int(effective_policy.get("account_failure_threshold") or ACCOUNT_FAILURE_THRESHOLD),
                window_seconds=int(effective_policy.get("failure_window_seconds") or FAILURE_WINDOW_SECONDS),
                open_seconds=int(effective_policy.get("account_open_seconds") or ACCOUNT_CIRCUIT_OPEN_SECONDS),
            )
            check_and_track_failure_circuit(
                "platform",
                plan.platform,
                error_type,
                threshold=int(effective_policy.get("platform_failure_threshold") or PLATFORM_FAILURE_THRESHOLD),
                window_seconds=int(effective_policy.get("failure_window_seconds") or FAILURE_WINDOW_SECONDS),
                open_seconds=int(effective_policy.get("platform_open_seconds") or PLATFORM_CIRCUIT_OPEN_SECONDS),
            )
            task = update_task_status(
                task_id,
                TaskStatus.FAILED,
                last_error=str(exc),
                last_error_type=error_type,
            )
            finish_task_run(
                task_run.id,
                TaskRunStatus.FAILED,
                error_message=str(exc),
                error_type=error_type,
            )
            create_audit_event(
                event_type="task.failed",
                target_type="task",
                target_id=task_id,
                details={"publish_plan_id": plan.id, "error": str(exc), "error_type": error_type.value},
            )
            raise

        return self.get_task(task.id, scope=scoped) or {"task": asdict(task)}

    def run_due_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        self._cleanup_stale_running_tasks()
        results: list[dict[str, Any]] = []
        for task in list_due_tasks()[:limit]:
            try:
                results.append(self.run_task(task.id))
            except Exception as exc:
                results.append(
                    {
                        "task": asdict(get_task(task.id)),
                        "publish_plan": None,
                        "runs": [],
                        "error": str(exc),
                    }
                )
        return results

    def _execute_plan(
        self,
        platform: str,
        content_type: PublishContentType,
        account_name: str,
        payload: dict[str, Any],
    ) -> None:
        if content_type == PublishContentType.VIDEO:
            request = self._build_video_request(platform, account_name, payload)
            asyncio.run(upload_service.upload_video(platform, request))
            return

        if content_type == PublishContentType.NOTE:
            request = self._build_note_request(platform, account_name, payload)
            asyncio.run(upload_service.upload_note(platform, request))
            return

        raise RuntimeError(f"Unsupported content type: {content_type}")

    def _build_video_request(self, platform: str, account_name: str, payload: dict[str, Any]):
        common = {
            "account_name": account_name,
            "video_file": Path(payload["video_file"]),
            "title": payload["title"],
            "description": payload.get("description", ""),
            "tags": list(payload.get("tags") or []),
            "publish_date": _parse_schedule(payload.get("publish_date")) or 0,
        }

        if platform == "douyin":
            return DouyinVideoUploadRequest(
                **common,
                thumbnail_file=Path(payload["thumbnail_file"]) if payload.get("thumbnail_file") else None,
                thumbnail_landscape_file=(
                    Path(payload["thumbnail_landscape_file"])
                    if payload.get("thumbnail_landscape_file")
                    else None
                ),
                thumbnail_portrait_file=(
                    Path(payload["thumbnail_portrait_file"])
                    if payload.get("thumbnail_portrait_file")
                    else None
                ),
                product_link=payload.get("product_link", ""),
                product_title=payload.get("product_title", ""),
                publish_strategy=payload.get("publish_strategy", "immediate"),
                debug=bool(payload.get("debug", False)),
                headless=bool(payload.get("headless", True)),
            )

        if platform == "kuaishou":
            return KuaishouVideoUploadRequest(
                **common,
                thumbnail_file=Path(payload["thumbnail_file"]) if payload.get("thumbnail_file") else None,
                publish_strategy=payload.get("publish_strategy", "immediate"),
                debug=bool(payload.get("debug", False)),
                headless=bool(payload.get("headless", True)),
            )

        if platform == "xiaohongshu":
            return XiaohongshuVideoUploadRequest(
                **common,
                thumbnail_file=Path(payload["thumbnail_file"]) if payload.get("thumbnail_file") else None,
                publish_strategy=payload.get("publish_strategy", "immediate"),
                debug=bool(payload.get("debug", False)),
                headless=bool(payload.get("headless", True)),
            )

        if platform == "bilibili":
            return BilibiliVideoUploadRequest(
                **common,
                tid=int(payload["tid"]),
            )

        if platform == "tencent":
            return TencentVideoUploadRequest(
                **common,
                thumbnail_file=Path(payload["thumbnail_file"]) if payload.get("thumbnail_file") else None,
                thumbnail_landscape_file=(
                    Path(payload["thumbnail_landscape_file"])
                    if payload.get("thumbnail_landscape_file")
                    else None
                ),
                thumbnail_portrait_file=(
                    Path(payload["thumbnail_portrait_file"])
                    if payload.get("thumbnail_portrait_file")
                    else None
                ),
                short_title=payload.get("short_title"),
                category=payload.get("category"),
                is_draft=bool(payload.get("is_draft", False)),
                publish_strategy=payload.get("publish_strategy", "immediate"),
                debug=bool(payload.get("debug", False)),
                headless=bool(payload.get("headless", True)),
            )

        if platform == "youtube":
            youtube_common = dict(common)
            youtube_common.pop("publish_date", None)
            return YouTubeVideoUploadRequest(
                **youtube_common,
                thumbnail_file=Path(payload["thumbnail_file"]) if payload.get("thumbnail_file") else None,
                playlist=payload.get("playlist"),
                visibility=payload.get("visibility", "public"),
                debug=bool(payload.get("debug", False)),
                headless=bool(payload.get("headless", False)),
            )

        raise RuntimeError(f"Unsupported video platform: {platform}")

    def _build_note_request(self, platform: str, account_name: str, payload: dict[str, Any]):
        common = {
            "account_name": account_name,
            "image_files": _materialize_path_list(payload.get("image_files")),
            "title": payload["title"],
            "note": payload.get("note", ""),
            "tags": list(payload.get("tags") or []),
            "publish_date": _parse_schedule(payload.get("publish_date")) or 0,
            "publish_strategy": payload.get("publish_strategy", "immediate"),
            "debug": bool(payload.get("debug", False)),
            "headless": bool(payload.get("headless", True)),
        }

        if platform == "douyin":
            return DouyinNoteUploadRequest(
                **common,
                bgm=payload.get("bgm", ""),
            )

        if platform == "kuaishou":
            return KuaishouNoteUploadRequest(**common)

        if platform == "xiaohongshu":
            return XiaohongshuNoteUploadRequest(**common)

        raise RuntimeError(f"Unsupported note platform: {platform}")


platform_service = PlatformApplicationService()
