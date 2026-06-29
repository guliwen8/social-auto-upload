<template>
  <div class="page">
    <div class="page-header">
      <h1>发布计划</h1>
      <div class="muted">创建/列表/提交审批</div>
    </div>

    <ReadonlyNotice
      v-if="!canEdit"
      message="当前角色只能查看计划与审批状态，不能创建计划或提交审批。"
    />

    <div class="card">
      <h2>创建计划</h2>
      <div class="row">
        <select v-model="platform">
          <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
        </select>
        <select v-model="contentType">
          <option value="video">video</option>
          <option value="note">note</option>
        </select>
      </div>
      <div class="row" style="margin-top:10px;">
        <input v-model="accountName" placeholder="account_name" />
        <label class="muted" style="display:flex;align-items:center;gap:8px;">
          <input v-model="requireApproval" type="checkbox" style="width:auto;" />
          需要审批
        </label>
      </div>
      <div class="row" style="margin-top:10px;">
        <input v-model="draftId" placeholder="draft_id（可选）" />
        <input v-model="assetIds" placeholder="asset_ids（可选，逗号分隔）" />
      </div>
      <textarea v-model="payloadRaw" placeholder='payload JSON（可选）例如 {"title":"标题","video_file":"demo.mp4"}' style="margin-top:10px;"></textarea>
      <div class="toolbar" style="margin-top:10px;">
        <button @click="createPlan" :disabled="loading || !canEdit">创建</button>
        <button class="secondary" @click="loadPlans" :disabled="loading">刷新列表</button>
      </div>
      <LoadingBlock v-if="loading && !createdPlan?.id" text="正在创建计划..." />
      <div v-if="createdPlan" class="detail-panel" style="margin-top: 12px">
        <div class="toolbar">
            <span class="status-tag" :class="createdPlan.status">{{ statusLabel(createdPlan.status) }}</span>
          <button class="secondary" @click="selectCreatedPlan">定位到详情</button>
        </div>
        <div class="detail-grid">
          <div class="detail-item">
            <div class="detail-label">plan_id</div>
            <div class="detail-value">{{ createdPlan.id }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">账号</div>
            <div class="detail-value">{{ createdPlan.account_name || "-" }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">平台</div>
            <div class="detail-value">{{ createdPlan.platform || "-" }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">类型</div>
            <div class="detail-value">{{ createdPlan.content_type || "-" }}</div>
          </div>
        </div>
      </div>
      <EmptyState v-else title="尚未创建计划" description="创建成功后，这里会显示新计划摘要。" />
    </div>

    <div class="row">
      <div class="card">
        <h2>计划列表</h2>
        <div class="toolbar">
          <button class="secondary" @click="selectMine">我提交的</button>
          <button class="secondary" @click="selectAll">全部</button>
        </div>
        <div class="filter-bar">
          <input v-model="search" placeholder="搜索 plan_id / 账号 / 平台" />
          <select v-model="statusFilter">
            <option value="">全部状态</option>
            <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
          </select>
          <span class="stats-line">共 {{ filteredPlans.length }} 条</span>
        </div>
        <LoadingBlock v-if="loadingList" text="正在加载计划列表..." />
        <DataTable v-else :columns="columns" :rows="filteredPlans" :selected-key="selectedId" empty-text="暂无计划" @select="onSelect" />
      </div>
      <div class="card">
        <h2>计划详情</h2>
        <div class="toolbar">
          <button class="secondary" @click="loadApprovals" :disabled="!selectedId">审批记录</button>
          <button @click="submit" :disabled="!canSubmit || !canEdit">提交审批</button>
        </div>
        <div v-if="selected" class="detail-panel" style="margin-top: 12px">
          <div class="toolbar">
            <span class="status-tag" :class="selected.status">{{ statusLabel(selected.status) }}</span>
            <span class="pill">{{ selected.platform }}</span>
            <span class="pill">{{ selected.content_type }}</span>
          </div>
          <div class="toolbar">
            <button class="secondary" @click="copyPlanId">复制 plan_id</button>
            <button class="secondary" @click="goTasks">查看关联任务</button>
            <button class="secondary" @click="goAccount">查看账号</button>
            <button v-if="selected.draft_id" class="secondary" @click="goDraft">查看草稿</button>
          </div>
          <div class="detail-grid">
            <div v-for="item in detailItems" :key="item.label" class="detail-item" :class="{ full: item.full }">
              <div class="detail-label">{{ item.label }}</div>
              <div class="detail-value">{{ item.value }}</div>
            </div>
          </div>
          <div class="detail-item full">
            <div class="detail-label">payload</div>
            <pre>{{ payloadJson }}</pre>
          </div>
          <div class="detail-item full">
            <div class="detail-label">审批记录</div>
            <LoadingBlock v-if="loadingApprovals" text="正在加载审批记录..." />
            <div v-else-if="approvals.length" class="timeline">
              <div v-for="record in approvals" :key="record.id" class="timeline-item">
                <div class="timeline-head">
                  <strong>{{ record.action }}</strong>
                  <span class="muted">{{ record.created_at }}</span>
                </div>
                <div class="muted">审批人：{{ record.actor_user_id || "-" }}</div>
                <div v-if="record.comment" style="margin-top: 8px">{{ record.comment }}</div>
              </div>
            </div>
            <EmptyState v-else title="暂无审批记录" description="当前计划还没有审批流水。" />
          </div>
          <div class="detail-item full">
            <div class="detail-label">关联任务摘要</div>
            <div v-if="relatedTasks.length" class="timeline">
              <div v-for="task in relatedTasks.slice(0, 3)" :key="task.id" class="timeline-item">
                <div class="timeline-head">
                  <strong>{{ statusLabel(task.status) }}</strong>
                  <span class="muted">{{ task.updated_at }}</span>
                </div>
                <div class="muted">task_id：{{ task.id }}</div>
                <div class="muted">尝试次数：{{ task.attempts ?? 0 }}</div>
                <div class="muted">错误类型：{{ task.last_error_type || "none" }}</div>
                <div class="toolbar" style="margin-top: 8px">
                  <button class="secondary" @click="$router.push({ path: '/tasks', query: { q: task.id, plan: task.publish_plan_id } })">
                    查看任务
                  </button>
                </div>
              </div>
            </div>
            <EmptyState v-else title="暂无关联任务" description="当前计划还没有生成任务或任务尚未进入列表。" />
          </div>
        </div>
        <EmptyState v-else title="请选择一条计划" description="点击左侧计划列表查看详情。" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api/client";
import DataTable, { type DataTableColumn } from "../components/DataTable.vue";
import EmptyState from "../components/EmptyState.vue";
import LoadingBlock from "../components/LoadingBlock.vue";
import ReadonlyNotice from "../components/ReadonlyNotice.vue";
import { confirmAction, showToast } from "../state/ui";
import { copyText } from "../utils/clipboard";
import { canEditContent, session } from "../state/session";
import { statusLabel } from "../utils/display";

type Plan = any;
const route = useRoute();
const router = useRouter();

const platforms = ["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent", "youtube"];
const platform = ref("douyin");
const contentType = ref<"video" | "note">("video");
const accountName = ref("");
const draftId = ref("");
const assetIds = ref("");
const requireApproval = ref(true);
const payloadRaw = ref("");

const loading = ref(false);
const loadingList = ref(false);
const loadingApprovals = ref(false);
const createdPlan = ref<any | null>(null);
const search = ref("");
const statusFilter = ref("");
const allTasks = ref<any[]>([]);

const plans = ref<Plan[]>([]);
const selected = ref<Plan | null>(null);
const approvals = ref<any[]>([]);

const selectedId = computed(() => selected.value?.id || "");
const canEdit = computed(() => canEditContent(session.actor?.role));
const statusOptions = computed(() => Array.from(new Set(plans.value.map((item) => item.status).filter(Boolean))));
const filteredPlans = computed(() => {
  const keyword = search.value.trim().toLowerCase();
  return plans.value.filter((item) => {
    const matchStatus = !statusFilter.value || item.status === statusFilter.value;
    const matchKeyword =
      !keyword ||
      String(item.id || "").toLowerCase().includes(keyword) ||
      String(item.account_name || "").toLowerCase().includes(keyword) ||
      String(item.platform || "").toLowerCase().includes(keyword) ||
      String(item.draft_id || "").toLowerCase().includes(keyword) ||
      String((item.asset_ids || []).join(", ") || "").toLowerCase().includes(keyword);
    return matchStatus && matchKeyword;
  });
});
const payloadJson = computed(() => JSON.stringify(selected.value?.payload || {}, null, 2));
const canSubmit = computed(() => Boolean(selected.value && selected.value.status === "draft"));
const relatedTasks = computed(() => {
  if (!selected.value?.id) return [];
  return allTasks.value.filter((item) => item.publish_plan_id === selected.value.id);
});
const detailItems = computed(() => {
  if (!selected.value) return [];
  return [
    { label: "plan_id", value: selected.value.id || "-" },
    { label: "账号", value: selected.value.account_name || "-" },
    { label: "提交人", value: selected.value.created_by || "-" },
    { label: "草稿 ID", value: selected.value.draft_id || "-" },
    { label: "素材 IDs", value: (selected.value.asset_ids || []).join(", ") || "-", full: true },
    { label: "计划执行时间", value: selected.value.schedule_at || "-" },
    { label: "创建时间", value: selected.value.created_at || "-" },
    { label: "更新时间", value: selected.value.updated_at || "-" },
  ];
});
const columns: DataTableColumn[] = [
  { key: "id", label: "plan_id", width: "240px" },
  { key: "platform", label: "平台", width: "100px" },
  { key: "account_name", label: "账号" },
  { key: "content_type", label: "类型", width: "90px" },
  { key: "status", label: "状态", width: "140px" },
];

async function createPlan() {
  loading.value = true;
  try {
    const asset_ids = assetIds.value.split(",").map((s) => s.trim()).filter(Boolean);
    const payload = payloadRaw.value.trim() ? JSON.parse(payloadRaw.value.trim()) : {};
    const res = await api("/api/v1/publish-plans", {
      method: "POST",
      body: JSON.stringify({
        platform: platform.value,
        content_type: contentType.value,
        account_name: accountName.value.trim(),
        draft_id: draftId.value.trim() || undefined,
        asset_ids,
        require_approval: requireApproval.value,
        payload,
      }),
    });
    createdPlan.value = res.data;
    showToast("发布计划已创建", "success");
    await loadPlans();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

function selectCreatedPlan() {
  if (!createdPlan.value?.id) return;
  selected.value = plans.value.find((item) => item.id === createdPlan.value.id) || createdPlan.value;
}

async function loadPlans() {
  loadingList.value = true;
  try {
    const res = await api<Plan[]>("/api/v1/publish-plans");
    plans.value = res.data || [];
    const taskRes = await api<any[]>("/api/v1/tasks");
    allTasks.value = taskRes.data || [];
    applyRouteQuery();
    approvals.value = [];
  } finally {
    loadingList.value = false;
  }
}

function onSelect(plan: Plan) {
  selected.value = plan;
}

async function loadApprovals() {
  approvals.value = [];
  if (!selectedId.value) return;
  loadingApprovals.value = true;
  try {
    const res = await api<any[]>(`/api/v1/approvals?plan_id=${encodeURIComponent(selectedId.value)}`);
    approvals.value = res.data || [];
  } finally {
    loadingApprovals.value = false;
  }
}

async function submit() {
  if (!selectedId.value) return;
  const { confirmed } = await confirmAction({
    title: "提交审批",
    message: "确认将当前计划提交进入审批流程吗？",
    confirmText: "提交",
  });
  if (!confirmed) return;
  try {
    const res = await api(`/api/v1/publish-plans/${selectedId.value}/submit`, { method: "POST", body: "{}" });
    showToast("已提交审批", "success");
    selected.value = res.data;
    await loadApprovals();
    await loadPlans();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  }
}

async function selectMine() {
  const res = await api<Plan[]>("/api/v1/publish-plans/mine");
  plans.value = res.data || [];
  const taskRes = await api<any[]>("/api/v1/tasks");
  allTasks.value = taskRes.data || [];
  applyRouteQuery();
}

async function selectAll() {
  await loadPlans();
}

function applyRouteQuery() {
  const q = String(route.query.q || "").trim();
  const status = String(route.query.status || "").trim();
  const plan = String(route.query.plan || "").trim();
  if (q) search.value = q;
  if (status) statusFilter.value = status;
  if (plan) {
    selected.value = plans.value.find((item) => item.id === plan) || plans.value[0] || null;
  } else {
    selected.value = plans.value[0] || null;
  }
}

async function copyPlanId() {
  if (!selectedId.value) return;
  const ok = await copyText(selectedId.value);
  showToast(ok ? "已复制 plan_id" : "复制失败", ok ? "success" : "error");
}

function goTasks() {
  if (!selectedId.value) return;
  router.push({ path: "/tasks", query: { q: selectedId.value, plan: selectedId.value } });
}

function goAccount() {
  if (!selected.value) return;
  router.push({ path: "/accounts", query: { q: selected.value.account_name || "" } });
}

function goDraft() {
  if (!selected.value?.draft_id) return;
  router.push({ path: "/content", query: { draft: selected.value.draft_id } });
}

loadPlans();
</script>
