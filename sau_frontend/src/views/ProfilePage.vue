<template>
  <div class="page">
    <div class="page-header">
      <h1>{{ PAGE_TEXTS.profile.title }}</h1>
      <div class="muted">{{ PAGE_TEXTS.profile.description }}</div>
    </div>

    <div class="row">
      <AppSectionCard title="当前身份">
        <AppDetailGrid :items="identityItems" />
      </AppSectionCard>

      <AppSectionCard title="可访问工作区">
        <div v-if="session.workspaces.length" class="list">
          <AppEntityListItem
            v-for="workspace in session.workspaces"
            :key="workspace.id"
            :title="workspace.name"
            :badge="workspace.id === session.activeWorkspaceId ? '当前使用' : '可切换'"
            :lines="[`工作区编号：${workspace.id}`]"
          />
        </div>
        <AppEmpty v-else :config="PAGE_TEXTS.profile.emptyStates.workspaces" />
      </AppSectionCard>
    </div>

    <div class="row">
      <AppSectionCard title="当前能力">
        <div class="list">
          <AppEntityListItem
            v-for="item in profileAbilityItems"
            :key="item.title"
            :title="item.title"
            :badge="item.badge"
            :lines="item.lines"
          />
        </div>
      </AppSectionCard>

      <AppSectionCard title="快捷操作">
        <div class="toolbar">
          <button
            v-for="action in profileQuickActions"
            :key="action.label"
            class="secondary"
            @click="$router.push(action.to)"
          >
            {{ action.label }}
          </button>
        </div>
        <div class="muted">{{ PAGE_TEXTS.profile.workspaceHint }}</div>
      </AppSectionCard>
    </div>

    <AppSectionCard title="AI 配置概览">
      <AppLoading v-if="loading" text="正在加载 AI 配置..." />
      <AppDetailGrid v-else-if="settings.provider" :items="aiSettingItems" />
      <AppEmpty v-else :config="PAGE_TEXTS.profile.emptyStates.aiSettings" />
    </AppSectionCard>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { api } from '../api/client'
import { ERROR_MESSAGES } from '../constants/error-messages'
import { PAGE_TEXTS } from '../constants/page-texts'
import { useAsyncTask } from '../composables/useAsyncTask'
import { canEditContent, session } from '../stores/session'
import { showError } from '../state/ui'
import { getAiSettingItems, getProfileIdentityItems } from '../utils/detail-configs'
import { getProfileAbilityItems, getProfileQuickActions } from '../utils/view-configs'
import { roleLabel } from '../utils/display'
import AppDetailGrid from '../components/AppDetailGrid.vue'
import AppEntityListItem from '../components/AppEntityListItem.vue'
import AppLoading from '../components/AppLoading.vue'
import AppEmpty from '../components/AppEmpty.vue'
import AppSectionCard from '../components/AppSectionCard.vue'

const { loading, run: runLoadTask } = useAsyncTask((error) => showError(error.message || ERROR_MESSAGES.aiSettingsLoadFailed))
const canEdit = computed(() => canEditContent(session.actor?.role))
const profileQuickActions = getProfileQuickActions()
const profileAbilityItems = computed(() =>
  getProfileAbilityItems({ canEdit: canEdit.value, workspaceCount: session.workspaces.length })
)
const identityItems = computed(() =>
  getProfileIdentityItems({
    displayName: session.actor?.display_name,
    email: session.actor?.email,
    roleLabel: roleLabel(session.actor?.role),
    activeWorkspaceId: session.activeWorkspaceId
  })
)
const aiSettingItems = computed(() =>
  getAiSettingItems({
    provider: settings.provider,
    model: settings.model,
    baseUrl: settings.base_url
  })
)
const settings = reactive({
  provider: '',
  model: '',
  base_url: ''
})

async function loadSettings() {
  await runLoadTask(async () => {
    const res = await api('/api/v1/ai/settings')
    settings.provider = res.data?.provider || ''
    settings.model = res.data?.model || ''
    settings.base_url = res.data?.base_url || ''
  })
}

loadSettings()
</script>
