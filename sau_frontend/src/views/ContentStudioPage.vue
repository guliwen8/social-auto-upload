<template>
  <div class="page">
    <div class="page-header">
      <h1>{{ PAGE_TEXTS.content.title }}</h1>
      <div class="muted">{{ PAGE_TEXTS.content.description }}</div>
    </div>

    <AppReadonlyNotice
      v-if="!canEdit"
      :message="PAGE_TEXTS.content.readonlyMessage"
    />

    <div class="row">
      <AppFormCard :title="PAGE_TEXTS.content.forms.createAsset.title" :hint="PAGE_TEXTS.content.forms.createAsset.hint">
        <AppFormFields :model="assetForm" :fields="assetFormFields" />
        <button @click="createAsset" :disabled="loading || !canEdit">{{ BUTTON_TEXTS.createAsset }}</button>
        <template #result>
          <AppDetailGrid v-if="createdAsset" :items="createdAssetItems" />
        </template>
      </AppFormCard>

      <AppFormCard :title="PAGE_TEXTS.content.forms.createDraft.title" :hint="PAGE_TEXTS.content.forms.createDraft.hint">
        <AppFormFields :model="draftForm" :fields="draftFormFields" />
        <button @click="createDraft" :disabled="loading || !canEdit">{{ BUTTON_TEXTS.createDraft }}</button>
        <template #result>
          <AppDetailGrid v-if="createdDraft" :items="createdDraftItems" />
        </template>
      </AppFormCard>
    </div>

    <div class="row">
      <div class="card">
        <h2>{{ PAGE_TEXTS.content.sections.assetList }}</h2>
        <AppListToolbar :config="PAGE_TEXTS.content.toolbars.assets" :loading="loadingList" @refresh="load">
          <AppFilterFields :fields="assetToolbarFields" />
        </AppListToolbar>
        <AppLoading v-if="loadingList" text="正在加载素材..." />
        <div v-else-if="filteredAssets.length" class="list">
          <AppEntityListItem
            v-for="asset in filteredAssets"
            :key="asset.id"
            :title="asset.path"
            :badge="asset.asset_type"
            :lines="getAssetListLines(asset)"
          >
            <template #actions>
              <button class="secondary" @click="selectedAsset = asset">{{ BUTTON_TEXTS.viewDetail }}</button>
            </template>
          </AppEntityListItem>
        </div>
        <AppEmpty
          v-else
          :config="assetListEmptyState"
          @action="assets.length ? clearAssetFilters() : null"
        />
      </div>

      <div class="card">
        <h2>{{ PAGE_TEXTS.content.sections.draftList }}</h2>
        <AppListToolbar :config="PAGE_TEXTS.content.toolbars.drafts" :loading="loadingList" @refresh="load">
          <AppFilterFields :fields="draftToolbarFields" />
        </AppListToolbar>
        <AppLoading v-if="loadingList" text="正在加载草稿..." />
        <div v-else-if="filteredDrafts.length" class="list">
          <AppEntityListItem
            v-for="draft in filteredDrafts"
            :key="draft.id"
            :title="draft.title"
            :badge="statusLabel(draft.status)"
            :badge-class="['status-tag', draft.status]"
            :lines="getDraftListLines(draft)"
          >
            <template #actions>
              <button class="secondary" @click="selectedDraft = draft">{{ BUTTON_TEXTS.viewDetail }}</button>
              <button class="secondary" @click="goCreatePlan(draft.id)">{{ BUTTON_TEXTS.createPlanFromDraft }}</button>
            </template>
          </AppEntityListItem>
        </div>
        <AppEmpty
          v-else
          :config="draftListEmptyState"
          @action="drafts.length ? clearDraftFilters() : null"
        />
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h2>{{ PAGE_TEXTS.content.sections.assetDetail }}</h2>
        <AppDetailGrid v-if="selectedAsset" :items="assetDetailItems" />
        <AppEmpty v-else :config="assetSelectionEmptyState" />
      </div>

      <div class="card">
        <h2>{{ PAGE_TEXTS.content.sections.draftDetail }}</h2>
        <AppDetailGrid v-if="selectedDraft" :items="draftDetailItems" />
        <div v-if="selectedDraft" class="toolbar">
          <button class="secondary" @click="goCreatePlan(selectedDraft.id)">{{ BUTTON_TEXTS.createPlanFromSelectedDraft }}</button>
        </div>
        <AppNextStep v-if="selectedDraft" :step="draftNextStep" />
        <AppEmpty v-else :config="draftSelectionEmptyState" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import { BUTTON_TEXTS } from '../constants/button-texts'
