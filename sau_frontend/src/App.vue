<template>
  <router-view v-if="route.path === '/login'" />
  <div v-else class="user-shell">
    <aside class="user-sidebar">
      <div class="brand">
        <div class="brand__title">自媒体工作台</div>
        <div class="brand__desc">内容准备到发布执行</div>
      </div>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-link" :class="{ active: route.path === item.path }">
          <span>{{ item.label }}</span>
          <span class="nav-link__desc">{{ item.desc }}</span>
        </RouterLink>
      </nav>
    </aside>

    <section class="user-main">
      <header class="user-topbar">
        <div>
          <div class="topbar__title">{{ currentNav?.label || '用户端' }}</div>
          <div class="topbar__desc">{{ currentNav?.desc || '按平台模型管理你的内容与发布流程' }}</div>
        </div>
        <div class="topbar__meta">
          <select v-model="selectedWorkspace" @change="onSwitchWorkspace">
            <option v-if="!session.workspaces.length" value="" disabled>暂无可切换工作区</option>
            <option v-for="workspace in session.workspaces" :key="workspace.id" :value="workspace.id">
              {{ workspace.name }}
            </option>
          </select>
          <div class="pill">{{ actorLabel }}</div>
          <button class="secondary" @click="onLogout">退出登录</button>
        </div>
      </header>

      <main class="user-page">
        <AppNextStep
          v-if="session.actor && !session.workspaces.length"
          title="当前没有可用工作区"
          description="你已经登录成功，但当前账号还没有可访问的工作区。建议先联系管理员分配工作区，再继续使用用户端。"
          action-label="查看个人中心"
          :action-to="'/profile'"
        />
        <router-view />
      </main>
    </section>
  </div>
  <ToastHost />
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { session, refreshSession, logout, switchWorkspace } from './stores/session'
import AppNextStep from './components/AppNextStep.vue'
import ToastHost from './components/ToastHost.vue'
import { SUCCESS_MESSAGES } from './constants/messages'
import { showError, showSuccess } from './state/ui'
import { roleLabel } from './utils/display'

const route = useRoute()
const router = useRouter()
const selectedWorkspace = ref('')

const navItems = [
  { path: '/', label: '首页', desc: '全局概览' },
  { path: '/content', label: '内容准备', desc: '素材与草稿' },
  { path: '/publish', label: '发布中心', desc: '计划与审批' },
  { path: '/records', label: '执行记录', desc: '任务与结果' },
  { path: '/accounts', label: '账号管理', desc: '账号与健康' },
  { path: '/profile', label: '个人中心', desc: '工作区与设置' }
]

const currentNav = computed(() => navItems.find((item) => item.path === route.path))
const actorLabel = computed(() => {
  if (!session.actor) return '未登录'
  return `${session.actor.display_name || session.actor.email || session.actor.user_id}（${roleLabel(session.actor.role)}）`
})

onMounted(async () => {
  if (route.path === '/login') return
  try {
    await refreshSession()
    selectedWorkspace.value = session.activeWorkspaceId
  } catch (error) {
    showError(error.message || '会话加载失败')
    await router.push('/login')
  }
})

watch(
  () => route.path,
  async (path) => {
    if (path === '/login' || session.actor) return
    try {
      await refreshSession()
      selectedWorkspace.value = session.activeWorkspaceId
    } catch (error) {
      showError(error.message || '会话加载失败')
      await router.push('/login')
    }
  }
)

async function onLogout() {
  await logout()
  showSuccess(SUCCESS_MESSAGES.logout)
  await router.push('/login')
}

async function onSwitchWorkspace() {
  if (!selectedWorkspace.value || !session.workspaces.length) return
  await switchWorkspace(selectedWorkspace.value)
  showSuccess(SUCCESS_MESSAGES.switchWorkspace)
}
</script>
