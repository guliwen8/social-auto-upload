from __future__ import annotations

from pathlib import Path

from flask import Flask, g, jsonify, request, send_file, send_from_directory

from .service import platform_service, role_allows
from .models import UserRole
from .storage import DB_PATH, initialize_database, validate_api_key


def create_app() -> Flask:
    initialize_database()
    app = Flask(__name__)
    bootstrap_info = platform_service.ensure_bootstrap()
    # 优先使用构建后的 Vue 控制台（更适合长期维护）；未构建时回退到旧的纯 HTML 控制台。
    legacy_console_root = Path(__file__).resolve().parent.parent / "sau_platform_console"
    vue_console_dist = Path(__file__).resolve().parent.parent / "sau_platform_console_vue" / "dist"
    console_root = vue_console_dist if (vue_console_dist / "index.html").exists() else legacy_console_root
    console_index = console_root / "index.html"

    def require_api_key() -> str | None:
        return request.headers.get("X-SAU-API-Key") or request.args.get("api_key")

    def require_user_id() -> str | None:
        return request.headers.get("X-SAU-User-Id") or request.args.get("user_id")

    def require_bearer_token() -> str | None:
        auth = (request.headers.get("Authorization") or "").strip()
        if not auth.lower().startswith("bearer "):
            return None
        return auth.split(" ", 1)[1].strip()

    def request_scope() -> dict[str, str]:
        if getattr(g, "session", None):
            return {
                "tenant_id": g.session["tenant_id"],
                "workspace_id": g.session["workspace_id"],
            }
        if getattr(g, "api_key", None):
            return {
                "tenant_id": g.api_key.tenant_id,
                "workspace_id": g.api_key.workspace_id,
            }
        return platform_service.get_default_scope()

    def required_role() -> UserRole | None:
        if not request.path.startswith("/api/v1/") or request.path in {"/api/v1/bootstrap"}:
            return None
        if request.path.startswith("/api/v1/auth/"):
            return None
        if request.path in {"/api/v1/me"}:
            return UserRole.VIEWER
        if request.path.startswith("/api/v1/workspaces"):
            return UserRole.ADMIN if request.method != "GET" else UserRole.VIEWER
        if request.path.startswith("/api/v1/approvals") or request.path.startswith("/api/v1/publish-plans/pending"):
            return UserRole.VIEWER
        if request.path.startswith("/api/v1/api-keys"):
            return UserRole.ADMIN
        if request.path.startswith("/api/v1/risk-policies"):
            return UserRole.ADMIN
        if request.path.startswith("/api/v1/users") or request.path.startswith("/api/v1/workspace-members"):
            return UserRole.ADMIN
        if request.path.startswith("/api/v1/accounts"):
            return UserRole.EDITOR if request.method != "GET" else UserRole.VIEWER
        if request.path.startswith("/api/v1/assets") or request.path.startswith("/api/v1/drafts"):
            return UserRole.EDITOR if request.method != "GET" else UserRole.VIEWER
        if request.path.startswith("/api/v1/publish-plans"):
            if request.path.endswith("/approve") or request.path.endswith("/reject"):
                return UserRole.ADMIN
            return UserRole.EDITOR if request.method != "GET" else UserRole.VIEWER
        if request.path.startswith("/api/v1/publish-plans/mine") or request.path.startswith(
            "/api/v1/publish-plans/pending-for-me"
        ):
            return UserRole.VIEWER
        if request.path.startswith("/api/v1/tasks"):
            return UserRole.EDITOR if request.method != "GET" else UserRole.VIEWER
        if request.path.startswith("/api/v1/ai/"):
            return UserRole.EDITOR
        return UserRole.VIEWER

    @app.before_request
    def enforce_auth():
        g.api_key = None
        g.actor = None
        g.session = None

        if request.path.startswith("/assets/") or request.path == "/":
            return None

        if request.path == "/health":
            return None

        if request.path.startswith("/api/v1/auth/") or request.path == "/api/v1/bootstrap":
            return None

        token = require_bearer_token()
        if token:
            session_actor = platform_service.auth_me(token)
            if not session_actor:
                return jsonify({"code": 401, "msg": "unauthorized", "data": None}), 401
            g.session = session_actor
            g.actor = {
                "tenant_id": session_actor["tenant_id"],
                "workspace_id": session_actor["workspace_id"],
                "user_id": session_actor["user_id"],
                "role": session_actor["role"],
                "email": session_actor["email"],
                "display_name": session_actor["display_name"],
            }
            needed = required_role()
            if needed and not role_allows(UserRole(g.actor["role"]), needed):
                return jsonify({"code": 403, "msg": "forbidden", "data": None}), 403
            return None

        key_value = require_api_key()
        if not key_value:
            return jsonify({"code": 401, "msg": "authorization required", "data": None}), 401
        g.api_key = validate_api_key(key_value or "")
        if not g.api_key:
            return jsonify({"code": 401, "msg": "unauthorized", "data": None}), 401
        g.actor = platform_service.resolve_actor(request_scope(), require_user_id())
        if g.actor:
            g.actor["tenant_id"] = g.api_key.tenant_id
            g.actor["workspace_id"] = g.api_key.workspace_id
        needed = required_role()
        if needed and not g.actor:
            return jsonify({"code": 403, "msg": "no workspace member context", "data": None}), 403
        if needed and not role_allows(UserRole(g.actor["role"]), needed):
            return jsonify({"code": 403, "msg": "forbidden", "data": None}), 403

    @app.get("/")
    def console():
        return send_file(console_index)

    @app.get("/assets/<path:filename>")
    def console_assets(filename: str):
        return send_from_directory(console_root / "assets", filename)

    @app.get("/health")
    def health():
        return jsonify(
            {
                "ok": True,
                "database_path": str(DB_PATH),
                "scope": platform_service.get_default_scope(),
            }
        )

    @app.get("/api/v1/bootstrap")
    def bootstrap():
        return jsonify({"code": 200, "data": bootstrap_info})

    @app.get("/api/v1/me")
    def me():
        return jsonify({"code": 200, "data": g.actor})

    @app.post("/api/v1/auth/register")
    def auth_register():
        payload = request.get_json(force=True, silent=False) or {}
        result = platform_service.auth_register(payload, scope=platform_service.get_default_scope())
        return jsonify({"code": 200, "data": result})

    @app.post("/api/v1/auth/login")
    def auth_login():
        payload = request.get_json(force=True, silent=False) or {}
        result = platform_service.auth_login(payload, scope=platform_service.get_default_scope())
        return jsonify({"code": 200, "data": result})

    @app.post("/api/v1/auth/logout")
    def auth_logout():
        token = require_bearer_token()
        if not token:
            return jsonify({"code": 401, "msg": "unauthorized", "data": None}), 401
        platform_service.auth_logout(token)
        return jsonify({"code": 200, "data": {"ok": True}})

    @app.post("/api/v1/auth/switch-workspace")
    def auth_switch_workspace():
        token = require_bearer_token()
        if not token:
            return jsonify({"code": 401, "msg": "unauthorized", "data": None}), 401
        payload = request.get_json(force=True, silent=False) or {}
        workspace_id = str(payload.get("workspace_id") or "").strip()
        if not workspace_id:
            return jsonify({"code": 400, "msg": "workspace_id required", "data": None}), 400
        try:
            result = platform_service.auth_switch_workspace(token, workspace_id)
            return jsonify({"code": 200, "data": result})
        except Exception as exc:
            return jsonify({"code": 500, "msg": str(exc), "data": None}), 500

    @app.get("/api/v1/workspaces")
    def list_workspaces():
        token = require_bearer_token()
        if token:
            return jsonify({"code": 200, "data": platform_service.auth_list_workspaces(token)})
        return jsonify({"code": 200, "data": platform_service.list_workspaces(scope=request_scope())})

    @app.post("/api/v1/workspaces")
    def create_workspace():
        payload = request.get_json(force=True, silent=False) or {}
        payload["__actor_user_id"] = g.actor["user_id"] if g.actor else None
        result = platform_service.create_workspace(payload, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.get("/api/v1/api-keys")
    def list_api_keys():
        return jsonify({"code": 200, "data": platform_service.list_api_keys(scope=request_scope())})

    @app.post("/api/v1/api-keys")
    def create_api_key():
        payload = request.get_json(force=True, silent=False) or {}
        result = platform_service.create_api_key(payload, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.post("/api/v1/api-keys/<api_key_id>/revoke")
    def revoke_api_key(api_key_id: str):
        result = platform_service.revoke_api_key(api_key_id, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.post("/api/v1/api-keys/<api_key_id>/rotate")
    def rotate_api_key(api_key_id: str):
        result = platform_service.rotate_api_key(api_key_id, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.get("/api/v1/risk-policies")
    def list_risk_policies():
        return jsonify({"code": 200, "data": platform_service.list_risk_policies(scope=request_scope())})

    @app.post("/api/v1/risk-policies")
    def upsert_risk_policy():
        payload = request.get_json(force=True, silent=False) or {}
        result = platform_service.upsert_risk_policy(payload, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.get("/api/v1/users")
    def list_users():
        return jsonify({"code": 200, "data": platform_service.list_users(scope=request_scope())})

    @app.post("/api/v1/users")
    def create_user():
        payload = request.get_json(force=True, silent=False) or {}
        result = platform_service.create_user(payload, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.get("/api/v1/workspace-members")
    def list_workspace_members():
        return jsonify({"code": 200, "data": platform_service.list_workspace_members(scope=request_scope())})

    @app.post("/api/v1/workspace-members")
    def add_workspace_member():
        payload = request.get_json(force=True, silent=False) or {}
        result = platform_service.add_workspace_member(payload, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.get("/api/v1/assets")
    def list_assets():
        return jsonify({"code": 200, "data": platform_service.list_assets(scope=request_scope())})

    @app.post("/api/v1/assets")
    def create_asset():
        payload = request.get_json(force=True, silent=False) or {}
        payload["__actor_user_id"] = g.actor["user_id"] if g.actor else None
        result = platform_service.create_asset(payload, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.get("/api/v1/drafts")
    def list_drafts():
        return jsonify({"code": 200, "data": platform_service.list_drafts(scope=request_scope())})

    @app.post("/api/v1/drafts")
    def create_draft():
        payload = request.get_json(force=True, silent=False) or {}
        payload["__actor_user_id"] = g.actor["user_id"] if g.actor else None
        result = platform_service.create_draft(payload, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.post("/api/v1/ai/rewrite")
    def ai_rewrite():
        payload = request.get_json(force=True, silent=False) or {}
        payload["__actor_user_id"] = g.actor["user_id"] if g.actor else None
        payload["__scope"] = request_scope()
        result = platform_service.ai_rewrite(payload)
        return jsonify({"code": 200, "data": result})

    @app.get("/api/v1/ai/settings")
    def get_ai_settings():
        actor_user_id = g.actor["user_id"] if g.actor else ""
        result = platform_service.get_ai_settings(request_scope(), actor_user_id)
        return jsonify({"code": 200, "data": result})

    @app.post("/api/v1/ai/settings")
    def upsert_ai_settings():
        payload = request.get_json(force=True, silent=False) or {}
        actor_user_id = g.actor["user_id"] if g.actor else ""
        try:
            result = platform_service.upsert_ai_settings(payload, request_scope(), actor_user_id)
            return jsonify({"code": 200, "data": result})
        except Exception as exc:
            return jsonify({"code": 500, "msg": str(exc), "data": None}), 500

    @app.get("/api/v1/accounts")
    def list_accounts():
        return jsonify({"code": 200, "data": platform_service.list_accounts(scope=request_scope())})

    @app.post("/api/v1/accounts")
    def register_account():
        payload = request.get_json(force=True, silent=False) or {}
        payload["__actor_user_id"] = g.actor["user_id"] if g.actor else None
        result = platform_service.register_account(payload, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.post("/api/v1/accounts/<account_id>/check")
    def check_account(account_id: str):
        try:
            result = platform_service.check_account(account_id, scope=request_scope())
            return jsonify({"code": 200, "data": result})
        except Exception as exc:
            return jsonify({"code": 500, "msg": str(exc), "data": None}), 500

    @app.get("/api/v1/publish-plans")
    def list_publish_plans():
        return jsonify({"code": 200, "data": platform_service.list_publish_plans(scope=request_scope())})

    @app.post("/api/v1/publish-plans")
    def create_publish_plan():
        payload = request.get_json(force=True, silent=False) or {}
        payload["__actor_user_id"] = g.actor["user_id"] if g.actor else None
        result = platform_service.create_publish_plan(payload, scope=request_scope())
        return jsonify({"code": 200, "data": result})

    @app.post("/api/v1/publish-plans/<plan_id>/submit")
    def submit_publish_plan(plan_id: str):
        try:
            result = platform_service.submit_publish_plan(
                plan_id,
                actor_user_id=g.actor["user_id"] if g.actor else "",
                comment="",
                scope=request_scope(),
            )
            return jsonify({"code": 200, "data": result})
        except Exception as exc:
            return jsonify({"code": 500, "msg": str(exc), "data": None}), 500

    @app.post("/api/v1/publish-plans/<plan_id>/approve")
    def approve_publish_plan(plan_id: str):
        payload = request.get_json(silent=True) or {}
        comment = str(payload.get("comment") or "")
        try:
            result = platform_service.approve_publish_plan(
                plan_id,
                comment=comment,
                actor_user_id=g.actor["user_id"] if g.actor else "",
                scope=request_scope(),
            )
            return jsonify({"code": 200, "data": result})
        except Exception as exc:
            return jsonify({"code": 500, "msg": str(exc), "data": None}), 500

    @app.post("/api/v1/publish-plans/<plan_id>/reject")
    def reject_publish_plan(plan_id: str):
        payload = request.get_json(silent=True) or {}
        reason = str(payload.get("reason") or "")
        try:
            result = platform_service.reject_publish_plan(
                plan_id,
                reason=reason,
                actor_user_id=g.actor["user_id"] if g.actor else "",
                scope=request_scope(),
            )
            return jsonify({"code": 200, "data": result})
        except Exception as exc:
            return jsonify({"code": 500, "msg": str(exc), "data": None}), 500

    @app.get("/api/v1/publish-plans/pending")
    def list_pending_publish_plans():
        return jsonify({"code": 200, "data": platform_service.list_pending_publish_plans(scope=request_scope())})

    @app.get("/api/v1/publish-plans/pending-for-me")
    def list_pending_publish_plans_for_me():
        actor_user_id = g.actor["user_id"] if g.actor else ""
        actor_role = g.actor["role"] if g.actor else ""
        return jsonify(
            {
                "code": 200,
                "data": platform_service.list_pending_publish_plans_for_me(
                    actor_user_id, actor_role, scope=request_scope()
                ),
            }
        )

    @app.get("/api/v1/publish-plans/mine")
    def list_my_publish_plans():
        actor_user_id = g.actor["user_id"] if g.actor else ""
        status = request.args.get("status")
        return jsonify(
            {
                "code": 200,
                "data": platform_service.list_my_publish_plans(
                    actor_user_id=actor_user_id, status=status, scope=request_scope()
                ),
            }
        )

    @app.get("/api/v1/approvals")
    def list_approvals():
        plan_id = request.args.get("plan_id")
        return jsonify(
            {"code": 200, "data": platform_service.list_approval_records(plan_id=plan_id, scope=request_scope())}
        )

    @app.get("/api/v1/tasks")
    def list_tasks():
        return jsonify({"code": 200, "data": platform_service.list_tasks(scope=request_scope())})

    @app.get("/api/v1/tasks/<task_id>")
    def get_task(task_id: str):
        result = platform_service.get_task(task_id, scope=request_scope())
        if not result:
            return jsonify({"code": 404, "msg": "task not found", "data": None}), 404
        return jsonify({"code": 200, "data": result})

    @app.post("/api/v1/tasks/<task_id>/run")
    def run_task(task_id: str):
        try:
            result = platform_service.run_task(task_id, scope=request_scope(), bypass_protection=True)
            return jsonify({"code": 200, "data": result})
        except Exception as exc:
            return jsonify({"code": 500, "msg": str(exc), "data": None}), 500

    @app.post("/api/v1/tasks/run-due")
    def run_due_tasks():
        payload = request.get_json(silent=True) or {}
        limit = int(payload.get("limit", 10))
        result = platform_service.run_due_tasks(limit=limit)
        return jsonify({"code": 200, "data": result})

    return app
