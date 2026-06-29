# 平台化 MVP 说明

## 当前定位

这个模块是新的最小控制面，用来承接未来的多人平台演进。

当前主线包括：

- `sau/`：统一运行时、请求模型、平台适配层、上传服务层
- `sau_cli.py`：CLI 契约入口
- `sau_platform/`：最小控制面
- `sau_platform_server.py`：平台后端启动入口
- `sau_platform_worker.py`：待执行任务 worker

旧的 `sau_backend.py`、`sau_frontend/`、`myUtils/` 仍然保留，但已经属于 `legacy`。

## 目前已经具备的能力

当前最小控制面已经支持：

- 用户
- 工作区成员
- 角色基础模型
- 真正的 RBAC 权限判断
- 多 API Key、吊销与轮换
- 登录态用户体系（注册/登录/退出，Bearer Token）
- 注册平台账号
- 账号健康检查
- 初始化默认 `tenant` / `workspace`
- 创建发布计划
- 为发布计划创建任务
- 查询任务状态
- 单个任务立即执行
- 批量拉起到期任务
- 记录基础审计事件
- 把任务真正委托给 `sau.services` 执行
- 任务失败类型分类（`error_type`）、账号冷却（默认 60 秒）与时间窗口熔断
- 风控策略配置（risk policies：cooldown/熔断阈值/每日限额）
- 前端控制台骨架（根路径 `/`）

这意味着主线已经形成了一个最小闭环：

`发布计划 -> 任务 -> worker/执行 -> 状态回写 -> 审计`

## 启动方式

启动后端：

```bash
python3 sau_platform_server.py --host 127.0.0.1 --port 5510
```

或者：

```bash
sau-platform --host 127.0.0.1 --port 5510
```

执行到期任务：

```bash
python3 sau_platform_worker.py --limit 10
```

或者：

```bash
sau-platform-worker --limit 10
```

持续运行（轮询调度）：

```bash
sau-platform-worker --loop --interval 30 --limit 10
```

## 数据存储

当前为了最小实现，平台数据使用：

- `data/platform.db`

这是一个基于 `sqlite3` 的本地数据库，用来支持个人使用和最小团队验证。

后续如果进入真正多人产品阶段，再切到：

- `PostgreSQL`
- `Redis`
- 对象存储
- Secret Store

## 当前接口

### 健康检查

`GET /health`

返回当前数据库位置和默认作用域。

### 获取默认作用域

`GET /api/v1/bootstrap`

返回默认：

- `tenant_id`
- `workspace_id`
- `api_key_path`
- `api_key`

说明：当前为了最小实现，`bootstrap` 会直接返回默认 `API Key`，用于本地快速验证。后续做真正的多用户平台时，这里会改成只返回一次或通过安全渠道下发。

除了 `GET /api/v1/bootstrap` 与 `/api/v1/auth/*`，其余 `/api/v1/*` 接口都需要带上：

优先使用登录态：

- `Authorization: Bearer <token>`

也可以用 `API Key` 作为服务侧/自动化调用凭证：

- `X-SAU-API-Key: <api_key>`

当前 `API Key` 同时决定工作区边界。接口会按 key 所属的 `tenant/workspace` 过滤数据。

登录态下系统会从 session 解析当前用户，不再需要 `X-SAU-User-Id`。只有在使用 `API Key` 调用时，才可以通过 `X-SAU-User-Id` 指定某个成员上下文。

当前角色层级：

- `viewer`
- `editor`
- `admin`
- `owner`

权限原则：

- `viewer`：只读
- `editor`：素材、草稿、发布计划、任务执行、AI 改写
- `admin`：用户、成员、账号、API Key
- `owner`：当前与 `admin` 等价，但保留最高权限语义

### 当前身份

`GET /api/v1/me`

返回当前请求解析出的成员上下文。

### 登录态

注册：

`POST /api/v1/auth/register`

登录：

`POST /api/v1/auth/login`

退出：

`POST /api/v1/auth/logout`

工作区列表（登录态）：

`GET /api/v1/workspaces`

切换工作区（登录态，返回新 token）：

`POST /api/v1/auth/switch-workspace`

示例：

```json
{
  "workspace_id": "workspace_xxx"
}
```

### API Key

查询 key：

`GET /api/v1/api-keys`

创建 key：

`POST /api/v1/api-keys`

吊销 key：

`POST /api/v1/api-keys/<api_key_id>/revoke`

轮换 key：

`POST /api/v1/api-keys/<api_key_id>/rotate`

### 用户

创建用户：

`POST /api/v1/users`

示例：

```json
{
  "email": "editor@example.com",
  "display_name": "Editor"
}
```

查询用户：

`GET /api/v1/users`

### 工作区成员

添加成员：

`POST /api/v1/workspace-members`

示例：

```json
{
  "user_id": "user_xxx",
  "role": "editor"
}
```

查询成员：