import { ERROR_MESSAGES } from '../constants/error-messages'
import { PAGE_TEXTS } from '../constants/page-texts'
import { SUCCESS_MESSAGES } from '../constants/messages'
import { useAsyncTask } from '../composables/useAsyncTask'
import { assetTypeOptions } from '../constants/options'
import AppDetailGrid from '../components/AppDetailGrid.vue'
import AppEntityListItem from '../components/AppEntityListItem.vue'
import AppFilterFields from '../components/AppFilterFields.vue'
import AppLoading from '../components/AppLoading.vue'
import AppEmpty from '../components/AppEmpty.vue'
import AppFormFields from '../components/AppFormFields.vue'
import AppFormCard from '../components/AppFormCard.vue'
import AppListToolbar from '../components/AppListToolbar.vue'
import AppReadonlyNotice from '../components/AppReadonlyNotice.vue'
import { canEditContent, session } from '../stores/session'
import { showError, showSuccess, showWarning } from '../state/ui'
import { getAssetDetailItems, getCreatedAssetItems, getCreatedDraftItems, getDraftDetailItems } from '../utils/detail-configs'
import { createInputField, createSelectField, createTextareaField, createToolbarFields } from '../utils/field-configs'
import { requireListLength, requireMinLength, requireText, validateAssetPathForType } from '../utils/form-validation'
import { getFilterableEmptyStateFromConfig, getSelectionEmptyStateFromConfig } from '../utils/empty-configs'
import { getAssetListLines, getDraftListLines } from '../utils/list-configs'
import { finishMutation } from '../utils/mutation-helpers'
import { assignSelection, clearRefValues } from '../utils/page-state'
import { getContentDraftNextStep } from '../utils/view-configs'
import { matchesKeyword } from '../utils/collection'
const route = useRoute()
const router = useRouter()
const { loading, run: runSubmitTask } = useAsyncTask((error) => showError(error.message || ERROR_MESSAGES.actionFailed))
const { loading: loadingList, run: runListTask } = useAsyncTask((error) => showError(error.message || ERROR_MESSAGES.contentLoadFailed))
const assets = ref([])
const drafts = ref([])
const createdAsset = ref(null)
const createdDraft = ref(null)
const selectedAsset = ref(null)
const selectedDraft = ref(null)
const assetForm = reactive({
  assetType: 'video',
  assetPath: ''
})
const draftForm = reactive({
  draftTitle: '',
  draftDesc: '',
  draftTags: '',
  draftAssetIds: ''
})
const assetKeyword = ref('')
const draftKeyword = ref('')
const canEdit = computed(() => canEditContent(session.actor?.role))
const assetFormFields = computed(() => [
  createSelectField('assetType', assetTypeOptions),
  createInputField('assetPath', PAGE_TEXTS.content.forms.createAsset.fields.assetPath)
])
const draftFormFields = computed(() => [
  createInputField('draftTitle', PAGE_TEXTS.content.forms.createDraft.fields.draftTitle),
  createTextareaField('draftDesc', PAGE_TEXTS.content.forms.createDraft.fields.draftDesc, { rows: 4 }),
  createInputField('draftTags', PAGE_TEXTS.content.forms.createDraft.fields.draftTags),
  createInputField('draftAssetIds', PAGE_TEXTS.content.forms.createDraft.fields.draftAssetIds)
])
const assetToolbarFields = computed(() =>
  createToolbarFields({
    keywordKey: 'assetKeyword',
    keywordModel: assetKeyword,
    keywordPlaceholder: PAGE_TEXTS.content.toolbars.assets.searchPlaceholder
  })
)
const draftToolbarFields = computed(() =>
  createToolbarFields({
    keywordKey: 'draftKeyword',
    keywordModel: draftKeyword,
    keywordPlaceholder: PAGE_TEXTS.content.toolbars.drafts.searchPlaceholder
  })
)
const filteredAssets = computed(() => {
  return assets.value.filter((item) => matchesKeyword([item.id, item.path, item.asset_type], assetKeyword.value))
})
const filteredDrafts = computed(() => {
  return drafts.value.filter((item) => matchesKeyword([item.id, item.title, item.description, ...(item.tags || [])], draftKeyword.value))
})
const assetDetailItems = computed(() => getAssetDetailItems(selectedAsset.value))
const draftDetailItems = computed(() => getDraftDetailItems(selectedDraft.value, statusLabel))
const createdAssetItems = computed(() => getCreatedAssetItems(createdAsset.value))
const createdDraftItems = computed(() => getCreatedDraftItems(createdDraft.value))
const draftNextStep = computed(() => (selectedDraft.value ? getContentDraftNextStep(selectedDraft.value.id) : null))
const assetListEmptyState = computed(() => getFilterableEmptyStateFromConfig(PAGE_TEXTS.content.emptyStates.assets, assets.value.length))
const draftListEmptyState = computed(() => getFilterableEmptyStateFromConfig(PAGE_TEXTS.content.emptyStates.drafts, drafts.value.length))
const assetSelectionEmptyState = getSelectionEmptyStateFromConfig(PAGE_TEXTS.content.emptyStates.assetSelection)
const draftSelectionEmptyState = getSelectionEmptyStateFromConfig(PAGE_TEXTS.content.emptyStates.draftSelection)

