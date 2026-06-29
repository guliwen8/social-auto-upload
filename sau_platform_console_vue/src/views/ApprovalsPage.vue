<template>
  <div class="page">
    <div class="page-header">
      <h1>审批中心</h1>
      <div class="muted">待我审批 / 我提交的</div>
    </div>

    <ReadonlyNotice
      v-if="!canEdit"
      message="当前角色只能查看审批数据，不能执行通过、驳回等审批动作。"
    />

    <div class="card">
      <div class="toolbar">
        <button class="secondary" @click="loadPending">待我审批</button>
        <button class="secondary" @click="loadMine">我提交的</button>
        <button class="secondary" @click="loadRecordsPrompt">按 plan_id 查记录</button>
      </div>
      <div class="filter-bar">
        <input v-model="search" placeholder="搜索 plan_id / 账号 / 平台 / 提交人" />
        <select v-model="statusFilter">
          <option value="">全部状态</option>
          <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
        </select>
        <span class="stats-line">共 {{ filteredList.length }} 条</span>
      </div>
      <LoadingBlock v-if="loadingList" text="正在加载审批列表..." />
      <DataTable v-else :columns="columns" :rows="filteredList" :selected-key="selectedId" empty-text="暂无计划" @select="onSelect" />
    </div>

    <div class="card">
      <h2>选中计划</h2>
      <div class="toolbar">
        <button @click="approve" :disabled="!selectedId || !canEdit">通过</button>
        <button class="secondary" @click="reject" :disabled="!selectedId || !canEdit">驳回</button>
        <button class="secondary" @click="loadApprovals" :disabled="!selectedId">刷新记录</button>
      </div>
      <div class="row" style="margin-top: 12px">
        <div class="card">
          <div v-if="selected" class="detail-panel">
            <div class="toolbar">
              <span class="status-tag" :class="selected.status">{{ statusLabel(selected.status) }}</span>
              <span class="pill">{{ selected.platform }}</span>
              <span class="pill">{{ selected.content_type }}</span>
            </div>
            <div class="toolbar">
              <button class="secondary" @click="copyPlanId">复制 plan_id</button>
              <button class="secondary" @click="goTasks">查看关联任务</button>
              <button class="secondary" @click="goAccount">查看账号</button>
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
          </div>
          <EmptyState v-else title="请选择一条计划" description="点击左侧列表后可查看详情与审批操作。" />
        </div>
        <div class="card">
          <div class="muted" style="margin-bottom: 10px">审批记录</div>
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
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
const router = useRouter();

const list = ref<Plan[]>([]);
const selected = ref<Plan | null>(null);
const approvals = ref<any[]>([]);
const loadingList = ref(false);
const loadingApprovals = ref(false);
const search = ref("");
const statusFilter = ref("");

const selectedId = computed(() => selected.value?.id || "");
const canEdit = computed(() => canEditContent(session.actor?.role));
const statusOptions = computed(() => Array.from(new Set(list.value.map((item) => item.status).filter(Boolean))));
const filteredList = computed(() => {
  const keyword = search.value.trim().toLowerCase();
  return list.value.filter((item) => {
    const matchStatus = !statusFilter.value || item.status === statusFilter.value;
    const matchKeyword =
      !keyword ||
      String(item.id || "").toLowerCase().includes(keyword) ||
      String(item.account_name || "").toLowerCase().includes(keyword) ||
      String(item.platform || "").toLowerCase().includes(keyword) ||
      String(item.created_by || "").toLowerCase().includes(keyword);
    return matchStatus && matchKeyword;
  });
});
const payloadJson = computed(() => JSON.stringify(selected.value?.payload || {}, null, 2));
const detailItems = computed(() => {
  if (!selected.value) return [];
  return [
    { label: "plan_id", value: selected.value.id || "-" },
    { label: "账号", value: selected.value.account_name || "-" },
    { label: "提交人", value: selected.value.created_by || "-" },
    { label: "草稿 ID", value: selected.value.draft_id || "-", full: false },
    { label: "素材 IDs", value: (selected.value.asset_ids || []).join(", ") || "-", full: true },
    { label: "计划执行时间", value: selected.value.schedule_at || "-", full: false },
    { label: "创建时间", value: selected.value.created_at || "-", full: false },
    { label: "更新时间", value: selected.value.updated_at || "-", full: false },
  ];
});
const columns: DataTableColumn[] = [
  { key: "id", label: "plan_id", width: "240px" },
  { key: "platform", label: "平台", width: "100px" },
  { key: "account_name", label: "账号" },
  { key: "content_type", label: "类型", width: "90px" },
  { key: "status", label: "状态", width: "140px" },
  { key: "created_by", label: "提交人", width: "180px" },
];

function selectFirst(plans: Plan[]) {
  selected.value = plans[0] || null;
}

function onSelect(plan: Plan) {
  selected.value = plan;
  loadApprovals();
}

async function loadPending() {
  loadingList.value = true;
  try {
    const res = await api<Plan[]>("/api/v1/publish-plans/pending-for-me");
    list.value = res.data || [];
    selectFirst(list.value);
    await loadApprovals();
  } finally {
    loadingList.value = false;
  }
}

async function loadMine() {
  loadingList.value = true;
  try {
    const res = await api<Plan[]>("/api/v1/publish-plans/mine");
    list.value = res.data || [];
    selectFirst(list.value);
    await loadApprovals();
  } finally {
    loadingList.value = false;
  }
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

async function approve() {
  if (!selectedId.value) return;
  const { confirmed, value } = await confirmAction({
    title: "通过审批",
    message: "确认通过当前发布计划吗？你也可以补充审批意见。",
    inputLabel: "审批意见（可选）",
    inputPlaceholder: "输入审批意见",
    confirmText: "通过",
  });
  if (!confirmed) return;
  try {
    await api(`/api/v1/publish-plans/${selectedId.value}/approve`, {
      method: "POST",
      body: JSON.stringify({ comment: value }),
    });
    showToast("已通过审批", "success");
    await loadApprovals();
    await loadPending();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  }
}

async function reject() {
  if (!selectedId.value) return;
  const { confirmed, value } = await confirmAction({
    title: "驳回审批",
    message: "请输入驳回原因，提交后当前计划会进入 rejected 状态。",
    inputLabel: "驳回原因",
    inputPlaceholder: "请输入驳回原因",
    inputRequired: true,
    confirmText: "驳回",
    danger: true,
  });
  if (!confirmed) return;
  try {
    await api(`/api/v1/publish-plans/${selectedId.value}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason: value }),
    });
    showToast("已驳回审批", "success");
    await loadApprovals();
    await loadPending();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  }
}

async function loadRecordsPrompt() {
  const { confirmed, value } = await confirmAction({
    title: "查询审批记录",
    message: "输入 plan_id 后查看对应的审批记录。",
    inputLabel: "plan_id",
    inputPlaceholder: "请输入 plan_id",
    inputRequired: true,
    confirmText: "查询",
  });
  if (!confirmed) return;
  selected.value = { id: value.trim() };
  await loadApprovals();
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

// default
loadPending();
</script>
