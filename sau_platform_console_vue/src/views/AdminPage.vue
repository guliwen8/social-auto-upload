<template>
  <div class="page">
    <div class="page-header">
      <h1>管理中心</h1>
      <div class="muted">API Key、用户与工作区成员管理</div>
    </div>

    <EmptyState
      v-if="!canManage"
      title="无权限访问"
      description="当前角色不具备系统管理权限，请联系管理员。"
    />

    <div v-else class="row">
      <div class="card">
        <h2>API Key</h2>
        <ReadonlyNotice
          message="API Key 与成员管理属于系统级配置。请谨慎操作，尤其是轮换、吊销和授予高权限角色。"
        />
        <div class="row">
          <input v-model="apiKeyName" placeholder="新 key 名称" />
          <button @click="createApiKey" :disabled="loading">创建</button>
        </div>
        <div class="filter-bar">
          <input v-model="apiKeySearch" placeholder="搜索 key id / 名称 / 状态" />
          <select v-model="apiKeyStatus">
            <option value="">全部状态</option>
            <option value="active">启用</option>
            <option value="revoked">已吊销</option>
          </select>
          <span class="stats-line">共 {{ filteredApiKeys.length }} 条</span>
        </div>
        <LoadingBlock v-if="loadingApiKeys" text="正在加载 API Key..." />
        <DataTable v-else :columns="apiKeyColumns" :rows="displayApiKeys" :selected-key="selectedApiKeyId" empty-text="暂无 API Key" @select="onSelectApiKey" />
        <div v-if="selectedApiKey" class="detail-panel" style="margin-top: 12px">
          <div class="toolbar">
            <span class="status-tag" :class="selectedApiKey.status">{{ statusLabel(selectedApiKey.status) }}</span>
            <button class="secondary" @click="copyApiKeyId">复制 key_id</button>
            <button class="secondary" @click="rotateApiKey" :disabled="selectedApiKey.status !== 'active'">轮换</button>
            <button class="danger" @click="revokeApiKey" :disabled="selectedApiKey.status !== 'active'">吊销</button>
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">key_id</div>
              <div class="detail-value">{{ selectedApiKey.id }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">名称</div>
              <div class="detail-value">{{ selectedApiKey.name }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">状态</div>
              <div class="detail-value">{{ statusLabel(selectedApiKey.status) }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">创建时间</div>
              <div class="detail-value">{{ selectedApiKey.created_at || "-" }}</div>
            </div>
            <div v-if="selectedApiKey.key" class="detail-item full">
              <div class="detail-label">最新明文 Key</div>
              <div class="detail-value">{{ selectedApiKey.key }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>用户与成员</h2>
        <div class="stack">
          <div class="row">
            <input v-model="userEmail" placeholder="用户邮箱" />
            <input v-model="userDisplayName" placeholder="显示名" />
          </div>
          <button @click="createUser" :disabled="loading">创建用户</button>
          <div class="row">
            <select v-model="memberUserId">
              <option value="">选择用户</option>
              <option v-for="user in users" :key="user.id" :value="user.id">
                {{ user.display_name || user.email }} · {{ user.id }}
              </option>
            </select>
            <select v-model="memberRole">
              <option value="viewer">只读成员</option>
              <option value="editor">编辑者</option>
              <option value="admin">管理员</option>
              <option value="owner">负责人</option>
            </select>
          </div>
          <button class="secondary" @click="addMember" :disabled="loading">添加成员</button>
        </div>

        <div class="row" style="margin-top: 16px">
          <div>
            <div class="muted" style="margin-bottom: 8px">用户列表</div>
            <LoadingBlock v-if="loadingUsers" text="正在加载用户..." />
            <DataTable v-else :columns="userColumns" :rows="displayUsers" empty-text="暂无用户" @select="onSelectUser" />
          </div>
          <div>
            <div class="muted" style="margin-bottom: 8px">工作区成员</div>
            <LoadingBlock v-if="loadingMembers" text="正在加载成员..." />
            <DataTable v-else :columns="memberColumns" :rows="displayMembers" empty-text="暂无成员" />
          </div>
        </div>

        <div v-if="selectedUser" class="detail-panel" style="margin-top: 12px">
          <div class="toolbar">
            <button class="secondary" @click="copyUserId">复制 user_id</button>
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">user_id</div>
              <div class="detail-value">{{ selectedUser.id }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">邮箱</div>
              <div class="detail-value">{{ selectedUser.email }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">显示名</div>
              <div class="detail-value">{{ selectedUser.display_name || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">创建时间</div>
              <div class="detail-value">{{ selectedUser.created_at || "-" }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { api } from "../api/client";
import DataTable, { type DataTableColumn } from "../components/DataTable.vue";
import EmptyState from "../components/EmptyState.vue";
import LoadingBlock from "../components/LoadingBlock.vue";
import ReadonlyNotice from "../components/ReadonlyNotice.vue";
import { confirmAction, showToast } from "../state/ui";
import { canManageSystem, session } from "../state/session";
import { copyText } from "../utils/clipboard";
import { roleLabel, statusLabel } from "../utils/display";

const canManage = computed(() => canManageSystem(session.actor?.role));

const loading = ref(false);
const loadingApiKeys = ref(false);
const loadingUsers = ref(false);
const loadingMembers = ref(false);

const apiKeys = ref<any[]>([]);
const selectedApiKey = ref<any | null>(null);
const apiKeyName = ref("");
const apiKeySearch = ref("");
const apiKeyStatus = ref("");

const users = ref<any[]>([]);
const selectedUser = ref<any | null>(null);
const members = ref<any[]>([]);
const userEmail = ref("");
const userDisplayName = ref("");
const memberUserId = ref("");
const memberRole = ref("editor");

const apiKeyColumns: DataTableColumn[] = [
  { key: "id", label: "key_id", width: "220px" },
  { key: "name", label: "名称" },
  { key: "status", label: "状态", width: "100px" },
  { key: "created_at", label: "创建时间", width: "180px" },
];
const userColumns: DataTableColumn[] = [
  { key: "id", label: "user_id", width: "200px" },
  { key: "email", label: "邮箱" },
  { key: "display_name", label: "显示名", width: "160px" },
];
const memberColumns: DataTableColumn[] = [
  { key: "user_id", label: "user_id", width: "200px" },
  { key: "role", label: "角色", width: "100px" },
  { key: "created_at", label: "加入时间", width: "180px" },
];

const selectedApiKeyId = computed(() => selectedApiKey.value?.id || "");
const filteredApiKeys = computed(() => {
  const q = apiKeySearch.value.trim().toLowerCase();
  return apiKeys.value.filter((item) => {
    const matchStatus = !apiKeyStatus.value || item.status === apiKeyStatus.value;
    const matchKeyword =
      !q ||
      String(item.id || "").toLowerCase().includes(q) ||
      String(item.name || "").toLowerCase().includes(q) ||
      String(item.status || "").toLowerCase().includes(q);
    return matchStatus && matchKeyword;
  });
});
const displayApiKeys = computed(() =>
  filteredApiKeys.value.map((item) => ({
    _raw: item,
    ...item,
    status: statusLabel(item.status),
  }))
);
const displayUsers = computed(() =>
  users.value.map((item) => ({
    ...item,
    display_name: item.display_name || "-",
  }))
);
const displayMembers = computed(() =>
  members.value.map((item) => ({
    ...item,
    role: roleLabel(item.role),
  }))
);

function onSelectApiKey(row: Record<string, any>) {
  selectedApiKey.value = row._raw || row;
}

function onSelectUser(row: Record<string, any>) {
  selectedUser.value = row;
}

async function loadApiKeys() {
  if (!canManage.value) return;
  loadingApiKeys.value = true;
  try {
    const res = await api<any[]>("/api/v1/api-keys");
    apiKeys.value = res.data || [];
    selectedApiKey.value = apiKeys.value.find((item) => item.id === selectedApiKeyId.value) || apiKeys.value[0] || null;
  } finally {
    loadingApiKeys.value = false;
  }
}

async function loadUsersAndMembers() {
  if (!canManage.value) return;
  loadingUsers.value = true;
  loadingMembers.value = true;
  try {
    const [u, m] = await Promise.all([
      api<any[]>("/api/v1/users"),
      api<any[]>("/api/v1/workspace-members"),
    ]);
    users.value = u.data || [];
    members.value = m.data || [];
    selectedUser.value = users.value[0] || null;
  } finally {
    loadingUsers.value = false;
    loadingMembers.value = false;
  }
}

async function createApiKey() {
  loading.value = true;
  try {
    const res = await api<any>("/api/v1/api-keys", {
      method: "POST",
      body: JSON.stringify({ name: apiKeyName.value.trim() || "console-key" }),
    });
    selectedApiKey.value = res.data;
    apiKeyName.value = "";
    showToast("API Key 已创建", "success");
    await loadApiKeys();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

async function revokeApiKey() {
  if (!selectedApiKey.value?.id) return;
  const { confirmed } = await confirmAction({
    title: "吊销 API Key",
    message: "确认吊销当前 API Key 吗？吊销后将无法继续调用。",
    confirmText: "吊销",
    danger: true,
  });
  if (!confirmed) return;
  loading.value = true;
  try {
    await api(`/api/v1/api-keys/${selectedApiKey.value.id}/revoke`, { method: "POST", body: "{}" });
    showToast("API Key 已吊销", "success");
    await loadApiKeys();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

async function rotateApiKey() {
  if (!selectedApiKey.value?.id) return;
  const { confirmed } = await confirmAction({
    title: "轮换 API Key",
    message: "确认轮换当前 API Key 吗？系统会生成新的明文 Key。",
    confirmText: "轮换",
  });
  if (!confirmed) return;
  loading.value = true;
  try {
    const res = await api<any>(`/api/v1/api-keys/${selectedApiKey.value.id}/rotate`, { method: "POST", body: "{}" });
    selectedApiKey.value = res.data;
    showToast("API Key 已轮换", "success");
    await loadApiKeys();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

async function createUser() {
  loading.value = true;
  try {
    await api<any>("/api/v1/users", {
      method: "POST",
      body: JSON.stringify({
        email: userEmail.value.trim(),
        display_name: userDisplayName.value.trim() || userEmail.value.trim(),
      }),
    });
    userEmail.value = "";
    userDisplayName.value = "";
    showToast("用户已创建", "success");
    await loadUsersAndMembers();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

async function addMember() {
  if (!memberUserId.value) return;
  loading.value = true;
  try {
    await api<any>("/api/v1/workspace-members", {
      method: "POST",
      body: JSON.stringify({ user_id: memberUserId.value, role: memberRole.value }),
    });
    showToast("成员已添加", "success");
    await loadUsersAndMembers();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

async function copyApiKeyId() {
  if (!selectedApiKey.value?.id) return;
  const ok = await copyText(selectedApiKey.value.id);
  showToast(ok ? "已复制 key_id" : "复制失败", ok ? "success" : "error");
}

async function copyUserId() {
  if (!selectedUser.value?.id) return;
  const ok = await copyText(selectedUser.value.id);
  showToast(ok ? "已复制 user_id" : "复制失败", ok ? "success" : "error");
}

loadApiKeys();
loadUsersAndMembers();
</script>
