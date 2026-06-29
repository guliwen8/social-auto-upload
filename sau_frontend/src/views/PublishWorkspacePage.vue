<template>
  <div class="page">
    <div class="page-header">
      <h1>{{ PAGE_TEXTS.publish.title }}</h1>
      <div class="muted">{{ PAGE_TEXTS.publish.description }}</div>
    </div>

    <AppReadonlyNotice
      v-if="!canEdit"
      :message="PAGE_TEXTS.publish.readonlyMessage"
    />

    <div class="row">
      <AppFormCard :title="PAGE_TEXTS.publish.forms.createPlan.title" :hint="PAGE_TEXTS.publish.forms.createPlan.hint">
        <AppFormFields :model="publishForm" :fields="publishFormFields" />
        <button @click="createPlan" :disabled="loading || !canEdit">{{ BUTTON_TEXTS.createPlan }}</button>
        <template #result>
          <AppDetailGrid v-if="createdPlan" :items="createdPlanItems" />
        </template>
        <div v-if="route.query.draft" class="muted">{{ PAGE_TEXTS.publish.forms.createPlan.routeDraftHintPrefix }}{{ route.query.draft }}</div>
      </AppFormCard>

      <div class="card">
        <h2>{{ PAGE_TEXTS.publish.sections.myPlans }}</h2>
        <AppListToolbar :config="PAGE_TEXTS.publish.toolbars.plans" :loading="loadingList" @refresh="load">
          <AppFilterFields :fields="planToolbarFields" />
        </AppListToolbar>
        <AppLoading v-if="loadingList" text="正在加载发布计划..." />
        <div v-else-if="filteredPlans.length" class="list">
          <AppEntityListItem
            v-for="plan in filteredPlans"
            :key="plan.id"
            :title="plan.account_name"
            :badge="statusLabel(plan.status)"
            :badge-class="['status-tag', plan.status]"
            :lines="getPublishPlanListLines(plan)"
          >
            <template #actions>
              <button class="secondary" @click="selectedPlan = plan">{{ BUTTON_TEXTS.viewDetail }}</button>
              <button class="secondary" @click="submitPlan(plan.id)" :disabled="plan.status !== 'draft' || !canEdit">{{ BUTTON_TEXTS.submitApproval }}</button>
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
        <h2>{{ PAGE_TEXTS.publish.sections.planDetail }}</h2>
        <AppDetailGrid v-if="selectedPlan" :items="planDetailItems" />
        <div v-if="selectedPlan" class="toolbar">
          <button class="secondary" @click="$router.push({ path: '/records', query: { plan: selectedPlan.id } })">{{ BUTTON_TEXTS.viewExecutionRecords }}</button>
          <button class="secondary" @click="$router.push({ path: '/content', query: { draft: selectedPlan.draft_id || '' } })">{{ BUTTON_TEXTS.viewDraft }}</button>
        </div>
        <AppNextStep v-if="selectedPlan" :step="planNextStep" />
        <AppEmpty v-else :config="planSelectionEmptyState" />
      </div>

      <div class="card">
        <h2>{{ PAGE_TEXTS.publish.sections.pendingPlans }}</h2>
        <div v-if="draftPlans.length" class="list">
          <AppEntityListItem
            v-for="plan in draftPlans.slice(0, 5)"
            :key="plan.id"
            :title="plan.account_name"
            :badge="statusLabel(plan.status)"
            :badge-class="['status-tag', plan.status]"
            :lines="getDraftPlanListLines(plan)"
          >
            <template #actions>
              <button class="secondary" @click="selectedPlan = plan">{{ BUTTON_TEXTS.viewDetail }}</button>
            </template>
          </AppEntityListItem>
        </div>
        <AppEmpty v-else :config="draftPlanEmptyState" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import { BUTTON_TEXTS } from '../constants/button-texts'