function applyRouteSelection() {
  assignSelection(selectedDraft, drafts.value, route.query.draft, selectedDraft.value)
}

async function load() {
  await runListTask(async () => {
    const [assetsRes, draftsRes] = await Promise.all([api('/api/v1/assets'), api('/api/v1/drafts')])
    assets.value = assetsRes.data || []
    drafts.value = draftsRes.data || []
    applyRouteSelection()
  })
}

async function createAsset() {
  if (!canEdit.value) return
  const normalizedPath = assetForm.assetPath.trim()
  if (!validateAssetPathForType(assetForm.assetType, normalizedPath, showWarning)) return
  await runSubmitTask(async () => {
    const res = await api('/api/v1/assets', {
      method: 'POST',
      body: JSON.stringify({ asset_type: assetForm.assetType, path: normalizedPath })
    })
    await finishMutation({
      data: res.data,
      createdRef: createdAsset,
      selectedRef: selectedAsset,
      successMessage: SUCCESS_MESSAGES.assetCreated,
      notify: showSuccess,
      refresh: load
    })
  })
}

async function createDraft() {
  if (!canEdit.value) return
  const title = draftForm.draftTitle.trim()
  const description = draftForm.draftDesc.trim()
  const tags = draftForm.draftTags.split(',').map((item) => item.trim()).filter(Boolean)
  const assetIds = draftForm.draftAssetIds.split(',').map((item) => item.trim()).filter(Boolean)
  if (!requireText(title, '请先填写草稿标题', showWarning)) return
  if (!requireMinLength(title, 4, '草稿标题建议至少 4 个字，便于后续检索', showWarning)) return
  if (!requireListLength(assetIds, 1, '请至少关联一个素材编号', showWarning)) return
  await runSubmitTask(async () => {
    const res = await api('/api/v1/drafts', {
      method: 'POST',
      body: JSON.stringify({
        title,
        description,
        tags,
        asset_ids: assetIds
      })
    })
    await finishMutation({
      data: res.data,
      createdRef: createdDraft,
      selectedRef: selectedDraft,
      successMessage: SUCCESS_MESSAGES.draftCreated,
      notify: showSuccess,
      refresh: load
    })
  })
}

function goCreatePlan(draftId) {
  router.push({ path: '/publish', query: { draft: draftId } })
}

function clearAssetFilters() {
  clearRefValues(assetKeyword)
}

function clearDraftFilters() {
  clearRefValues(draftKeyword)
}

watch(() => route.query.draft, applyRouteSelection)

load()
</script>
