<template>
  <div class="page">
    <div class="page-header">
      <h1>{{ PAGE_TEXTS.records.title }}</h1>
      <div class="muted">{{ PAGE_TEXTS.records.description }}</div>
    </div>

    <div class="row">
      <div class="card">
        <h2>{{ PAGE_TEXTS.records.sections.taskList }}</h2>
        <AppListToolbar :config="PAGE_TEXTS.records.toolbars.tasks" :loading="loading" @refresh="load">
          <AppFilterFields :fields="taskToolbarFields" />
        </AppListToolbar>
        <AppLoading v-if="loading" text="正在加载任务记录..." />
        <div v-else-if="filteredTasks.length" class="list">
          <AppEntityListItem
            v-for="task in filteredTasks"
            :key="task.id"
            :title="task.publish_plan_id"
            :badge="statusLabel(task.status)"
            :badge-class="['status-tag', task.status]"
            :lines="getTaskListLines(task)"
          >
            <template #actions>
              <button class="secondary" @click="selectedTask = task">{{ BUTTON_TEXTS.viewDetail }}</button>
              <button class="secondary" @click="router.push({ path: '/publish', query: { plan: task.publish_plan_id } })">{{ BUTTON_TEXTS.viewPlan }}</button>
            </template>
          </AppEntityListItem>
        </div>
        <AppEmpty
          v-else
          :config="taskListEmptyState"
          @action="tasks.length ? clearTaskFilters() : null"
        />
      </div>

      <div class="card">
        <h2>{{ PAGE_TEXTS.records.sections.planStatus }}</h2>
        <AppListToolbar :config="PAGE_TEXTS.records.toolbars.plans" :loading="loading" @refresh="load">
          <AppFilterFields :fields="planToolbarFields" />
        </AppListToolbar>
        <AppLoading v-if="loading" text="正在加载计划状态..." />
        <div v-else-if="filteredPlans.length" class="list">
          <AppEntityListItem
            v-for="plan in filteredPlans"
            :key="plan.id"
            :title="plan.account_name"
            :badge="statusLabel(plan.status)"
            :badge-class="['status-tag', plan.status]"
            :lines="getRecordPlanListLines(plan)"
          >
            <template #actions>
              <button class="secondary" @click="selectedPlan = plan">{{ BUTTON_TEXTS.viewDetail }}</button>
            </template>
          </AppEntityListItem>
        </div>
        <AppEmpty
          v-else
          :config="planListEmptyState"
          @action="plans.length ? clearPlanFilters() : null"
        />
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h2>{{ PAGE_TEXTS.records.sections.taskDetail }}</h2>
        <AppDetailGrid v-if="selectedTask" :items="taskDetailItems" />
        <AppEmpty v-else :config="taskSelectionEmptyState" />
      </div>

      <div class="card">
        <h2>{{ PAGE_TEXTS.records.sections.planDetail }}</h2>
        <AppDetailGrid v-if="selectedPlan" :items="recordPlanDetailItems" />
        <AppEmpty v-else :config="planSelectionEmptyState" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { BUTTON_TEXTS } from '../constants/button-texts'
import { ERROR_MESSAGES } from '../constants/error-messages'
import { PAGE_TEXTS } from '../constants/page-texts'
import { useAsyncTask } from '../composables/useAsyncTask'
import { taskStatusOptions } from '../constants/options'
import AppDetailGrid from '../components/AppDetailGrid.vue'
import AppEntityListItem from '../components/AppEntityListItem.vue'
import AppFilterFields from '../components/AppFilterFields.vue'
import AppLoading from '../components/AppLoading.vue'
import AppEmpty from '../components/AppEmpty.vue'
import AppListToolbar from '../components/AppListToolbar.vue'
import { showError } from '../state/ui'
import { getRecordPlanDetailItems, getTaskDetailItems } from '../utils/detail-configs'
import { getFilterableEmptyStateFromConfig, getSelectionEmptyStateFromConfig } from '../utils/empty-configs'
import { createFilterSelectField, createToolbarFields } from '../utils/field-configs'
import { getRecordPlanListLines, getTaskListLines } from '../utils/list-configs'
import { assignSelection, clearRefValues } from '../utils/page-state'
import { matchesKeyword } from '../utils/collection'
import { statusLabel } from '../utils/display'

