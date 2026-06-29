<template>
  <div class="page">
    <div class="page-header">
      <h1>素材与草稿</h1>
      <div class="muted">素材库、草稿库</div>
    </div>

    <ReadonlyNotice
      v-if="!canEdit"
      message="当前角色只能查看素材和草稿，不能创建新的素材或草稿。"
    />

    <div class="card">
      <div class="toolbar">
        <button class="secondary" @click="loadAll" :disabled="loading">刷新</button>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h2>创建素材</h2>
        <div class="row">
          <select v-model="assetType">
            <option value="video">video</option>
            <option value="image">image</option>
          </select>
          <input v-model="assetPath" placeholder="素材路径" />
        </div>
        <div class="toolbar" style="margin-top:10px;">
        <button @click="createAsset" :disabled="loading || !canEdit">创建</button>
        </div>
        <div v-if="createdAsset" class="detail-panel" style="margin-top: 12px">
          <div class="toolbar">
            <span class="pill">{{ createdAsset.asset_type }}</span>
            <button class="secondary" @click="selectedAsset = createdAsset">定位到详情</button>
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">asset_id</div>
              <div class="detail-value">{{ createdAsset.id }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">路径</div>
              <div class="detail-value">{{ createdAsset.path || "-" }}</div>
            </div>
          </div>
        </div>
        <EmptyState v-else title="尚未创建素材" description="创建成功后，这里会显示新素材摘要。" />
      </div>
      <div class="card">
        <h2>创建草稿</h2>
        <input v-model="draftTitle" placeholder="标题" />
        <textarea v-model="draftDesc" placeholder="描述" style="margin-top:10px;"></textarea>
        <input v-model="draftTags" placeholder="tags（逗号分隔）" style="margin-top:10px;" />
        <input v-model="draftAssetIds" placeholder="asset_ids（逗号分隔）" style="margin-top:10px;" />
        <div class="toolbar" style="margin-top:10px;">
          <button @click="createDraft" :disabled="loading || !canEdit">创建</button>
        </div>
        <div v-if="createdDraft" class="detail-panel" style="margin-top: 12px">
          <div class="toolbar">
            <span class="status-tag" :class="createdDraft.status">{{ statusLabel(createdDraft.status) }}</span>
            <button class="secondary" @click="selectedDraft = createdDraft">定位到详情</button>
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">draft_id</div>
              <div class="detail-value">{{ createdDraft.id }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">标题</div>
              <div class="detail-value">{{ createdDraft.title || "-" }}</div>
            </div>
            <div class="detail-item full">
              <div class="detail-label">素材 IDs</div>
              <div class="detail-value">{{ (createdDraft.asset_ids || []).join(", ") || "-" }}</div>
            </div>
          </div>
        </div>
        <EmptyState v-else title="尚未创建草稿" description="创建成功后，这里会显示新草稿摘要。" />
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h2>素材列表</h2>
        <LoadingBlock v-if="loadingList" text="正在加载素材..." />
        <DataTable v-else :columns="assetColumns" :rows="assets" :selected-key="selectedAssetId" empty-text="暂无素材" @select="onSelectAsset" />
      </div>
      <div class="card">
        <h2>草稿列表</h2>
        <LoadingBlock v-if="loadingList" text="正在加载草稿..." />
        <DataTable v-else :columns="draftColumns" :rows="drafts" :selected-key="selectedDraftId" empty-text="暂无草稿" @select="onSelectDraft" />
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h2>素材详情</h2>
        <div v-if="selectedAsset" class="detail-panel">
          <div class="toolbar">
            <span class="pill">{{ selectedAsset.asset_type }}</span>
          </div>
          <div class="toolbar">
            <button class="secondary" @click="copyAssetId">复制 asset_id</button>
            <button class="secondary" @click="goPlansByAsset">查看相关计划</button>
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">asset_id</div>
              <div class="detail-value">{{ selectedAsset.id }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">类型</div>
              <div class="detail-value">{{ selectedAsset.asset_type }}</div>
            </div>
            <div class="detail-item full">
              <div class="detail-label">路径</div>
              <div class="detail-value">{{ selectedAsset.path || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">SHA256</div>
              <div class="detail-value">{{ selectedAsset.sha256 || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">创建时间</div>
              <div class="detail-value">{{ selectedAsset.created_at || "-" }}</div>
            </div>
          </div>
        </div>
        <EmptyState v-else title="请选择素材" description="点击素材列表查看详情。" />
      </div>
      <div class="card">
        <h2>草稿详情</h2>
        <div v-if="selectedDraft" class="detail-panel">
          <div class="toolbar">
            <span class="status-tag" :class="selectedDraft.status">{{ statusLabel(selectedDraft.status) }}</span>
          </div>
          <div class="toolbar">
            <button class="secondary" @click="copyDraftId">复制 draft_id</button>
            <button class="secondary" @click="goPlansByDraft">查看相关计划</button>
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">draft_id</div>
              <div class="detail-value">{{ selectedDraft.id }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">标题</div>
              <div class="detail-value">{{ selectedDraft.title || "-" }}</div>
            </div>
            <div class="detail-item full">
              <div class="detail-label">描述</div>
              <div class="detail-value">{{ selectedDraft.description || "-" }}</div>
            </div>
            <div class="detail-item full">
              <div class="detail-label">标签</div>
              <div class="detail-value">{{ (selectedDraft.tags || []).join(", ") || "-" }}</div>
            </div>
            <div class="detail-item full">
              <div class="detail-label">素材 IDs</div>
              <div class="detail-value">{{ (selectedDraft.asset_ids || []).join(", ") || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">创建时间</div>
              <div class="detail-value">{{ selectedDraft.created_at || "-" }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">更新时间</div>
              <div class="detail-value">{{ selectedDraft.updated_at || "-" }}</div>
            </div>
          </div>
        </div>
        <EmptyState v-else title="请选择草稿" description="点击草稿列表查看详情。" />
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
import { showToast } from "../state/ui";
import { copyText } from "../utils/clipboard";
import { canEditContent, session } from "../state/session";
import { statusLabel } from "../utils/display";

const route = useRoute();
const router = useRouter();

const assets = ref<any[]>([]);
const drafts = ref<any[]>([]);
const selectedAsset = ref<any | null>(null);
const selectedDraft = ref<any | null>(null);
const loading = ref(false);
const loadingList = ref(false);

const assetType = ref<"video" | "image">("video");
const assetPath = ref("");
const createdAsset = ref<any | null>(null);

const draftTitle = ref("");
const draftDesc = ref("");
const draftTags = ref("");
const draftAssetIds = ref("");
const createdDraft = ref<any | null>(null);

const selectedAssetId = computed(() => selectedAsset.value?.id || "");
const selectedDraftId = computed(() => selectedDraft.value?.id || "");
const canEdit = computed(() => canEditContent(session.actor?.role));
const assetColumns: DataTableColumn[] = [
  { key: "id", label: "asset_id", width: "240px" },
  { key: "asset_type", label: "类型", width: "100px" },
  { key: "path", label: "路径" },
  { key: "created_at", label: "创建时间", width: "180px" },
];
const draftColumns: DataTableColumn[] = [
  { key: "id", label: "draft_id", width: "240px" },
  { key: "title", label: "标题" },
  { key: "status", label: "状态", width: "100px" },
  { key: "updated_at", label: "更新时间", width: "180px" },
];

function parseList(raw: string) {
  return raw.split(",").map((s) => s.trim()).filter(Boolean);
}

async function loadAll() {
  loadingList.value = true;
  try {
    const [a, d] = await Promise.all([api<any[]>("/api/v1/assets"), api<any[]>("/api/v1/drafts")]);
    assets.value = a.data || [];
    drafts.value = d.data || [];
    applyRouteQuery();
  } finally {
    loadingList.value = false;
  }
}

function onSelectAsset(item: any) {
  selectedAsset.value = item;
}

function onSelectDraft(item: any) {
  selectedDraft.value = item;
}

async function createAsset() {
  loading.value = true;
  try {
    const res = await api("/api/v1/assets", { method: "POST", body: JSON.stringify({ asset_type: assetType.value, path: assetPath.value.trim() }) });
    createdAsset.value = res.data;
    showToast("素材已创建", "success");
    await loadAll();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

async function createDraft() {
  loading.value = true;
  try {
    const res = await api("/api/v1/drafts", {
      method: "POST",
      body: JSON.stringify({
        title: draftTitle.value.trim(),
        description: draftDesc.value.trim(),
        tags: parseList(draftTags.value),
        asset_ids: parseList(draftAssetIds.value),
      }),
    });
    createdDraft.value = res.data;
    showToast("草稿已创建", "success");
    await loadAll();
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

function applyRouteQuery() {
  const asset = String(route.query.asset || "").trim();
  const draft = String(route.query.draft || "").trim();
  selectedAsset.value = assets.value.find((item) => item.id === asset) || assets.value[0] || null;
  selectedDraft.value = drafts.value.find((item) => item.id === draft) || drafts.value[0] || null;
}

async function copyAssetId() {
  if (!selectedAsset.value?.id) return;
  const ok = await copyText(selectedAsset.value.id);
  showToast(ok ? "已复制 asset_id" : "复制失败", ok ? "success" : "error");
}

async function copyDraftId() {
  if (!selectedDraft.value?.id) return;
  const ok = await copyText(selectedDraft.value.id);
  showToast(ok ? "已复制 draft_id" : "复制失败", ok ? "success" : "error");
}

function goPlansByDraft() {
  if (!selectedDraft.value?.id) return;
  router.push({ path: "/plans", query: { q: selectedDraft.value.id, draft: selectedDraft.value.id } });
}

function goPlansByAsset() {
  if (!selectedAsset.value?.id) return;
  router.push({ path: "/plans", query: { q: selectedAsset.value.id } });
}

loadAll();
</script>