import { ERROR_MESSAGES } from '../constants/error-messages'
import { PAGE_TEXTS } from '../constants/page-texts'
import { SUCCESS_MESSAGES } from '../constants/messages'
import { useAsyncTask } from '../composables/useAsyncTask'
import { booleanChoiceOptions, publishContentTypeOptions, publishStatusOptions, publishStrategyOptions, youtubeVisibilityOptions } from '../constants/options'
import AppDetailGrid from '../components/AppDetailGrid.vue'
import AppEntityListItem from '../components/AppEntityListItem.vue'
import AppFilterFields from '../components/AppFilterFields.vue'
import AppLoading from '../components/AppLoading.vue'
import AppEmpty from '../components/AppEmpty.vue'
import AppFormCard from '../components/AppFormCard.vue'
import AppFormFields from '../components/AppFormFields.vue'
import AppListToolbar from '../components/AppListToolbar.vue'
import AppNextStep from '../components/AppNextStep.vue'
import AppReadonlyNotice from '../components/AppReadonlyNotice.vue'
import { canEditContent, session } from '../stores/session'
import { showError, showSuccess, showWarning } from '../state/ui'
import { getCreatedPlanItems, getPublishPlanDetailItems } from '../utils/detail-configs'
import { createFilterSelectField, createInputField, createSelectField, createToolbarFields, prependPlaceholderOption } from '../utils/field-configs'
import { requirePattern, requirePresent, requireText } from '../utils/form-validation'
import { getFilterableEmptyStateFromConfig, getSelectionEmptyStateFromConfig } from '../utils/empty-configs'
import { getDraftPlanListLines, getPublishPlanListLines } from '../utils/list-configs'
import { finishMutation } from '../utils/mutation-helpers'
import { assignSelection, clearRefValues } from '../utils/page-state'
import { matchesKeyword } from '../utils/collection'
import { getPublishPlanNextStep } from '../utils/view-configs'
import { statusLabel } from '../utils/display'

