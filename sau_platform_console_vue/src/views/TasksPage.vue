<template>
  <div class="page">
    <div class="page-header">
      <h1>任务中心</h1>
      <div class="muted">查看任务、执行任务</div>
    </div>

    <ReadonlyNotice
      v-if="!canEdit"
      message="当前角色只能查看任务与执行记录，不能手动触发任务执行。"
    />

    <div class="row">
      <div class="card">
        <div class="toolbar">
          <button class="secondary" @click="loadTasks">刷新列表</button>
          <button class="secondary" @click="runDue" :disabled="!canEdit">执行到期任务</button>
        </div>
        <div class="filter-bar">
          <input v-model="search" placeholder="搜索 task_id / plan_id / 错误类型" />
          <select v-model="statusFilter">
            <option value="">全部状态</option>
            <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
          </select>
          <span class="stats-line">共 {{ filteredTasks.length }} 条</span>
        </div>
        <LoadingBlock v-if="loadingList" text="正在加载任务列表..." />
        <DataTable v-else :columns="columns" :rows="filteredTasks" :selected-key="selectedId" empty-text="暂无任务" @select="onSelect" />
      </div>
      <div class="card">
        <h2>任务详情</h2>
        <div class="toolbar">
          <button @click="runTask" :disabled="!selectedId || !canEdit">执行任务</button>
          <button class="secondary" @click="loadTask" :disabled="!selectedId">刷新详情</button>
        </div>
        <div class="row" style="margin-top:10px;">
          <input v-model="taskIdInput" placeholder="task_id（可手动输入）" />
          <button class="secondary" @click="loadTaskByInput">加载</button>
        </div>
        <div v-if="selected" class="detail-panel" style="margin-top: 12px">
          <div class="toolbar">
            <span class="status-tag" :class="selected.status">{{ statusLabel(selected.status) }}</span>
            <span v-if="selected.last_error_type && selected.last_error_type !== 'none'" class="pill">
              {{ selected.last_error_type }}
            </span>
          </div>
          <div class="toolbar">
            <button class="secondary" @click="copyTaskId">复制 task_id</button>
            <button class="secondary" @click="goPlan">查看关联计划</button>
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
            <div class="detail-label">最近执行记录</div>
            <div v-if="taskRuns.length" class="timeline">
              <div v-for="run in taskRuns" :key="run.id" class="timeline-item">
                <div class="timeline-head">
                  <strong>{{ statusLabel(run.status) }}</strong>
                  <span class="muted">{{ run.started_at }}</span>
                </div>
                <div class="muted">结束时间：{{ run.finished_at || "-" }}</div>
                <div class="muted">错误类型：{{ run.error_type || "none" }}</div>
                <div v-if="run.error_message" style="margin-top: 8px">{{ run.error_message }}</div>
              </div>
            </div>
            <EmptyState v-else title="暂无执行记录" description="当前任务还没有运行历史。" />
          </div>
        </div>
        <EmptyState v-else title="请选择一个任务" description="点击左侧任务列表查看详情或执行任务。" />
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

type Task = any;
type TaskDetail = { task: Task; publish_plan?: any; runs: any[] };
const route = useRoute();
const router = useRouter();

const tasks = ref<Task[]>([]);
const selected = ref<Task | null>(null);
const taskRuns = ref<any[]>([]);
const taskIdInput = ref("");
const loadingList = ref(false);
const search = ref("");
const statusFilter = ref("");

