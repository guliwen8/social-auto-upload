<template>
  <div class="page">
    <div class="page-header">
      <h1>设置</h1>
      <div class="muted">AI 配置（用户级）</div>
    </div>

    <div class="card">
      <h2>AI 配置</h2>
      <div class="row">
        <input v-model="baseUrl" placeholder="Base URL（OpenAI 兼容）" />
        <input v-model="model" placeholder="Model（例如 gpt-4.1-mini）" />
      </div>
      <input v-model="apiKey" placeholder="API Key（保存后自动清空）" style="margin-top:10px;" />
      <div class="toolbar" style="margin-top:10px;">
        <button class="secondary" @click="load" :disabled="loading">读取</button>
        <button @click="save" :disabled="loading">保存</button>
      </div>
      <LoadingBlock v-if="loading && !config.provider" text="正在加载 AI 配置..." />
    </div>

    <div class="card">
      <h2>当前配置</h2>
      <div v-if="config.provider" class="detail-panel">
        <div class="toolbar">
          <span class="pill">{{ config.provider }}</span>
          <span class="pill">{{ config.model || "-" }}</span>
        </div>
        <div class="detail-grid">
          <div class="detail-item">
            <div class="detail-label">Provider</div>
            <div class="detail-value">{{ config.provider }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">Model</div>
            <div class="detail-value">{{ config.model || "-" }}</div>
          </div>
          <div class="detail-item full">
            <div class="detail-label">Base URL</div>
            <div class="detail-value">{{ config.base_url || "-" }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">API Key 状态</div>
            <div class="detail-value">{{ apiKeyConfigured ? "已配置" : "未配置" }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">最近加载模型</div>
            <div class="detail-value">{{ config.model || "gpt-4.1-mini" }}</div>
          </div>
        </div>
      </div>
      <EmptyState v-else title="尚未读取配置" description="点击上方“读取”后查看当前 AI 配置。" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { api } from "../api/client";
import EmptyState from "../components/EmptyState.vue";
import LoadingBlock from "../components/LoadingBlock.vue";
import { showToast } from "../state/ui";

const baseUrl = ref("");
const model = ref("gpt-4.1-mini");
const apiKey = ref("");
const loading = ref(false);
const config = reactive<any>({
  provider: "",
  base_url: "",
  model: "",
  api_key_masked: "",
});
const apiKeyConfigured = computed(() => Boolean(config.api_key_masked || apiKey.value.trim()));

async function load() {
  loading.value = true;
  try {
    const res = await api<any>("/api/v1/ai/settings");
    baseUrl.value = res.data?.base_url || "";
    model.value = res.data?.model || "gpt-4.1-mini";
    config.provider = res.data?.provider || "";
    config.base_url = res.data?.base_url || "";
    config.model = res.data?.model || "";
    config.api_key_masked = res.data?.api_key_masked || "";
  } finally {
    loading.value = false;
  }
}

async function save() {
  loading.value = true;
  try {
    const res = await api<any>("/api/v1/ai/settings", {
      method: "POST",
      body: JSON.stringify({
        provider: "openai_compat",
        base_url: baseUrl.value.trim(),
        api_key: apiKey.value.trim(),
        model: model.value.trim() || "gpt-4.1-mini",
      }),
    });
    apiKey.value = "";
    config.provider = res.data?.provider || "openai_compat";
    config.base_url = res.data?.base_url || baseUrl.value.trim();
    config.model = res.data?.model || model.value.trim();
    config.api_key_masked = res.data?.api_key_masked || "***";
    showToast("AI 配置已保存", "success");
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

load();
</script>