const route = useRoute()
const { loading, run: runSubmitTask } = useAsyncTask((error) => showError(error.message || ERROR_MESSAGES.actionFailed))
const { loading: loadingList, run: runListTask } = useAsyncTask((error) => showError(error.message || ERROR_MESSAGES.publishLoadFailed))
const accounts = ref([])
const drafts = ref([])
const plans = ref([])
const createdPlan = ref(null)
const selectedPlan = ref(null)
const publishForm = reactive({
  accountId: '',
  draftId: '',
  contentType: 'video',
  scheduledFor: '',
  publishStrategy: 'immediate',
  isDraft: 'false',
  shortTitle: '',
  category: '',
  thumbnailFile: '',
  thumbnailLandscapeFile: '',
  thumbnailPortraitFile: '',
  youtubeVisibility: 'public',
  youtubePlaylist: '',
  youtubeThumbnailFile: ''
})
const planKeyword = ref('')
const statusFilter = ref('')
const canEdit = computed(() => canEditContent(session.actor?.role))
const selectedAccount = computed(() => accounts.value.find((item) => item.id === publishForm.accountId) || null)
const selectedPlatform = computed(() => selectedAccount.value?.platform || '')
const supportsNotePlatforms = new Set(['douyin', 'kuaishou', 'xiaohongshu'])
const availableContentTypeOptions = computed(() =>
  supportsNotePlatforms.has(selectedPlatform.value) || !selectedPlatform.value
    ? publishContentTypeOptions
    : publishContentTypeOptions.filter((item) => item.value === 'video')
)
const isTencentPlatform = computed(() => selectedPlatform.value === 'tencent')
const isYouTubePlatform = computed(() => selectedPlatform.value === 'youtube')
const publishFormFields = computed(() => {
  const fields = [
    createSelectField('accountId', prependPlaceholderOption(PAGE_TEXTS.publish.forms.createPlan.fields.accountPlaceholder, accounts.value.map((item) => ({ value: item.id, label: `${item.account_name} / ${item.platform}` })))),
    createSelectField('draftId', prependPlaceholderOption(PAGE_TEXTS.publish.forms.createPlan.fields.draftPlaceholder, drafts.value.map((item) => ({ value: item.id, label: item.title }))),
    ),
    createSelectField('contentType', availableContentTypeOptions.value),
  ]

  if (isTencentPlatform.value && publishForm.contentType === 'video') {
    fields.push(
      createSelectField('publishStrategy', publishStrategyOptions),
      createSelectField('isDraft', booleanChoiceOptions),
      createInputField('shortTitle', '短标题，可选，建议 6 到 16 个字符'),
      createInputField('category', '原创分类，可选'),
      createInputField('thumbnailFile', '封面路径，可选'),
      createInputField('thumbnailLandscapeFile', '横版封面路径，可选'),
      createInputField('thumbnailPortraitFile', '竖版封面路径，可选')
    )
  }

  if (isYouTubePlatform.value && publishForm.contentType === 'video') {
    fields.push(
      createSelectField('youtubeVisibility', youtubeVisibilityOptions),
      createInputField('youtubePlaylist', '播放列表名称，可选'),
      createInputField('youtubeThumbnailFile', '缩略图路径，可选')
    )
  }

  fields.push(createInputField('scheduledFor', PAGE_TEXTS.publish.forms.createPlan.fields.scheduledFor))
  return fields
})
const planToolbarFields = computed(() =>
  createToolbarFields({
    keywordKey: 'planKeyword',
    keywordModel: planKeyword,
    keywordPlaceholder: PAGE_TEXTS.publish.toolbars.plans.searchPlaceholder,
    selectFields: [createFilterSelectField('statusFilter', statusFilter, publishStatusOptions)]
  })
)
const draftPlans = computed(() => plans.value.filter((item) => item.status === 'draft'))
const createdPlanItems = computed(() => getCreatedPlanItems(createdPlan.value, statusLabel))
const planDetailItems = computed(() => getPublishPlanDetailItems(selectedPlan.value, statusLabel))
const planNextStep = computed(() => getPublishPlanNextStep(selectedPlan.value))
const planListEmptyState = computed(() => getFilterableEmptyStateFromConfig(PAGE_TEXTS.publish.emptyStates.plans, plans.value.length))
const planSelectionEmptyState = getSelectionEmptyStateFromConfig(PAGE_TEXTS.publish.emptyStates.planSelection)
const draftPlanEmptyState = getSelectionEmptyStateFromConfig(PAGE_TEXTS.publish.emptyStates.draftPlans)
const filteredPlans = computed(() => {
  const status = route.query.status || statusFilter.value
  const planId = route.query.plan
  return plans.value.filter((item) => {
    const statusMatched = !status || item.status === status
    const planMatched = !planId || item.id === planId
    const keywordMatched = matchesKeyword([item.id, item.account_name, item.draft_id, item.platform], planKeyword.value)
    return statusMatched && planMatched && keywordMatched
  })
})

if (route.query.draft) {
  publishForm.draftId = String(route.query.draft)
}

function applyRouteSelection() {
  if (route.query.draft) publishForm.draftId = String(route.query.draft)
  assignSelection(selectedPlan, filteredPlans.value, route.query.plan, selectedPlan.value)
}

async function load() {
  await runListTask(async () => {
    const [accountsRes, draftsRes, plansRes] = await Promise.all([
      api('/api/v1/accounts'),
      api('/api/v1/drafts'),
      api('/api/v1/publish-plans/mine')
    ])
    accounts.value = accountsRes.data || []
    drafts.value = draftsRes.data || []
    plans.value = plansRes.data || []
    applyRouteSelection()
  })
}

