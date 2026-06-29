<template>
  <div class="toast-host">
    <div v-for="toast in uiState.toasts" :key="toast.id" class="toast-item" :class="toast.type">
      <div>{{ toast.message }}</div>
      <button class="toast-close" @click="removeToast(toast.id)">关闭</button>
    </div>
  </div>
</template>

<script setup>
import { removeToast, uiState } from '../state/ui'
</script>