const route = useRoute()
const router = useRouter()
const { loading, run: runListTask } = useAsyncTask((error) => showError(error.message || ERROR_MESSAGES.recordsLoadFailed))
const tasks = ref([])
const plans = ref([])
const selectedTask = ref(null)
const selectedPlan = ref(null)
const taskKeyword = ref('')
const taskStatusFilter = ref('')
const planKeyword = ref('')
const taskToolbarFields = computed(() =>
  createToolbarFields({
    keywordKey: 'taskKeyword',
    keywordModel: taskKeyword,
    keywordPlaceholder: PAGE_TEXTS.records.toolbars.tasks.searchPlaceholder,
    selectFields: [createFilterSelectField('taskStatusFilter', taskStatusFilter, taskStatusOptions)]
  })
)
const planToolbarFields = computed(() =>
  createToolbarFields({
    keywordKey: 'planKeyword',
    keywordModel: planKeyword,
    keywordPlaceholder: PAGE_TEXTS.records.toolbars.plans.searchPlaceholder
  })
)
const taskDetailItems = computed(() => getTaskDetailItems(selectedTask.value, statusLabel))
const recordPlanDetailItems = computed(() => getRecordPlanDetailItems(selectedPlan.value, statusLabel))
const taskListEmptyState = computed(() => getFilterableEmptyStateFromConfig(PAGE_TEXTS.records.emptyStates.tasks, tasks.value.length))
const planListEmptyState = computed(() => getFilterableEmptyStateFromConfig(PAGE_TEXTS.records.emptyStates.plans, plans.value.length))
const taskSelectionEmptyState = getSelectionEmptyStateFromConfig(PAGE_TEXTS.records.emptyStates.taskSelection)
const planSelectionEmptyState = getSelectionEmptyStateFromConfig(PAGE_TEXTS.records.emptyStates.planSelection)
const filteredTasks = computed(() => {
  const taskStatus = route.query.taskStatus || taskStatusFilter.value
  const planId = route.query.plan
  return tasks.value.filter((item) => {
    const statusMatched = !taskStatus || item.status === taskStatus
    const planMatched = !planId || item.publish_plan_id === planId
    const keywordMatched = matchesKeyword(
      [item.id, item.publish_plan_id, item.last_error_type, item.last_error_message],
      taskKeyword.value
    )
    return statusMatched && planMatched && keywordMatched
  })
})
const filteredPlans = computed(() => {
  const planId = route.query.plan
  return plans.value.filter((item) => {
    const planMatched = !planId || item.id === planId
    const keywordMatched = matchesKeyword([item.id, item.account_name, item.content_type, item.platform], planKeyword.value)
    return planMatched && keywordMatched
  })
})

function applyRouteSelection() {
  if (route.query.plan) {
    assignSelection(selectedPlan, plans.value, route.query.plan, selectedPlan.value)
    assignSelection(selectedTask, tasks.value, route.query.plan, selectedTask.value, 'publish_plan_id')
  } else {
    assignSelection(selectedTask, filteredTasks.value, '', selectedTask.value)
    assignSelection(selectedPlan, filteredPlans.value, '', selectedPlan.value)
  }
}

async function load() {
  await runListTask(async () => {
    const [tasksRes, plansRes] = await Promise.all([
      api('/api/v1/tasks'),
      api('/api/v1/publish-plans/mine')
    ])
    tasks.value = tasksRes.data || []
    plans.value = plansRes.data || []
    applyRouteSelection()
  })
}

function clearTaskFilters() {
  clearRefValues(taskKeyword, taskStatusFilter)
}

function clearPlanFilters() {
  clearRefValues(planKeyword)
}

watch(() => [route.query.plan, route.query.taskStatus], applyRouteSelection)

load()
</script>
