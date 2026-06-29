<template>
  <div class="page">
    <div class="page-header">
      <h1>{{ PAGE_TEXTS.home.title }}</h1>
      <div class="muted">{{ PAGE_TEXTS.home.description }}</div>
      <div class="toolbar">
        <button class="secondary" @click="load" :disabled="loading">{{ BUTTON_TEXTS.refreshHome }}</button>
      </div>
    </div>

    <AppLoading v-if="loading" text="正在加载首页概览..." />

    <template v-else>
      <div class="metric-grid">
        <div class="metric-card" v-for="item in metrics" :key="item.label">
          <div class="detail-label">{{ item.label }}</div>
          <div class="metric-card__value">{{ item.value }}</div>
          <div class="muted">{{ item.desc }}</div>
        </div>
      </div>

      <div class="row">
        <AppSectionCard :title="PAGE_TEXTS.home.sections.quickActions">
          <div class="toolbar">
            <button
              v-for="action in homeQuickActions"
              :key="action.label"
              class="secondary"
              @click="$router.push(action.to)"
            >
              {{ action.label }}
            </button>
          </div>
          <AppDetailGrid :items="workspaceSummaryItems" />
        </AppSectionCard>

        <AppSectionCard :title="PAGE_TEXTS.home.sections.statusSummary">
          <div class="list">
            <AppEntityListItem
              v-for="item in homeStatusItems"
              :key="item.title"
              :title="item.title"
              :badge="item.badge"
              :lines="item.lines"
            />
          </div>
          <AppNextStep :step="homeNextStep" />
        </AppSectionCard>
      </div>

      <div class="row">
        <AppSectionCard :title="PAGE_TEXTS.home.sections.alerts">
          <div v-if="alerts.length" class="list">
            <AppEntityListItem
              v-for="alert in alerts"
              :key="alert.title"
              :title="alert.title"
              :badge="alert.level"
              :lines="getHomeAlertLines(alert)"
            >
              <template #actions>
                <button class="secondary" @click="$router.push(alert.to)">{{ BUTTON_TEXTS.handleNow }}</button>
              </template>
            </AppEntityListItem>
          </div>
          <AppEmpty v-else :config="PAGE_TEXTS.home.emptyStates.alerts" />
        </AppSectionCard>

        <AppSectionCard :title="PAGE_TEXTS.home.sections.recentPlans">
          <div v-if="recentPlans.length" class="list">
            <AppEntityListItem
              v-for="plan in recentPlans"
              :key="plan.id"
              :title="plan.account_name || '-'"
              :badge="statusLabel(plan.status)"
              :badge-class="['status-tag', plan.status]"
              :lines="getHomeRecentPlanLines(plan)"
            >
              <template #actions>
                <button class="secondary" @click="$router.push({ path: '/publish', query: { plan: plan.id } })">{{ BUTTON_TEXTS.viewPlan }}</button>
              </template>
            </AppEntityListItem>
          </div>
          <AppEmpty v-else :config="PAGE_TEXTS.home.emptyStates.recentPlans" />
        </AppSectionCard>
      </div>

      <div class="row">
        <AppSectionCard :title="PAGE_TEXTS.home.sections.failedTasks">
          <div v-if="failedTasks.length" class="list">
            <AppEntityListItem
              v-for="task in failedTasks"
              :key="task.id"
              :title="task.publish_plan_id"
              badge="已失败"
              :badge-class="['status-tag', 'failed']"
              :lines="getHomeFailedTaskLines(task)"
            >
              <template #actions>
                <button class="secondary" @click="$router.push({ path: '/records', query: { plan: task.publish_plan_id, taskStatus: 'failed' } })">{{ BUTTON_TEXTS.viewTask }}</button>
              </template>
            </AppEntityListItem>
          </div>
          <AppEmpty v-else :config="PAGE_TEXTS.home.emptyStates.failedTasks" />
        </AppSectionCard>

        <AppSectionCard :title="PAGE_TEXTS.home.sections.invalidAccounts">
          <div v-if="invalidAccounts.length" class="list">
            <AppEntityListItem
              v-for="account in invalidAccounts"
              :key="account.id"
              :title="account.account_name"
              badge="异常"
              :badge-class="['status-tag', 'invalid']"
              :lines="getHomeInvalidAccountLines(account)"
            >
              <template #actions>
                <button class="secondary" @click="$router.push({ path: '/accounts', query: { account: account.id, status: 'invalid' } })">{{ BUTTON_TEXTS.viewAccount }}</button>
              </template>
            </AppEntityListItem>
          </div>
          <AppEmpty v-else :config="PAGE_TEXTS.home.emptyStates.invalidAccounts" />
        </AppSectionCard>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { api } from '../api/client'
