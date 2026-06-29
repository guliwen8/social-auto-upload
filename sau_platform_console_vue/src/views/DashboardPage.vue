<template>
  <div class="page">
    <div class="card">
      <div class="page-header">
        <h1>仪表盘</h1>
        <div class="muted">当前工作区业务总览</div>
      </div>
      <div class="dashboard-grid" style="margin-top: 12px">
        <div class="stat-card">
          <div class="detail-label">发布计划</div>
          <div class="stat-value">{{ stats.planCount }}</div>
          <div class="muted">待审批 {{ stats.pendingApprovalCount }}</div>
        </div>
        <div class="stat-card">
          <div class="detail-label">任务</div>
          <div class="stat-value">{{ stats.taskCount }}</div>
          <div class="muted">失败 {{ stats.failedTaskCount }}</div>
        </div>
        <div class="stat-card">
          <div class="detail-label">账号</div>
          <div class="stat-value">{{ stats.accountCount }}</div>
          <div class="muted">异常 {{ stats.invalidAccountCount }}</div>
        </div>
        <div class="stat-card">
          <div class="detail-label">工作区</div>
          <div class="stat-value">{{ stats.workspaceCount }}</div>
          <div class="muted">当前角色 {{ roleLabel(session.actor?.role) }}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>快捷入口</h2>
      <div class="toolbar">
        <button class="secondary" @click="$router.push('/approvals')">审批中心</button>
        <button class="secondary" @click="$router.push('/tasks')">任务中心</button>
        <button class="secondary" @click="$router.push('/plans')">发布计划</button>
        <button class="secondary" @click="$router.push('/accounts')">账号中心</button>
        <button v-if="canManage" class="secondary" @click="$router.push('/risk-policies')">风控策略</button>
        <button v-if="canManage" class="secondary" @click="$router.push('/admin')">管理中心</button>
        <button class="secondary" @click="$router.push('/settings')">设置</button>
      </div>
    </div>

    <div class="card">
      <h2>异常提醒</h2>
      <LoadingBlock v-if="loading" text="正在生成健康摘要..." />
      <div v-else-if="alerts.length" class="stack">
        <div v-for="alert in alerts" :key="alert.title" class="alert-card" :class="alert.level">
          <div class="timeline-head">
            <strong>{{ alert.title }}</strong>
            <span class="muted">{{ alert.levelLabel }}</span>
          </div>
          <div>{{ alert.description }}</div>
          <div class="toolbar" style="margin-top: 8px">
            <button class="secondary" @click="$router.push(alert.to)">立即查看</button>
          </div>
        </div>
      </div>
      <EmptyState v-else title="当前没有明显异常" description="任务、计划与账号状态基本正常。" />
    </div>

    <div class="row">
      <div class="card">
        <h2>待审批</h2>
        <LoadingBlock v-if="loading" text="正在加载仪表盘..." />
        <div v-else-if="pendingApprovals.length" class="timeline">
          <div v-for="plan in pendingApprovals.slice(0, 5)" :key="plan.id" class="timeline-item">
            <div class="timeline-head">
              <strong>{{ plan.account_name }}</strong>
              <span class="muted">{{ plan.created_at }}</span>
            </div>
            <div class="muted">plan_id：{{ plan.id }}</div>
            <div class="muted">{{ plan.platform }} / {{ plan.content_type }}</div>
            <div class="toolbar" style="margin-top: 8px">
              <button class="secondary" @click="$router.push({ path: '/approvals', query: { q: plan.id, plan: plan.id } })">
                打开审批
              </button>
            </div>
          </div>
        </div>
        <EmptyState v-else title="暂无待审批计划" description="当前工作区没有待你处理的审批。" />
      </div>

      <div class="card">
        <h2>最近任务</h2>
        <LoadingBlock v-if="loading" text="正在加载任务摘要..." />
        <div v-else-if="recentTasks.length" class="timeline">
          <div v-for="task in recentTasks.slice(0, 5)" :key="task.id" class="timeline-item">
            <div class="timeline-head">
              <strong>{{ statusLabel(task.status) }}</strong>
              <span class="muted">{{ task.updated_at }}</span>
            </div>
            <div class="muted">task_id：{{ task.id }}</div>
            <div class="muted">plan_id：{{ task.publish_plan_id }}</div>
            <div class="toolbar" style="margin-top: 8px">
              <button class="secondary" @click="$router.push({ path: '/tasks', query: { q: task.id, plan: task.publish_plan_id } })">
                查看任务
              </button>
            </div>
          </div>
        </div>
        <EmptyState v-else title="暂无任务" description="当前工作区还没有任务数据。" />
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h2>最近计划</h2>
        <LoadingBlock v-if="loading" text="正在加载计划摘要..." />
        <div v-else-if="recentPlans.length" class="timeline">
          <div v-for="plan in recentPlans.slice(0, 5)" :key="plan.id" class="timeline-item">
            <div class="timeline-head">
              <strong>{{ statusLabel(plan.status) }}</strong>
              <span class="muted">{{ plan.updated_at }}</span>
            </div>
            <div class="muted">账号：{{ plan.account_name }}</div>
            <div class="muted">plan_id：{{ plan.id }}</div>
            <div class="toolbar" style="margin-top: 8px">
              <button class="secondary" @click="$router.push({ path: '/plans', query: { q: plan.id, plan: plan.id } })">
                查看计划
              </button>
            </div>
          </div>
        </div>
        <EmptyState v-else title="暂无计划" description="当前工作区还没有发布计划。" />
      </div>

      <div class="card">
        <h2>当前身份</h2>
        <div class="detail-panel">
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">显示名</div>
              <div class="detail-value">{{ session.actor?.display_name || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">邮箱</div>
              <div class="detail-value">{{ session.actor?.email || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">角色</div>
              <div class="detail-value">{{ roleLabel(session.actor?.role) }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">工作区</div>
              <div class="detail-value">{{ session.actor?.workspace_id || "-" }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { api } from "../api/client";
import EmptyState from "../components/EmptyState.vue";
import LoadingBlock from "../components/LoadingBlock.vue";
import { showToast } from "../state/ui";
import { canManageSystem, refreshSession, session } from "../state/session";
import { roleLabel, statusLabel } from "../utils/display";

const loading = ref(false);
const canManage = computed(() => canManageSystem(session.actor?.role));
const recentPlans = ref<any[]>([]);
const recentTasks = ref<any[]>([]);
const pendingApprovals = ref<any[]>([]);
const alerts = ref<Array<{ title: string; description: string; to: any; level: string; levelLabel: string }>>([]);
const stats = reactive({
  planCount: 0,
  pendingApprovalCount: 0,
  taskCount: 0,
  failedTaskCount: 0,
  accountCount: 0,
  invalidAccountCount: 0,
  workspaceCount: 0,
});

onMounted(async () => {
  await refreshSession();
  await loadDashboard();
});

async function loadDashboard() {
  loading.value = true;
  try {
    const [plansRes, tasksRes, accountsRes, pendingRes] = await Promise.all([
      api<any[]>("/api/v1/publish-plans"),
      api<any[]>("/api/v1/tasks"),
      api<any[]>("/api/v1/accounts"),
      api<any[]>("/api/v1/publish-plans/pending-for-me"),
    ]);

    const plans = plansRes.data || [];
    const tasks = tasksRes.data || [];
    const accounts = accountsRes.data || [];
    const pending = pendingRes.data || [];

    recentPlans.value = [...plans].sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || "")));
    recentTasks.value = [...tasks].sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || "")));
    pendingApprovals.value = pending;

    stats.planCount = plans.length;
    stats.pendingApprovalCount = pending.length;
    stats.taskCount = tasks.length;
    stats.failedTaskCount = tasks.filter((item) => item.status === "failed").length;
    stats.accountCount = accounts.length;
    stats.invalidAccountCount = accounts.filter((item) => item.status === "invalid").length;
    stats.workspaceCount = (session.workspaces || []).length;
    alerts.value = buildAlerts({ plans, tasks, accounts, pending });
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

function buildAlerts(payload: { plans: any[]; tasks: any[]; accounts: any[]; pending: any[] }) {
  const result: Array<{ title: string; description: string; to: any; level: string; levelLabel: string }> = [];
  const failedTasks = payload.tasks.filter((item) => item.status === "failed");
  const invalidAccounts = payload.accounts.filter((item) => item.status === "invalid");
  const stuckApprovals = payload.pending.filter((item) => item.status === "pending_approval");

  if (failedTasks.length) {
    result.push({
      title: "存在失败任务",
      description: `当前有 ${failedTasks.length} 个失败任务，建议优先检查错误类型与最近执行记录。`,
      to: { path: "/tasks", query: { status: "failed", q: failedTasks[0]?.id || "" } },
      level: "danger",
      levelLabel: "高优先级",
    });
  }
  if (invalidAccounts.length) {
    result.push({
      title: "存在异常账号",
      description: `当前有 ${invalidAccounts.length} 个账号状态异常，建议尽快执行健康检查或修复登录态。`,
      to: { path: "/accounts", query: { status: "invalid", account: invalidAccounts[0]?.id || "" } },
      level: "warning",
      levelLabel: "需处理",
    });
  }
  if (stuckApprovals.length) {
    result.push({
      title: "存在待审批计划",
      description: `当前有 ${stuckApprovals.length} 条计划等待审批，可能影响发布节奏。`,
      to: { path: "/approvals", query: { plan: stuckApprovals[0]?.id || "", q: stuckApprovals[0]?.id || "" } },
      level: "info",
      levelLabel: "待关注",
    });
  }
  if (!result.length && canManage.value) {
    result.push({
      title: "系统运行平稳",
      description: "当前未发现明显异常。你可以前往风控策略或管理中心继续维护系统配置。",
      to: { path: "/risk-policies" },
      level: "success",
      levelLabel: "正常",
    });
  }
  return result;
}
</script>
