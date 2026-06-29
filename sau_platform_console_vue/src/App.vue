<template>
  <div v-if="!authed" class="page">
    <RouterView />
    <ToastHost />
    <ConfirmDialog />
  </div>
  <div v-else class="app">
    <aside class="sidebar">
      <div class="brand">
        SAU Platform
        <small>Vue 控制台</small>
      </div>
      <nav class="nav">
        <RouterLink to="/" class="link" :class="{ active: route.path === '/' }">
          <span>仪表盘</span><span class="desc">全局总览</span>
        </RouterLink>
        <RouterLink to="/approvals" class="link" :class="{ active: route.path === '/approvals' }">
          <span>审批中心</span><span class="desc">待审与记录</span>
        </RouterLink>
        <RouterLink to="/plans" class="link" :class="{ active: route.path === '/plans' }">
          <span>发布计划</span><span class="desc">创建与审批</span>
        </RouterLink>
        <RouterLink to="/tasks" class="link" :class="{ active: route.path === '/tasks' }">
          <span>任务中心</span><span class="desc">执行与记录</span>
        </RouterLink>
        <RouterLink to="/accounts" class="link" :class="{ active: route.path === '/accounts' }">
          <span>账号中心</span><span class="desc">注册与健康</span>
        </RouterLink>
        <RouterLink to="/content" class="link" :class="{ active: route.path === '/content' }">
          <span>素材草稿</span><span class="desc">内容资产</span>
        </RouterLink>
        <RouterLink v-if="canManage" to="/risk-policies" class="link" :class="{ active: route.path === '/risk-policies' }">
          <span>风控策略</span><span class="desc">限流与熔断</span>
        </RouterLink>
        <RouterLink v-if="canManage" to="/admin" class="link" :class="{ active: route.path === '/admin' }">
          <span>管理中心</span><span class="desc">密钥与成员</span>
        </RouterLink>
        <RouterLink to="/settings" class="link" :class="{ active: route.path === '/settings' }">
          <span>设置</span><span class="desc">AI 配置</span>
        </RouterLink>
      </nav>
    </aside>

    <header class="topbar">
      <span class="pill">本地环境</span>
      <div class="toolbar">
        <select v-model="selectedWorkspace" style="width: 320px">
          <option v-for="ws in filteredWorkspaces" :key="ws.id" :value="ws.id">
            {{ ws.name }} · {{ ws.id }}
          </option>
        </select>
        <input v-model="workspaceQuery" placeholder="搜索工作区" style="width: 220px" />
        <button class="secondary" @click="onSwitchWorkspace" :disabled="!selectedWorkspace">切换</button>
      </div>
      <div class="spacer" />
      <span class="badge">{{ actorLabel }}</span>
      <button class="secondary" @click="onLogout">退出</button>
    </header>

    <main class="main">
      <RouterView />
    </main>
    <ToastHost />
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getToken } from "./api/client";
import { canManageSystem, refreshSession, session, logout, switchWorkspace } from "./state/session";
import { showToast } from "./state/ui";
import ToastHost from "./components/ToastHost.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import { roleLabel } from "./utils/display";

const route = useRoute();
const router = useRouter();

const authed = computed(() => Boolean(getToken()));
const canManage = computed(() => canManageSystem(session.actor?.role));
const workspaceQuery = ref("");
const selectedWorkspace = ref("");

const actorLabel = computed(() => {
  if (!session.actor) return "未登录";
  return `${session.actor.display_name || session.actor.email || session.actor.user_id}（${roleLabel(session.actor.role)}）`;
});

const filteredWorkspaces = computed(() => {
  const q = workspaceQuery.value.trim().toLowerCase();
  const list = [...(session.workspaces || [])].sort((a, b) => String(a.name).localeCompare(String(b.name)));
  if (!q) return list;
  return list.filter((w) => String(w.name).toLowerCase().includes(q) || String(w.id).toLowerCase().includes(q));
});

watch(
  () => session.actor?.workspace_id,
  (wsId) => {
    if (wsId) selectedWorkspace.value = wsId;
  },
  { immediate: true }
);

async function onLogout() {
  await logout();
  showToast("已退出登录", "success");
  await router.push("/login");
}

async function onSwitchWorkspace() {
  if (!selectedWorkspace.value) return;
  await switchWorkspace(selectedWorkspace.value);
  showToast("已切换工作区", "success");
}

onMounted(async () => {
  if (authed.value) {
    await refreshSession();
  } else if (route.path !== "/login") {
    await router.replace("/login");
  }
});
</script>

<style scoped>
.link { display: flex; justify-content: space-between; gap: 10px; }
</style>
