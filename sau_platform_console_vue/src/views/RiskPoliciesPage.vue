<template>
  <div class="page">
    <div class="page-header">
      <h1>风控策略</h1>
      <div class="muted">平台级与账号级限流、熔断、冷却策略</div>
    </div>

    <EmptyState
      v-if="!canManage"
      title="无权限访问"
      description="当前角色不具备风控策略管理权限，请联系管理员。"
    />

    <template v-else>
      <div class="row">
        <div class="card">
          <h2>策略列表</h2>
          <div class="filter-bar">
            <input v-model="search" placeholder="搜索 scope_key / scope_type" />
            <select v-model="scopeTypeFilter">
              <option value="">全部类型</option>
              <option value="platform">平台级</option>
              <option value="account">账号级</option>
            </select>
            <span class="stats-line">共 {{ filteredPolicies.length }} 条</span>
          </div>
          <LoadingBlock v-if="loadingList" text="正在加载风控策略..." />
          <DataTable
            v-else
            :columns="columns"
            :rows="displayPolicies"
            :selected-key="selectedId"
            empty-text="暂无策略"
            @select="onSelect"
          />
        </div>

        <div class="card">
          <h2>新增 / 更新策略</h2>
          <ReadonlyNotice
            message="风控策略属于系统级配置。建议仅由管理员或负责人修改，并在改动后观察任务失败率与账号健康度。"
          />
          <div class="stack">
            <div class="row">
              <select v-model="scopeType">
                <option value="platform">平台级</option>
                <option value="account">账号级</option>
              </select>
              <input
                v-model="scopeKey"
                :placeholder="scopeType === 'platform' ? '例如 douyin' : '例如 douyin:my_account'"
              />
            </div>
            <div class="row">
              <input v-model.number="cooldownSeconds" type="number" placeholder="cooldown_seconds" />
              <input v-model.number="dailyLimit" type="number" placeholder="daily_limit" />
            </div>
            <div class="row">
              <input v-model.number="accountFailureThreshold" type="number" placeholder="account_failure_threshold" />
              <input v-model.number="platformFailureThreshold" type="number" placeholder="platform_failure_threshold" />
            </div>
            <div class="toolbar">
              <button @click="savePolicy" :disabled="loadingSave">保存策略</button>
              <button class="secondary" @click="fillFromSelected" :disabled="!selectedPolicy">载入选中</button>
              <button class="secondary" @click="resetForm">重置表单</button>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>策略详情</h2>
        <div v-if="selectedPolicy" class="detail-panel">
          <div class="toolbar">
            <span class="pill">{{ scopeTypeLabel(selectedPolicy.scope_type) }}</span>
            <button class="secondary" @click="copyPolicyId">复制 policy_id</button>
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">policy_id</div>
              <div class="detail-value">{{ selectedPolicy.id }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">scope_key</div>
            <div class="detail-value">{{ selectedPolicy.scope_key }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">更新时间</div>
              <div class="detail-value">{{ selectedPolicy.updated_at || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">冷却时间</div>
              <div class="detail-value">{{ selectedPolicy.policy?.cooldown_seconds ?? 0 }} 秒</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">每日上限</div>
              <div class="detail-value">{{ selectedPolicy.policy?.daily_limit ?? 0 }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">账号失败阈值</div>
              <div class="detail-value">{{ selectedPolicy.policy?.account_failure_threshold ?? 0 }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">平台失败阈值</div>
              <div class="detail-value">{{ selectedPolicy.policy?.platform_failure_threshold ?? 0 }}</div>
            </div>
          </div>
        </div>
        <EmptyState v-else title="请选择一条策略" description="点击左侧策略列表查看详情。" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { api } from "../api/client";
import DataTable, { type DataTableColumn } from "../components/DataTable.vue";
import EmptyState from "../components/EmptyState.vue";
import LoadingBlock from "../components/LoadingBlock.vue";
import ReadonlyNotice from "../components/ReadonlyNotice.vue";
import { showToast } from "../state/ui";
import { canManageSystem, session } from "../state/session";
import { copyText } from "../utils/clipboard";
import { scopeTypeLabel } from "../utils/display";

const canManage = computed(() => canManageSystem(session.actor?.role));

const loadingList = ref(false);
const loadingSave = ref(false);
const policies = ref<any[]>([]);
const selectedPolicy = ref<any | null>(null);
const search = ref("");
const scopeTypeFilter = ref("");

const scopeType = ref<"platform" | "account">("platform");
const scopeKey = ref("");
const cooldownSeconds = ref(300);
const dailyLimit = ref(10);
const accountFailureThreshold = ref(3);
const platformFailureThreshold = ref(5);

const selectedId = computed(() => selectedPolicy.value?.id || "");
const filteredPolicies = computed(() => {
  const q = search.value.trim().toLowerCase();
  return policies.value.filter((item) => {
    const matchType = !scopeTypeFilter.value || item.scope_type === scopeTypeFilter.value;
    const matchKeyword =
      !q ||
      String(item.scope_key || "").toLowerCase().includes(q) ||
      String(item.scope_type || "").toLowerCase().includes(q);
    return matchType && matchKeyword;
  });
});
const displayPolicies = computed(() =>
  filteredPolicies.value.map((item) => ({
    _raw: item,
    ...item,
    scope_type: scopeTypeLabel(item.scope_type),
  }))
);

const columns: DataTableColumn[] = [
  { key: "id", label: "policy_id", width: "220px" },
  { key: "scope_type", label: "类型", width: "100px" },
  { key: "scope_key", label: "scope_key" },
  { key: "updated_at", label: "更新时间", width: "180px" },
];

function onSelect(row: Record<string, any>) {
  selectedPolicy.value = row._raw || row;
}

async function loadPolicies() {
  if (!canManage.value) return;
  loadingList.value = true;
  try {
    const res = await api<any[]>("/api/v1/risk-policies");
    policies.value = res.data || [];
    selectedPolicy.value = policies.value.find((item) => item.id === selectedId.value) || policies.value[0] || null;
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loadingList.value = false;
  }
}

async function savePolicy() {
  if (!canManage.value) return;
  loadingSave.value = true;
  try {
    await api("/api/v1/risk-policies", {
      method: "POST",
      body: JSON.stringify({
        scope_type: scopeType.value,
        scope_key: scopeKey.value.trim(),
        policy: {
          cooldown_seconds: Number(cooldownSeconds.value) || 0,
          daily_limit: Number(dailyLimit.value) || 0,
          account_failure_threshold: Number(accountFailureThreshold.value) || 0,
          platform_failure_threshold: Number(platformFailureThreshold.value) || 0,
        },
      }),
    });
    showToast("风控策略已保存", "success");
    await loadPolicies();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loadingSave.value = false;
  }
}

function fillFromSelected() {
  if (!selectedPolicy.value) return;
  scopeType.value = selectedPolicy.value.scope_type;
  scopeKey.value = selectedPolicy.value.scope_key;
  cooldownSeconds.value = Number(selectedPolicy.value.policy?.cooldown_seconds || 0);
  dailyLimit.value = Number(selectedPolicy.value.policy?.daily_limit || 0);
  accountFailureThreshold.value = Number(selectedPolicy.value.policy?.account_failure_threshold || 0);
  platformFailureThreshold.value = Number(selectedPolicy.value.policy?.platform_failure_threshold || 0);
}

function resetForm() {
  scopeType.value = "platform";
  scopeKey.value = "";
  cooldownSeconds.value = 300;
  dailyLimit.value = 10;
  accountFailureThreshold.value = 3;
  platformFailureThreshold.value = 5;
}

async function copyPolicyId() {
  if (!selectedPolicy.value?.id) return;
  const ok = await copyText(selectedPolicy.value.id);
  showToast(ok ? "已复制 policy_id" : "复制失败", ok ? "success" : "error");
}

loadPolicies();
</script>