const selectedId = computed(() => selected.value?.id || "");
const canEdit = computed(() => canEditContent(session.actor?.role));
const statusOptions = computed(() => Array.from(new Set(tasks.value.map((item) => item.status).filter(Boolean))));
const filteredTasks = computed(() => {
  const keyword = search.value.trim().toLowerCase();
  return tasks.value.filter((item) => {
    const matchStatus = !statusFilter.value || item.status === statusFilter.value;
    const matchKeyword =
      !keyword ||
      String(item.id || "").toLowerCase().includes(keyword) ||
      String(item.publish_plan_id || "").toLowerCase().includes(keyword) ||
      String(item.last_error_type || "").toLowerCase().includes(keyword);
    return matchStatus && matchKeyword;
  });
});
const payloadJson = computed(() => JSON.stringify(selected.value?.payload || {}, null, 2));
const detailItems = computed(() => {
  if (!selected.value) return [];
  return [
    { label: "task_id", value: selected.value.id || "-" },
    { label: "发布计划 ID", value: selected.value.publish_plan_id || "-" },
    { label: "执行次数", value: String(selected.value.attempts ?? 0) },
    { label: "下一次计划执行", value: selected.value.scheduled_at || "-" },
    { label: "最后错误类型", value: selected.value.last_error_type || "none" },
    { label: "最后错误信息", value: selected.value.last_error_message || "-", full: true },
    { label: "创建时间", value: selected.value.created_at || "-" },
    { label: "更新时间", value: selected.value.updated_at || "-" },
  ];
});
const columns: DataTableColumn[] = [
  { key: "id", label: "task_id", width: "240px" },
  { key: "status", label: "状态", width: "120px" },
  { key: "attempts", label: "次数", width: "80px" },
  { key: "scheduled_at", label: "计划执行时间" },
  { key: "last_error_type", label: "错误类型", width: "140px" },
];

async function loadTasks() {
  loadingList.value = true;
  try {
    const res = await api<Task[]>("/api/v1/tasks");
    tasks.value = res.data || [];
    applyRouteQuery();
    if (selected.value?.id) await loadTask();
  } finally {
    loadingList.value = false;
  }
}

function onSelect(task: Task) {
  selected.value = task;
  taskIdInput.value = task.id || "";
}

async function loadTask() {
  if (!selectedId.value) return;
  const res = await api<TaskDetail>(`/api/v1/tasks/${selectedId.value}`);
  selected.value = res.data?.task || selected.value;
  taskRuns.value = res.data?.runs || [];
}

async function loadTaskByInput() {
  if (!taskIdInput.value.trim()) return;
  const res = await api<TaskDetail>(`/api/v1/tasks/${taskIdInput.value.trim()}`);
  selected.value = res.data?.task || null;
  taskRuns.value = res.data?.runs || [];
}

function applyRouteQuery() {
  const q = String(route.query.q || "").trim();
  const status = String(route.query.status || "").trim();
  const plan = String(route.query.plan || "").trim();
  if (q) search.value = q;
  if (status) statusFilter.value = status;
  if (plan) {
    selected.value = tasks.value.find((item) => item.publish_plan_id === plan || item.id === plan) || tasks.value[0] || null;
  } else {
    selected.value = tasks.value[0] || null;
  }
  taskRuns.value = [];
  taskIdInput.value = selectedId.value;
}

async function copyTaskId() {
  if (!selectedId.value) return;
  const ok = await copyText(selectedId.value);
  showToast(ok ? "已复制 task_id" : "复制失败", ok ? "success" : "error");
}

function goPlan() {
  if (!selected.value?.publish_plan_id) return;
  router.push({ path: "/plans", query: { q: selected.value.publish_plan_id, plan: selected.value.publish_plan_id } });
}

async function runTask() {
  if (!selectedId.value) return;
  const { confirmed } = await confirmAction({
    title: "执行任务",
    message: "确认立即执行当前任务吗？",
    confirmText: "执行",
  });
  if (!confirmed) return;
  try {
    const res = await api<TaskDetail>(`/api/v1/tasks/${selectedId.value}/run`, { method: "POST", body: "{}" });
    selected.value = res.data?.task || selected.value;
    taskRuns.value = res.data?.runs || [];
    showToast("已触发任务执行", "success");
    await loadTasks();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  }
}

async function runDue() {
  const { confirmed } = await confirmAction({
    title: "执行到期任务",
    message: "确认批量执行当前工作区内到期任务吗？",
    confirmText: "开始执行",
  });
  if (!confirmed) return;
  try {
    const res = await api<any[]>("/api/v1/tasks/run-due", { method: "POST", body: JSON.stringify({ limit: 10 }) });
    showToast(`已触发到期任务执行，执行数量：${(res.data || []).length}`, "success");
    await loadTasks();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  }
}

loadTasks();
</script>
