<template>
  <div class="page" style="min-height: 100vh; place-content: center; max-width: 480px; margin: 0 auto; padding: 24px;">
    <div class="card">
      <div class="page-header">
        <h1>{{ PAGE_TEXTS.login.title }}</h1>
        <div class="muted">{{ PAGE_TEXTS.login.description }}</div>
      </div>
      <AppFormFields :model="loginForm" :fields="loginFormFields" />
      <div class="muted">{{ PAGE_TEXTS.login.hint }}</div>
      <div class="toolbar">
        <button @click="onLogin" :disabled="loading">{{ BUTTON_TEXTS.login }}</button>
        <button class="secondary" @click="onRegister" :disabled="loading">{{ BUTTON_TEXTS.register }}</button>
      </div>
      <AppLoading v-if="loading" text="正在处理请求..." />
      <AppDetailGrid v-else-if="resultMode" :items="loginResultItems" />
      <AppEmpty v-else :config="PAGE_TEXTS.login.emptyState" />
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { setToken } from '../api/client'
import { BUTTON_TEXTS } from '../constants/button-texts'
import { ERROR_MESSAGES } from '../constants/error-messages'
import { PAGE_TEXTS } from '../constants/page-texts'
import { SUCCESS_MESSAGES } from '../constants/messages'
import { refreshSession } from '../stores/session'
import AppDetailGrid from '../components/AppDetailGrid.vue'
import AppFormFields from '../components/AppFormFields.vue'
import AppLoading from '../components/AppLoading.vue'
import AppEmpty from '../components/AppEmpty.vue'
import { createInputField } from '../utils/field-configs'
import { requireMinLength, requireText, validateEmail } from '../utils/form-validation'
import { getLoginResultItems } from '../utils/detail-configs'
import { showError, showSuccess, showWarning } from '../state/ui'

const router = useRouter()
const loginForm = reactive({
  email: '',
  password: ''
})
const loading = ref(false)
const resultMode = ref('')
const result = reactive({})
const loginFormFields = computed(() => [
  createInputField('email', PAGE_TEXTS.login.fields.email, { enterHandler: onLogin }),
  createInputField('password', PAGE_TEXTS.login.fields.password, { inputType: 'password', enterHandler: onLogin })
])
const loginResultItems = computed(() =>
  getLoginResultItems({
    mode: resultMode.value,
    result,
    fallbackEmail: loginForm.email
  })
)

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  const data = await response.json()
  if (!response.ok || data.code !== 200) throw new Error(data.msg || ERROR_MESSAGES.requestFailed)
  return data
}

async function onLogin() {
  const normalizedEmail = loginForm.email.trim()
  const normalizedPassword = loginForm.password.trim()
  if (!validateEmail(normalizedEmail, showWarning)) return
  if (!requireText(normalizedPassword, '请先填写密码', showWarning)) return
  loading.value = true
  try {
    const res = await postJson('/api/v1/auth/login', { email: normalizedEmail, password: normalizedPassword })
    setToken(res.data.token)
    await refreshSession()
    Object.assign(result, res.data || {})
    resultMode.value = 'login'
    showSuccess(SUCCESS_MESSAGES.login)
    router.push('/')
  } catch (error) {
    showError(error.message || ERROR_MESSAGES.loginFailed)
  } finally {
    loading.value = false
  }
}

async function onRegister() {
  const normalizedEmail = loginForm.email.trim()
  const normalizedPassword = loginForm.password.trim()
  if (!validateEmail(normalizedEmail, showWarning)) return
  if (!requireMinLength(normalizedPassword, 6, '密码至少需要 6 个字符', showWarning)) return
  loading.value = true
  try {
    const res = await postJson('/api/v1/auth/register', {
      email: normalizedEmail,
      password: normalizedPassword,
      display_name: normalizedEmail
    })
    Object.assign(result, res.data || {})
    resultMode.value = 'register'
    showSuccess(SUCCESS_MESSAGES.register)
  } catch (error) {
    showError(error.message || ERROR_MESSAGES.registerFailed)
  } finally {
    loading.value = false
  }
}
</script>
