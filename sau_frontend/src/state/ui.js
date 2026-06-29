import { reactive } from 'vue'

let id = 0

export const uiState = reactive({
  toasts: []
})

function pushToast(type, message) {
  const toast = { id: `toast-${++id}`, type, message }
  uiState.toasts.push(toast)
  setTimeout(() => removeToast(toast.id), 2600)
}

export function showSuccess(message) {
  pushToast('success', message)
}

export function showError(message) {
  pushToast('error', message)
}

export function showWarning(message) {
  pushToast('warning', message)
}

export function removeToast(toastId) {
  const index = uiState.toasts.findIndex((item) => item.id === toastId)
  if (index >= 0) uiState.toasts.splice(index, 1)
}