`GET /api/v1/workspace-members`

### 注册账号

`POST /api/v1/accounts`

示例：

```json
{
  "platform": "douyin",
  "account_name": "creator"
}
```

### 查询账号列表

`GET /api/v1/accounts`

### 检查账号健康状态

`POST /api/v1/accounts/<account_id>/check`

### 素材

当前素材接口是“只存元数据”的最小实现，不做文件上传。

创建素材：

`POST /api/v1/assets`

示例：

```json
{
  "asset_type": "video",
  "path": "demo.mp4"
}
```

查询素材：

`GET /api/v1/assets`

### 草稿

草稿用于复用标题、描述、标签和素材组合。

创建草稿：

`POST /api/v1/drafts`

示例：

```json
{
  "title": "草稿标题",
  "description": "草稿描述",
  "tags": ["测试"],
  "asset_ids": ["asset_xxx"]
}
```

查询草稿：

`GET /api/v1/drafts`

### AI 改写

`POST /api/v1/ai/rewrite`

示例：

```json
{
  "platform": "douyin",
  "title": "原标题",
  "description": "原描述",
  "tags": ["tag1", "tag2"]
}
```

默认情况下如果当前用户没有配置大模型，会走兜底改写（不编造、不新增事实）。

### 用户级 AI 配置

读取当前用户配置：

`GET /api/v1/ai/settings`

写入当前用户配置：

`POST /api/v1/ai/settings`

示例（OpenAI 兼容接口）：

```json
{
  "provider": "openai_compat",
  "base_url": "https://api.openai.com",
  "api_key": "sk-xxx",
  "model": "gpt-4.1-mini"
}
```

说明：

- API key 只保存在当前用户的配置中，接口返回会脱敏（`api_key_masked`）。
- 仍保留环境变量 `SAU_AI_BASE_URL/SAU_AI_API_KEY/SAU_AI_MODEL` 作为兜底（适合本地单人调试），但多人产品建议让每个用户自行配置。

### 创建发布计划

`POST /api/v1/publish-plans`

示例：

```json
{
  "platform": "douyin",
  "content_type": "video",
  "account_name": "creator",
  "payload": {
    "video_file": "demo.mp4",
    "title": "测试标题",
    "description": "测试描述",
    "tags": ["测试"]
  }
}
```

现在除了直接传 `payload`，也支持让发布计划引用：

- `draft_id`
- `asset_ids`

如果引用了 `draft_id` 且没有显式提供 `payload`，系统会优先从草稿中补齐：

- `title`
- `description`
- `tags`

如果内容类型是 `video`，且引用了视频素材但没有显式传 `video_file`，系统会自动取素材路径填入。

### 发布审批流

如果你在创建发布计划时传入：

`require_approval: true`

那么计划会以 `draft` 创建，你可以：

- 提交审批：`POST /api/v1/publish-plans/<plan_id>/submit`
- 通过：`POST /api/v1/publish-plans/<plan_id>/approve`
- 驳回：`POST /api/v1/publish-plans/<plan_id>/reject`

其中 `approve/reject` 需要 `admin/owner` 权限。

审批记录：

`GET /api/v1/approvals?plan_id=<plan_id>`

待审批计划：

`GET /api/v1/publish-plans/pending`

待我审批（会按当前登录用户判定；非 admin/owner 返回空列表）：

`GET /api/v1/publish-plans/pending-for-me`

我提交的：

`GET /api/v1/publish-plans/mine`

### 风控策略

查询策略：

`GET /api/v1/risk-policies`

写入/更新策略：

`POST /api/v1/risk-policies`

示例（账号维度）：

```json
{
  "scope_type": "account",
  "scope_key": "douyin:creator",
  "policy": {
    "cooldown_seconds": 120,
    "daily_limit": 20,
    "account_failure_threshold": 3,
    "failure_window_seconds": 600,
    "account_open_seconds": 600
  }
}
```

### 查询发布计划

`GET /api/v1/publish-plans`

### 查询任务列表

`GET /api/v1/tasks`

### 查询单个任务

`GET /api/v1/tasks/<task_id>`

### 立即执行单个任务

`POST /api/v1/tasks/<task_id>/run`

### 拉起到期任务

`POST /api/v1/tasks/run-due`

示例：

```json
{
  "limit": 5
}
```

## 当前支持的内容类型

视频：

- `douyin`
- `kuaishou`
- `xiaohongshu`
- `bilibili`
- `tencent`
- `youtube`

图文：

- `douyin`
- `kuaishou`
- `xiaohongshu`

## 当前边界

这个阶段故意只做最小闭环，还没有引入：

- 真正登录态用户认证
- 审核流
- 更细的高级风控策略
- 多租户真正隔离
- 分布式执行

这不是缺陷，而是当前阶段的刻意收敛。现在已经有多人产品骨架，下一步更适合继续补登录态用户系统、持久化前端、以及更完整的风控与审批流。
