import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sau_platform.app import create_app
from sau_platform.storage import DB_PATH, ensure_default_api_key, initialize_database


class SauPlatformAppTests(unittest.TestCase):
    def setUp(self):
        Path(DB_PATH).unlink(missing_ok=True)
        initialize_database()
        self.app = create_app()
        self.client = self.app.test_client()
        # 默认 API Key，写接口需要带上。
        bootstrap = self.client.get("/api/v1/bootstrap").get_json()["data"]
        scope_key = ensure_default_api_key(bootstrap["tenant_id"], bootstrap["workspace_id"]).key
        self.auth_headers = {"X-SAU-API-Key": scope_key}

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertIn("tenant_id", payload["scope"])
        self.assertIn("workspace_id", payload["scope"])

    def test_write_requires_api_key(self):
        response = self.client.post(
            "/api/v1/publish-plans",
            json={
                "platform": "douyin",
                "content_type": "video",
                "account_name": "creator",
                "payload": {"video_file": "demo.mp4", "title": "测试"},
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_auth_register_login_and_bearer_access(self):
        register_resp = self.client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "password123", "display_name": "LoginUser"},
        )
        self.assertEqual(register_resp.status_code, 200)

        login_resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "password123"},
        )
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.get_json()["data"]["token"]

        me_resp = self.client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.get_json()["data"]["email"], "login@example.com")

        asset_resp = self.client.post(
            "/api/v1/assets",
            json={"asset_type": "video", "path": "bearer.mp4"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(asset_resp.status_code, 200)

    def test_workspace_switch_and_approval_records(self):
        self.client.post(
            "/api/v1/auth/register",
            json={"email": "member@example.com", "password": "password123", "display_name": "Member"},
        )
        login_resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": "member@example.com", "password": "password123"},
        )
        token = login_resp.get_json()["data"]["token"]
        user_id = login_resp.get_json()["data"]["user"]["id"]

        ws_resp = self.client.post(
            "/api/v1/workspaces",
            json={"name": "team-2"},
            headers=self.auth_headers,
        )
        self.assertEqual(ws_resp.status_code, 200)
        workspace = ws_resp.get_json()["data"]

        # 把登录用户加入新工作区
        member_resp = self.client.post(
            "/api/v1/workspace-members",
            json={"workspace_id": workspace["id"], "user_id": user_id, "role": "editor"},
            headers=self.auth_headers,
        )
        self.assertEqual(member_resp.status_code, 200)

        # 切换工作区会返回新 token
        switch_resp = self.client.post(
            "/api/v1/auth/switch-workspace",
            json={"workspace_id": workspace["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(switch_resp.status_code, 200)
        new_token = switch_resp.get_json()["data"]["token"]

        me_resp = self.client.get("/api/v1/me", headers={"Authorization": f"Bearer {new_token}"})
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.get_json()["data"]["workspace_id"], workspace["id"])

        # 创建需要审批的发布计划（draft）
        plan_resp = self.client.post(
            "/api/v1/publish-plans",
            json={
                "platform": "douyin",
                "content_type": "video",
                "account_name": "creator",
                "require_approval": True,
                "payload": {"video_file": "demo.mp4", "title": "审批标题"},
            },
            headers={"Authorization": f"Bearer {new_token}"},
        )
        self.assertEqual(plan_resp.status_code, 200)
        plan = plan_resp.get_json()["data"]["publish_plan"]
        self.assertEqual(plan["status"], "draft")
        self.assertIsNone(plan_resp.get_json()["data"]["task"])

        submit_resp = self.client.post(
            f"/api/v1/publish-plans/{plan['id']}/submit",
            json={},
            headers={"Authorization": f"Bearer {new_token}"},
        )
        self.assertEqual(submit_resp.status_code, 200)

        # 为新工作区创建一个 admin key 来审批
        ws_key_resp = self.client.post(
            "/api/v1/api-keys",
            json={"name": "team2-admin", "workspace_id": workspace["id"]},
            headers=self.auth_headers,
        )
        ws_key = ws_key_resp.get_json()["data"]["key"]
        ws_admin_headers = {"X-SAU-API-Key": ws_key}

        approve_resp = self.client.post(
            f"/api/v1/publish-plans/{plan['id']}/approve",
            json={"comment": "ok"},
            headers=ws_admin_headers,
        )
        self.assertEqual(approve_resp.status_code, 200)
        self.assertIsNotNone(approve_resp.get_json()["data"]["task"])

        approvals_resp = self.client.get(
            f"/api/v1/approvals?plan_id={plan['id']}",
            headers=ws_admin_headers,
        )
        self.assertEqual(approvals_resp.status_code, 200)
        approvals = approvals_resp.get_json()["data"]
        self.assertGreaterEqual(len(approvals), 2)
        actions = {item["action"] for item in approvals}
        self.assertIn("submitted", actions)
        self.assertIn("approved", actions)

        pending_for_me = self.client.get(
            "/api/v1/publish-plans/pending-for-me",
            headers=ws_admin_headers,
        ).get_json()["data"]
        # 已经批准，应该不在待审批里
        self.assertEqual(len(pending_for_me), 0)

        mine = self.client.get(
            "/api/v1/publish-plans/mine",
            headers={"Authorization": f"Bearer {new_token}"},
        ).get_json()["data"]
        self.assertGreaterEqual(len(mine), 1)

    def test_create_publish_plan_and_list_task(self):
        response = self.client.post(
            "/api/v1/publish-plans",
            json={
                "platform": "douyin",
                "content_type": "video",
                "account_name": "creator",
                "payload": {
                    "video_file": "demo.mp4",
                    "title": "测试标题",
                    "description": "测试描述",
                    "tags": ["测试"],
                },
            },
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()["data"]
        self.assertEqual(payload["publish_plan"]["platform"], "douyin")
        self.assertEqual(payload["task"]["status"], "queued")

        tasks_response = self.client.get("/api/v1/tasks", headers=self.auth_headers)
        self.assertEqual(tasks_response.status_code, 200)
        tasks_payload = tasks_response.get_json()["data"]
        self.assertEqual(len(tasks_payload), 1)
        self.assertEqual(tasks_payload[0]["publish_plan_id"], payload["publish_plan"]["id"])

    def test_register_and_check_account(self):
        response = self.client.post(
            "/api/v1/accounts",
            json={
                "platform": "douyin",
                "account_name": "creator",
            },
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        account = response.get_json()["data"]
        self.assertEqual(account["platform"], "douyin")
        self.assertEqual(account["status"], "unknown")

        with patch(
            "sau_platform.service.upload_service.check",
            new=AsyncMock(return_value=True),
        ) as mock_check:
            check_response = self.client.post(
                f"/api/v1/accounts/{account['id']}/check", headers=self.auth_headers
            )

        self.assertEqual(check_response.status_code, 200)
        check_payload = check_response.get_json()["data"]
        self.assertTrue(check_payload["is_valid"])
        self.assertEqual(check_payload["account"]["status"], "active")
        mock_check.assert_called_once_with("douyin", "creator")

    def test_create_user_and_workspace_member(self):
        user_resp = self.client.post(
            "/api/v1/users",
            json={"email": "editor@example.com", "display_name": "Editor"},
            headers=self.auth_headers,
        )
        self.assertEqual(user_resp.status_code, 200)
        user = user_resp.get_json()["data"]
        self.assertEqual(user["email"], "editor@example.com")

        member_resp = self.client.post(
            "/api/v1/workspace-members",
            json={"user_id": user["id"], "role": "editor"},
            headers=self.auth_headers,
        )
        self.assertEqual(member_resp.status_code, 200)
        member = member_resp.get_json()["data"]
        self.assertEqual(member["role"], "editor")

        users = self.client.get("/api/v1/users", headers=self.auth_headers).get_json()["data"]
        members = self.client.get("/api/v1/workspace-members", headers=self.auth_headers).get_json()["data"]
        self.assertGreaterEqual(len(users), 2)
        self.assertGreaterEqual(len(members), 2)

    def test_rbac_forbids_viewer_write(self):
        user_resp = self.client.post(
            "/api/v1/users",
            json={"email": "viewer@example.com", "display_name": "Viewer"},
            headers=self.auth_headers,
        )
        user = user_resp.get_json()["data"]
        self.client.post(
            "/api/v1/workspace-members",
            json={"user_id": user["id"], "role": "viewer"},
            headers=self.auth_headers,
        )
        viewer_headers = {
            **self.auth_headers,
            "X-SAU-User-Id": user["id"],
        }
        response = self.client.post(
            "/api/v1/assets",
            json={"asset_type": "video", "path": "viewer.mp4"},
            headers=viewer_headers,
        )
        self.assertEqual(response.status_code, 403)

    def test_api_key_lifecycle(self):
        create_resp = self.client.post(
            "/api/v1/api-keys",
            json={"name": "ci-key"},
            headers=self.auth_headers,
        )
        self.assertEqual(create_resp.status_code, 200)
        api_key = create_resp.get_json()["data"]
        self.assertEqual(api_key["name"], "ci-key")
        self.assertIn("key", api_key)

        list_resp = self.client.get("/api/v1/api-keys", headers=self.auth_headers)
        self.assertEqual(list_resp.status_code, 200)
        self.assertGreaterEqual(len(list_resp.get_json()["data"]), 2)

        rotate_resp = self.client.post(
            f"/api/v1/api-keys/{api_key['id']}/rotate",
            json={},
            headers=self.auth_headers,
        )
        self.assertEqual(rotate_resp.status_code, 200)
        rotated = rotate_resp.get_json()["data"]
        self.assertNotEqual(rotated["id"], api_key["id"])

        revoke_resp = self.client.post(
            f"/api/v1/api-keys/{rotated['id']}/revoke",
            json={},
            headers=self.auth_headers,
        )
        self.assertEqual(revoke_resp.status_code, 200)
        self.assertEqual(revoke_resp.get_json()["data"]["status"], "revoked")

    def test_create_asset_and_draft(self):
        asset_resp = self.client.post(
            "/api/v1/assets",
            json={"asset_type": "video", "path": "demo.mp4"},
            headers=self.auth_headers,
        )
        self.assertEqual(asset_resp.status_code, 200)
        asset = asset_resp.get_json()["data"]
        self.assertEqual(asset["asset_type"], "video")

        draft_resp = self.client.post(
            "/api/v1/drafts",
            json={
                "title": "草稿标题",
                "description": "草稿描述",
                "tags": ["测试"],
                "asset_ids": [asset["id"]],
            },
            headers=self.auth_headers,
        )
        self.assertEqual(draft_resp.status_code, 200)
        draft = draft_resp.get_json()["data"]
        self.assertEqual(draft["title"], "草稿标题")
        self.assertEqual(draft["asset_ids"], [asset["id"]])

        list_assets = self.client.get("/api/v1/assets", headers=self.auth_headers).get_json()["data"]
        list_drafts = self.client.get("/api/v1/drafts", headers=self.auth_headers).get_json()["data"]
        self.assertEqual(len(list_assets), 1)
        self.assertEqual(len(list_drafts), 1)

    def test_ai_rewrite_endpoint(self):
        # 用登录态调用（用户自配模型 key 的前提）
        self.client.post(
            "/api/v1/auth/register",
            json={"email": "ai@example.com", "password": "password123", "display_name": "AIUser"},
        )
        login_resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": "ai@example.com", "password": "password123"},
        )
        token = login_resp.get_json()["data"]["token"]

        with patch(
            "sau_ai.openai_compat.requests.post",
        ) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": '{"title":"新标题","description":"新描述","tags":["t1","t2"]}'
                        }
                    }
                ]
            }
            mock_post.return_value.raise_for_status.return_value = None

            # 保存用户级 AI 配置
            settings_resp = self.client.post(
                "/api/v1/ai/settings",
                json={
                    "provider": "openai_compat",
                    "base_url": "https://api.example.com",
                    "api_key": "sk-test-1234567890",
                    "model": "gpt-4.1-mini",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(settings_resp.status_code, 200)

            response = self.client.post(
                "/api/v1/ai/rewrite",
                json={
                    "platform": "douyin",
                    "title": "标题",
                    "description": "描述",
                    "tags": ["tag1"],
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()["data"]
        self.assertEqual(payload["provider"], "openai_compat")
        self.assertEqual(payload["title"], "新标题")
        self.assertEqual(payload["tags"], ["t1", "t2"])

    def test_create_publish_plan_from_draft_and_assets(self):
        asset_resp = self.client.post(
            "/api/v1/assets",
            json={"asset_type": "video", "path": "draft-video.mp4"},
            headers=self.auth_headers,
        )
        asset = asset_resp.get_json()["data"]
        draft_resp = self.client.post(
            "/api/v1/drafts",
            json={
                "title": "草稿计划标题",
                "description": "草稿计划描述",
                "tags": ["计划"],
                "asset_ids": [asset["id"]],
            },
            headers=self.auth_headers,
        )
        draft = draft_resp.get_json()["data"]

        response = self.client.post(
            "/api/v1/publish-plans",
            json={
                "platform": "douyin",
                "content_type": "video",
                "account_name": "creator",
                "draft_id": draft["id"],
                "asset_ids": [asset["id"]],
            },
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()["data"]
        self.assertEqual(payload["publish_plan"]["draft_id"], draft["id"])
        self.assertEqual(payload["publish_plan"]["asset_ids"], [asset["id"]])
        self.assertEqual(payload["publish_plan"]["payload"]["title"], "草稿计划标题")
        self.assertEqual(payload["publish_plan"]["payload"]["video_file"], "draft-video.mp4")

    def test_run_task_endpoint_updates_task_status(self):
        response = self.client.post(
            "/api/v1/publish-plans",
            json={
                "platform": "douyin",
                "content_type": "video",
                "account_name": "creator",
                "payload": {
                    "video_file": "demo.mp4",
                    "title": "测试标题",
                    "description": "测试描述",
                    "tags": ["测试"],
                },
            },
            headers=self.auth_headers,
        )
        task_id = response.get_json()["data"]["task"]["id"]

        with patch(
            "sau_platform.service.upload_service.upload_video",
            new=AsyncMock(return_value=None),
        ) as mock_upload_video:
            run_response = self.client.post(
                f"/api/v1/tasks/{task_id}/run", headers=self.auth_headers
            )

        self.assertEqual(run_response.status_code, 200)
        run_payload = run_response.get_json()["data"]
        self.assertEqual(run_payload["task"]["status"], "succeeded")
        self.assertEqual(len(run_payload["runs"]), 1)
        self.assertEqual(run_payload["runs"][0]["status"], "succeeded")
        mock_upload_video.assert_called_once()

    def test_run_due_tasks_endpoint_runs_queued_tasks(self):
        self.client.post(
            "/api/v1/publish-plans",
            json={
                "platform": "douyin",
                "content_type": "video",
                "account_name": "creator",
                "payload": {
                    "video_file": "demo.mp4",
                    "title": "测试标题",
                    "description": "测试描述",
                    "tags": ["测试"],
                },
            },
            headers=self.auth_headers,
        )

        with patch(
            "sau_platform.service.upload_service.upload_video",
            new=AsyncMock(return_value=None),
        ) as mock_upload_video:
            response = self.client.post(
                "/api/v1/tasks/run-due", json={"limit": 5}, headers=self.auth_headers
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()["data"]
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["task"]["status"], "succeeded")
        mock_upload_video.assert_called_once()

    def test_circuit_breaker_opens_after_repeated_failures(self):
        task_ids = []
        for index in range(4):
            response = self.client.post(
                "/api/v1/publish-plans",
                json={
                    "platform": "douyin",
                    "content_type": "video",
                    "account_name": "creator",
                    "payload": {
                        "video_file": f"demo-{index}.mp4",
                        "title": f"测试标题{index}",
                        "description": "测试描述",
                        "tags": ["测试"],
                    },
                },
                headers=self.auth_headers,
            )
            task_ids.append(response.get_json()["data"]["task"]["id"])

        with patch(
            "sau_platform.service.enforce_account_cooldown",
            return_value=(True, datetime.now(UTC)),
        ), patch(
            "sau_platform.service.upload_service.upload_video",
            new=AsyncMock(side_effect=RuntimeError("rate limit")),
        ):
            for task_id in task_ids[:3]:
                response = self.client.post(
                    f"/api/v1/tasks/{task_id}/run",
                    headers=self.auth_headers,
                )
                self.assertEqual(response.status_code, 500)

            circuit_response = self.client.post(
                f"/api/v1/tasks/{task_ids[3]}/run",
                headers=self.auth_headers,
            )

        self.assertEqual(circuit_response.status_code, 200)
        payload = circuit_response.get_json()["data"]
        self.assertEqual(payload["task"]["status"], "queued")
        self.assertEqual(payload["task"]["last_error_type"], "circuit_open")
