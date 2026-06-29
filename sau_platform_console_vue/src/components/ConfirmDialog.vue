<template>
  <div v-if="uiState.confirmVisible" class="modal-mask" @click.self="resolveConfirm(false)">
    <div class="modal-card">
      <div class="page-header">
        <h2>{{ uiState.confirmTitle }}</h2>
      </div>
      <div v-if="uiState.confirmMessage" class="muted">{{ uiState.confirmMessage }}</div>
      <div v-if="uiState.confirmInputLabel" class="stack" style="margin-top: 12px">
        <label class="muted">{{ uiState.confirmInputLabel }}</label>
        <input v-model="uiState.confirmValue" :placeholder="uiState.confirmInputPlaceholder" />
      </div>
      <div class="toolbar" style="margin-top: 16px">
        <button class="secondary" @click="resolveConfirm(false)">{{ uiState.confirmCancelText }}</button>
        <button :class="uiState.confirmDanger ? 'danger' : ''" @click="onConfirm">
          {{ uiState.confirmConfirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { resolveConfirm, showToast, uiState } from "../state/ui";

function onConfirm() {
  if (uiState.confirmInputRequired && !uiState.confirmValue.trim()) {
    showToast("请输入必填内容", "error");
    return;
  }
  resolveConfirm(true);
}
</script>

