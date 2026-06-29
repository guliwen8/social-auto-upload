<template>
  <div class="page">
    <div class="page-header">
      <h1>{{ PAGE_TEXTS.accounts.title }}</h1>
      <div class="muted">{{ PAGE_TEXTS.accounts.description }}</div>
    </div>

    <AppReadonlyNotice
      v-if="!canEdit"
      :message="PAGE_TEXTS.accounts.readonlyMessage"
    />

    <div class="row">
      <AppFormCard :title="PAGE_TEXTS.accounts.forms.createAccount.title" :hint="PAGE_TEXTS.accounts.forms.createAccount.hint">
        <AppFormFields :model="accountForm" :fields="accountFormFields" />
        <button @click="createAccount" :disabled="loading || !canEdit">{{ BUTTON_TEXTS.registerAccount }}</button>
        <template #result>
          <AppDetailGrid v-if="createdAccount" :items="createdAccountItems" />
        </template>
      </AppFormCard>

      <div class="card">
        <h2>{{ PAGE_TEXTS.accounts.sections.accountList }}</h2>
        <AppListToolbar :config="PAGE_TEXTS.accounts.toolbars.accounts" :loading="loadingList" @refresh="load">
          <AppFilterFields :fields="accountToolbarFields" />
        </AppListToolbar>
        <AppLoading v-if="loadingList" text="正在加载账号..." />
        <div v-else-if="filteredAccounts.length" class="list">
          <AppEntityListItem
            v-for="account in filteredAccounts"
            :key="account.id"
            :title="account.account_name"
            :badge="statusLabel(account.status)"
            :badge-class="['status-tag', account.status]"
            :lines="getAccountListLines(account)"
          >
            <template #actions>
              <button class="secondary" @click="selectedAccount = account">{{ BUTTON_TEXTS.viewDetail }}</button>
              <button class="secondary" @click="checkAccount(account.id)" :disabled="!canEdit">{{ BUTTON_TEXTS.healthCheck }}</button>
            </template>
          </AppEntityListItem>
        </div>
        <AppEmpty
          v-else
          :config="accountListEmptyState"
          @action="accounts.length ? clearAccountFilters() : null"
        />
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h2>{{ PAGE_TEXTS.accounts.sections.accountDetail }}</h2>
        <AppDetailGrid v-if="selectedAccount" :items="accountDetailItems" />
        <AppNextStep v-if="selectedAccount" :step="accountNextStep" />
        <AppEmpty v-else :config="accountSelectionEmptyState" />
      </div>

      <div class="card">
        <h2>{{ PAGE_TEXTS.accounts.sections.relatedPlans }}</h2>
        <div v-if="relatedPlans.length" class="list">
          <AppEntityListItem
            v-for="plan in relatedPlans.slice(0, 5)"
            :key="plan.id"
            :title="plan.account_name"
            :badge="statusLabel(plan.status)"
            :badge-class="['status-tag', plan.status]"
            :lines="getRelatedPlanListLines(plan)"
          >
            <template #actions>
              <button class="secondary" @click="$router.push({ path: '/publish', query: { plan: plan.id } })">{{ BUTTON_TEXTS.viewPlan }}</button>
            </template>
          </AppEntityListItem>
        </div>
        <AppEmpty v-else :config="relatedPlanEmptyState" />
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
import { accountPlatformOptions, accountStatusOptions } from '../constants/options'
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
import { getAccountDetailItems, getCreatedAccountItems } from '../utils/detail-configs'
import { createFilterSelectField, createInputField, createSelectField, createToolbarFields } from '../utils/field-configs'
import { requireMinLength, requireText } from '../utils/form-validation'
import { getFilterableEmptyStateFromConfig, getSelectionEmptyStateFromConfig } from '../utils/empty-configs'
import { getAccountListLines, getRelatedPlanListLines } from '../utils/list-configs'
import { finishMutation } from '../utils/mutation-helpers'
import { assignSelection, clearRefValues } from '../utils/page-state'
import { matchesKeyword } from '../utils/collection'
import { getAccountNextStep } from '../utils/view-configs'
import { statusLabel } from '../utils/display'