import { BUTTON_TEXTS } from '../constants/button-texts'
import { ERROR_MESSAGES } from '../constants/error-messages'
import { PAGE_TEXTS } from '../constants/page-texts'
import { useAsyncTask } from '../composables/useAsyncTask'
import AppDetailGrid from '../components/AppDetailGrid.vue'
import AppEntityListItem from '../components/AppEntityListItem.vue'
import AppLoading from '../components/AppLoading.vue'
import AppEmpty from '../components/AppEmpty.vue'
import AppNextStep from '../components/AppNextStep.vue'
import AppSectionCard from '../components/AppSectionCard.vue'
import { session } from '../stores/session'
import { showError } from '../state/ui'
import { getWorkspaceSummaryItems } from '../utils/detail-configs'
import { getHomeAlertLines, getHomeFailedTaskLines, getHomeInvalidAccountLines, getHomeRecentPlanLines } from '../utils/list-configs'
import { getHomeAlerts, getHomeMetrics, getHomeNextStep, getHomeQuickActions, getHomeStatusItems } from '../utils/view-configs'
import { roleLabel, statusLabel } from '../utils/display'

const { loading, run: runLoadTask } = useAsyncTask((error) => showError(error.message || ERROR_MESSAGES.homeLoadFailed))
const plans = ref([])
const tasks = ref([])
const accounts = ref([])
const assets = ref([])
const drafts = ref([])

const recentPlans = computed(() => [...plans.value].slice(0, 5))
const failedTasks = computed(() => tasks.value.filter((item) => item.status === 'failed').slice(0, 5))
const invalidAccounts = computed(() => accounts.value.filter((item) => item.status === 'invalid').slice(0, 5))
const pendingCount = computed(() => plans.value.filter((item) => item.status === 'pending_approval').length)
const failedCount = computed(() => tasks.value.filter((item) => item.status === 'failed').length)
const homeQuickActions = getHomeQuickActions()
const workspaceSummaryItems = computed(() =>
  getWorkspaceSummaryItems({
    activeWorkspaceId: session.activeWorkspaceId,
    roleLabel: roleLabel(session.actor?.role)
  })
)
const homeStatusItems = computed(() =>
  getHomeStatusItems({
    assetsCount: assets.value.length,
    draftsCount: drafts.value.length,
    plansCount: plans.value.length,
    pendingCount: pendingCount.value,
    failedCount: failedCount.value
  })
)
const homeNextStep = computed(() =>
  getHomeNextStep({
    assetsCount: assets.value.length,
    draftsCount: drafts.value.length,
    pendingCount: pendingCount.value,
    failedCount: failedCount.value
  })
)
const metrics = computed(() =>
  getHomeMetrics({
    assetsCount: assets.value.length,
    draftsCount: drafts.value.length,
    plansCount: plans.value.length,
    pendingCount: pendingCount.value,
    tasksCount: tasks.value.length,
    failedCount: failedCount.value,
    accountCount: accounts.value.length,
    invalidAccountCount: invalidAccounts.value.length
  })
)
const alerts = computed(() =>
  getHomeAlerts({
    failedTasks: failedTasks.value,
    invalidAccounts: invalidAccounts.value,
    pendingPlans: plans.value.filter((item) => item.status === 'pending_approval')
  })
)

async function load() {
  await runLoadTask(async () => {
    const [plansRes, tasksRes, accountsRes, assetsRes, draftsRes] = await Promise.all([
      api('/api/v1/publish-plans/mine'),
      api('/api/v1/tasks'),
      api('/api/v1/accounts'),
      api('/api/v1/assets'),
      api('/api/v1/drafts')
    ])
    plans.value = plansRes.data || []
    tasks.value = tasksRes.data || []
    accounts.value = accountsRes.data || []
    assets.value = assetsRes.data || []
    drafts.value = draftsRes.data || []
  })
}

load()
</script>