async function createPlan() {
  if (!canEdit.value) return
  if (!requirePresent(publishForm.accountId, '请先选择发布账号', showWarning)) return
  if (!requirePresent(publishForm.draftId, '请先选择草稿', showWarning)) return
  if (
    publishForm.publishStrategy === 'scheduled' &&
    !requireText(publishForm.scheduledFor, '请填写计划时间', showWarning)
  ) return
  if (
    publishForm.scheduledFor &&
    !requirePattern(publishForm.scheduledFor, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/, '计划时间格式示例：2026-06-29T10:00:00+08:00', showWarning)
  ) return
  const account = accounts.value.find((item) => item.id === publishForm.accountId)
  await runSubmitTask(async () => {
    const payload = {}
    const scheduleAt = isTencentPlatform.value && publishForm.publishStrategy !== 'scheduled'
      ? null
      : (publishForm.scheduledFor || null)
    if (isTencentPlatform.value && publishForm.contentType === 'video') {
      payload.publish_strategy = publishForm.publishStrategy
      payload.is_draft = publishForm.isDraft === 'true'
      if (publishForm.shortTitle.trim()) payload.short_title = publishForm.shortTitle.trim()
      if (publishForm.category.trim()) payload.category = publishForm.category.trim()
      if (publishForm.thumbnailFile.trim()) payload.thumbnail_file = publishForm.thumbnailFile.trim()
      if (publishForm.thumbnailLandscapeFile.trim()) payload.thumbnail_landscape_file = publishForm.thumbnailLandscapeFile.trim()
      if (publishForm.thumbnailPortraitFile.trim()) payload.thumbnail_portrait_file = publishForm.thumbnailPortraitFile.trim()
    }
    if (isYouTubePlatform.value && publishForm.contentType === 'video') {
      payload.visibility = publishForm.youtubeVisibility
      if (publishForm.youtubePlaylist.trim()) payload.playlist = publishForm.youtubePlaylist.trim()
      if (publishForm.youtubeThumbnailFile.trim()) payload.thumbnail_file = publishForm.youtubeThumbnailFile.trim()
    }
    const res = await api('/api/v1/publish-plans', {
      method: 'POST',
      body: JSON.stringify({
        account_id: publishForm.accountId,
        account_name: account?.account_name || '',
        platform: account?.platform || 'douyin',
        draft_id: publishForm.draftId,
        content_type: publishForm.contentType,
        schedule_at: scheduleAt,
        payload
      })
    })
    await finishMutation({
      data: res.data,
      createdRef: createdPlan,
      selectedRef: selectedPlan,
      successMessage: SUCCESS_MESSAGES.planCreated,
      notify: showSuccess,
      refresh: load
    })
  })
}

async function submitPlan(planId) {
  if (!canEdit.value) return
  await runSubmitTask(async () => {
    await api(`/api/v1/publish-plans/${planId}/submit`, { method: 'POST', body: '{}' })
    await finishMutation({
      successMessage: SUCCESS_MESSAGES.planSubmitted,
      notify: showSuccess,
      refresh: load
    })
  })
}

function clearPlanFilters() {
  clearRefValues(planKeyword, statusFilter)
}

watch(() => [route.query.plan, route.query.draft, route.query.status], applyRouteSelection)
watch(
  () => selectedPlatform.value,
  (platform) => {
    if (!supportsNotePlatforms.has(platform) && publishForm.contentType === 'note') {
      publishForm.contentType = 'video'
    }
    if (platform !== 'tencent') {
      publishForm.publishStrategy = 'immediate'
      publishForm.isDraft = 'false'
      publishForm.shortTitle = ''
      publishForm.category = ''
      publishForm.thumbnailFile = ''
      publishForm.thumbnailLandscapeFile = ''
      publishForm.thumbnailPortraitFile = ''
    }
    if (platform !== 'youtube') {
      publishForm.youtubeVisibility = 'public'
      publishForm.youtubePlaylist = ''
      publishForm.youtubeThumbnailFile = ''
    }
  }
)

load()
</script>
