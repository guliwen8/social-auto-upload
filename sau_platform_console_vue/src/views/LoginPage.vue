<template>
  <div class="page">
    <div class="card">
      <div class="page-header">
        <h1>登录</h1>
        <div class="muted">登录后进入控制台</div>
      </div>
      <div class="row" style="margin-top: 12px">
        <div class="stack">
          <input v-model="email" placeholder="邮箱" />
          <input v-model="password" placeholder="密码（>=8）" type="password" />
          <div class="toolbar">
            <button @click="onLogin" :disabled="loading">登录</button>
            <button class="secondary" @click="onRegister" :disabled="loading">注册</button>
          </div>
          <LoadingBlock v-if="loading" text="正在处理登录请求..." />
        </div>
        <div class="stack">
          <div v-if="resultMode" class="detail-panel">
            <div class="toolbar">
              <span class="pill">{{ resultMode === 'login' ? '登录结果' : '注册结果' }}</span>
            </div>
            <div class="detail-grid">
              <div class="detail-item">
                <div class="detail-label">邮箱</div>
                <div class="detail-value">{{ resultData.email || email || "-" }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">显示名</div>
                <div class="detail-value">{{ resultData.display_name || "-" }}</div>
              </div>
              <div class="detail-item" v-if="resultMode === 'login'">
                <div class="detail-label">工作区</div>
                <div class="detail-value">{{ resultData.workspace_id || "-" }}</div>
              </div>
              <div class="detail-item" v-if="resultMode === 'login'">
                <div class="detail-label">过期时间</div>
                <div class="detail-value">{{ resultData.expires_at || "-" }}</div>
              </div>
              <div class="detail-item" v-if="resultMode === 'register'">
                <div class="detail-label">user_id</div>
                <div class="detail-value">{{ resultData.id || "-" }}</div>
              </div>
              <div class="detail-item" v-if="resultMode === 'register'">
                <div class="detail-label">状态</div>
                <div class="detail-value">注册成功，请继续登录</div>
              </div>
            </div>
          </div>
          <EmptyState v-else title="等待操作" description="登录或注册成功后，这里会展示结构化结果。" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { setToken } from "../api/client";
import { refreshSession } from "../state/session";
import EmptyState from "../components/EmptyState.vue";
import LoadingBlock from "../components/LoadingBlock.vue";
import { showToast } from "../state/ui";

const router = useRouter();
const email = ref("");
const password = ref("");
const loading = ref(false);
const resultMode = ref<"" | "login" | "register">("");
const resultData = reactive<any>({});

async function postJson(path: string, body: any) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok || data.code !== 200) throw new Error(data.msg || "request failed");
  return data;
}

async function onLogin() {
  loading.value = true;
  try {
    const res = await postJson("/api/v1/auth/login", { email: email.value.trim(), password: password.value.trim() });
    setToken(res.data.token);
    await refreshSession();
    resultMode.value = "login";
    Object.assign(resultData, res.data || {});
    showToast("登录成功", "success");
    await router.push("/");
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}

async function onRegister() {
  loading.value = true;
  try {
    const res = await postJson("/api/v1/auth/register", { email: email.value.trim(), password: password.value.trim(), display_name: email.value.trim() });
    resultMode.value = "register";
    Object.assign(resultData, res.data || {});
    showToast("注册成功，请登录", "success");
  } catch (e: any) {
    showToast(String(e.message || e), "error");
  } finally {
    loading.value = false;
  }
}
</script>