const route = useRoute()
const { loading, run: runSubmitTask } = useAsyncTask((error) => showError(error.message || ERROR_MESSAGES.actionFailed))
const { loading: loadingList, run: runListTask } = useAsyncTask((error) => showError(error.message || ERROR_MESSAGES.accountLoadFailed))
const accounts = ref([])
const createdAccount = ref(null)
const selectedAccount = ref(null)
const allPlans = ref([])
const accountForm = reactive({
  platform: 'douyin',
  accountName: ''
})
const accountKeyword = ref('')
const statusFilter = ref('')
const canEdit = computed(() => canEditContent(session.actor?.role))
const accountFormFields = computed(() => [
  createSelectField('platform', accountPlatformOptions),
  createInputField('accountName', PAGE_TEXTS.accounts.forms.createAccount.fields.accountName)
])
const accountToolbarFields = computed(() =>
  createToolbarFields({
    keywordKey: 'accountKeyword',
    keywordModel: accountKeyword,
    keywordPlaceholder: PAGE_TEXTS.accounts.toolbars.accounts.searchPlaceholder,
    selectFields: [createFilterSelectField('statusFilter', statusFilter, accountStatusOptions)]
  })
)
const createdAccountItems = computed(() => getCreatedAccountItems(createdAccount.value, statusLabel))
const accountNextStep = computed(() => getAccountNextStep(selectedAccount.value))
const accountListEmptyState = computed(() => getFilterableEmptyStateFromConfig(PAGE_TEXTS.accounts.emptyStates.accounts, accounts.value.length))
const accountSelectionEmptyState = getSelectionEmptyStateFromConfig(PAGE_TEXTS.accounts.emptyStates.accountSelection)
const relatedPlanEmptyState = getSelectionEmptyStateFromConfig(PAGE_TEXTS.accounts.emptyStates.relatedPlans)
const filteredAccounts = computed(() => {
  const status = route.query.status || statusFilter.value
  const accountId = route.query.account
  return accounts.value.filter((item) => {
    const statusMatched = !status || item.status === status
    const accountMatched = !accountId || item.id === accountId
    const keywordMatched = matchesKeyword([item.id, item.account_name, item.platform], accountKeyword.value)
    return statusMatched && accountMatched && keywordMatched
  })
})
const accountDetailItems = computed(() => getAccountDetailItems(selectedAccount.value, statusLabel))
const relatedPlans = computed(() =>
  allPlans.value.filter((item) => item.account_id === selectedAccount.value?.id)
)

function applyRouteSelection() {
  assignSelection(selectedAccount, filteredAccounts.value, route.query.account, selectedAccount.value)
}

async function load() {
  await runListTask(async () => {
    const [accountsRes, plansRes] = await Promise.all([api('/api/v1/accounts'), api('/api/v1/publish-plans/mine')])
    accounts.value = accountsRes.data || []
    allPlans.value = plansRes.data || []
    applyRouteSelection()
  })
}

async function createAccount() {
  if (!canEdit.value) return
  const normalizedName = accountForm.accountName.trim()
  if (!requireText(normalizedName, '请先填写账号名称', showWarning)) return
  if (!requireMinLength(normalizedName, 2, '账号名称至少需要 2 个字符', showWarning)) return
  await runSubmitTask(async () => {
    const res = await api('/api/v1/accounts', {
      method: 'POST',
      body: JSON.stringify({ platform: accountForm.platform, account_name: normalizedName })
    })
    await finishMutation({
      data: res.data,
      createdRef: createdAccount,
      selectedRef: selectedAccount,
      successMessage: SUCCESS_MESSAGES.accountCreated,
      notify: showSuccess,
      refresh: load
    })
  })
}

async function checkAccount(accountId) {
  if (!canEdit.value) return
  await runSubmitTask(async () => {
    await api(`/api/v1/accounts/${accountId}/check`, { method: 'POST', body: '{}' })
    await finishMutation({
      successMessage: SUCCESS_MESSAGES.accountChecked,
      notify: showSuccess,
      refresh: load
    })
  })
}

function clearAccountFilters() {
  clearRefValues(accountKeyword, statusFilter)
}

watch(() => [route.query.account, route.query.status], applyRouteSelection)

load()
</script>
