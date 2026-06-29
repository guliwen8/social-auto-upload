<template>
  <div class="page">
    <div class="page-header">
      <h1>账号中心</h1>
      <div class="muted">注册账号、查看详情、执行健康检查</div>
    </div>

    <ReadonlyNotice
      v-if="!canEdit"
      message="当前角色只能查看账号状态与关联计划，不能注册账号或执行健康检查。"
    />

    <div class="card">
      <h2>注册账号</h2>
      <div class="row">
        <select v-model="platform">
          <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
        </select>
        <input v-model="accountName" placeholder="account_name" />
      </div>
      <div class="toolbar" style="margin-top: 10px">
        <button @click="createAccount" :disabled="loading || !canEdit">注册</button>
        <button class="secondary" @click="loadAccounts" :disabled="loading">刷新列表</button>
      </div>
      <LoadingBlock v-if="loading && !createdAccount?.id" text="正在注册账号..." />
      <div v-if="createdAccount" class="detail-panel" style="margin-top: 12px">
        <div class="toolbar">
          <span class="status-tag" :class="createdAccount.status">{{ statusLabel(createdAccount.status) }}</span>
          <button class="secondary" @click="selectCreatedAccount">定位到详情</button>
        </div>
        <div class="detail-grid">
          <div class="detail-item">
            <div class="detail-label">account_id</div>
            <div class="detail-value">{{ createdAccount.id }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">账号名</div>
            <div class="detail-value">{{ createdAccount.account_name || "-" }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">平台</div>
            <div class="detail-value">{{ createdAccount.platform || "-" }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">创建时间</div>
            <div class="detail-value">{{ createdAccount.created_at || "-" }}</div>
          </div>
        </div>
      </div>
      <EmptyState v-else title="尚未注册账号" description="注册成功后，这里会显示新账号摘要。" />
    </div>

    <div class="row">
      <div class="card">
        <h2>账号列表</h2>
        <div class="filter-bar">
          <input v-model="search" placeholder="搜索 account_id / 账号名 / 平台" />
          <select v-model="statusFilter">
            <option value="">全部状态</option>
            <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
          </select>
          <span class="stats-line">共 {{ filteredAccounts.length }} 条</span>
        </div>
        <LoadingBlock v-if="loadingList" text="正在加载账号列表..." />
        <DataTable v-else :columns="columns" :rows="filteredAccounts" :selected-key="selectedId" empty-text="暂无账号" @select="onSelect" />
      </div>

      <div class="card">
        <h2>账号详情</h2>
        <div class="toolbar">
          <button @click="checkAccount" :disabled="!selectedId || loading || !canEdit">健康检查</button>
          <button class="secondary" @click="loadAccounts" :disabled="loading">刷新</button>
        </div>

        <div v-if="selected" class="detail-panel" style="margin-top: 12px">
          <div class="toolbar">
            <span class="status-tag" :class="selected.status">{{ statusLabel(selected.status) }}</span>
            <span class="pill">{{ selected.platform }}</span>
          </div>
          <div class="toolbar">
            <button class="secondary" @click="copyAccountId">复制 account_id</button>
            <button class="secondary" @click="goPlans">查看相关计划</button>
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">account_id</div>
              <div class="detail-value">{{ selected.id }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">账号名</div>
              <div class="detail-value">{{ selected.account_name }}</div>
            </div>
            <div class="detail-item full">
              <div class="detail-label">账号文件</div>
              <div class="detail-value">{{ selected.account_file || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">创建时间</div>
              <div class="detail-value">{{ selected.created_at || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">更新时间</div>
              <div class="detail-value">{{ selected.updated_at || "-" }}</div>
            </div>
          </div>

          <div class="detail-item full">
            <div class="detail-label">最近一次检查结果</div>
            <div class="detail-value">{{ checkHint || "尚未执行健康检查" }}</div>
          </div>
          <div class="detail-item full">
            <div class="detail-label">相关计划</div>
            <div v-if="relatedPlans.length" class="timeline">
              <div v-for="plan in relatedPlans.slice(0, 3)" :key="plan.id" class="timeline-item">
                <div class="timeline-head">
                  <strong>{{ statusLabel(plan.status) }}</strong>
                  <span class="muted">{{ plan.updated_at }}</span>
                </div>
                <div class="muted">plan_id：{{ plan.id }}</div>
                <div class="muted">平台：{{ plan.platform }}</div>
                <div class="muted">类型：{{ plan.content_type }}</div>
                <div class="toolbar" style="margin-top: 8px">
                  <button class="secondary" @click="$router.push({ path: '/plans', query: { q: plan.id, plan: plan.id } })">
                    查看计划
                  </button>
                </div>
              </div>
            </div>
            <EmptyState v-else title="暂无相关计划" description="当前账号还没有关联的发布计划。" />
          </div>
        </div>

        <EmptyState v-else title="请选择一个账号" description="点击左侧账号列表查看详情并执行健康检查。" />
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

type Account = {
  id: string;
  platform: string;
  account_name: string;
  account_file: string;
  status: string;
  created_at: string;
  updated_at: string;
};
const route = useRoute();
const router = useRouter();

const platforms = ["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent", "youtube"];
const platform = ref("douyin");
const accountName = ref("");

const loading = ref(false);
const loadingList = ref(false);
const checkHint = ref("");
const createdAccount = ref<Account | null>(null);
const allPlans = ref<any[]>([]);

const accounts = ref<Account[]>([]);
const selected = ref<Account | null>(null);
const search = ref("");
const statusFilter = ref("");

const selectedId = computed(() => selected.value?.id || "");
const canEdit = computed(() => canEditContent(session.actor?.role));
const statusOptions = computed(() => Array.from(new Set(accounts.value.map((item) => item.status).filter(Boolean))));
const filteredAccounts = computed(() => {
  const keyword = search.value.trim().toLowerCase();
  return accounts.value.filter((item) => {
    const matchStatus = !statusFilter.value || item.status === statusFilter.value;
    const matchKeyword =
      !keyword ||
      String(item.id || "").toLowerCase().includes(keyword) ||
      String(item.account_name || "").toLowerCase().includes(keyword) ||
      String(item.platform || "").toLowerCase().includes(keyword);
    return matchStatus && matchKeyword;
  });
});
const relatedPlans = computed(() => {
  if (!selected.value?.account_name) return [];
  return allPlans.value.filter((item) => item.account_name === selected.value?.account_name);
});

const columns: DataTableColumn[] = [
  { key: "id", label: "account_id", width: "240px" },
  { key: "platform", label: "平台", width: "100px" },
  { key: "account_name", label: "账号名" },
  { key: "status", label: "状态", width: "120px" },
  { key: "updated_at", label: "更新时间", width: "180px" },
];

async function loadAccounts() {
  loadingList.value = true;
  try {
    const res = await api<Account[]>("/api/v1/accounts");
    accounts.value = res.data || [];
    const planRes = await api<any[]>("/api/v1/publish-plans");
    allPlans.value = planRes.data || [];
    applyRouteQuery();
  } finally {
    loadingList.value = false;
  }
}

function onSelect(row: Record<string, any>) {
  selected.value = row as Account;
  checkHint.value = "";
}

async function createAccount() {
  loading.value = true;
  try {
    const res = await api<Account>("/api/v1/accounts", {
      method: "POST",
      body: JSON.stringify({
        platform: platform.value,
        account_name: accountName.value.trim(),
      }),
    });
    createdAccount.value = res.data;
    showToast("账号已注册", "success");
    accountName.value = "";
    await loadAccounts();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

function selectCreatedAccount() {
  if (!createdAccount.value?.id) return;
  selected.value = accounts.value.find((item) => item.id === createdAccount.value?.id) || createdAccount.value;
}

async function checkAccount() {
  if (!selectedId.value) return;
  const { confirmed } = await confirmAction({
    title: "执行账号健康检查",
    message: "确认检查当前账号的登录态和可用性吗？",
    confirmText: "开始检查",
  });
  if (!confirmed) return;
  loading.value = true;
  try {
    const res = await api<{ account: Account; is_valid: boolean }>(`/api/v1/accounts/${selectedId.value}/check`, {
      method: "POST",
      body: "{}",
    });
    selected.value = res.data.account;
    checkHint.value = res.data.is_valid ? "检查通过，账号有效" : "检查失败，账号无效或登录态过期";
    showToast("健康检查已完成", res.data.is_valid ? "success" : "error");
    await loadAccounts();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

function applyRouteQuery() {
  const q = String(route.query.q || "").trim();
  const status = String(route.query.status || "").trim();
  const account = String(route.query.account || "").trim();
  if (q) search.value = q;
  if (status) statusFilter.value = status;
  if (account) {
    selected.value = accounts.value.find((item) => item.id === account || item.account_name === account) || accounts.value[0] || null;
  } else {
    selected.value = accounts.value.find((item) => item.id === selectedId.value) || accounts.value[0] || null;
  }
}

async function copyAccountId() {
  if (!selectedId.value) return;
  const ok = await copyText(selectedId.value);
  showToast(ok ? "已复制 account_id" : "复制失败", ok ? "success" : "error");
}

function goPlans() {
  if (!selected.value) return;
  router.push({ path: "/plans", query: { q: selected.value.account_name || "" } });
}

loadAccounts();
</script>
