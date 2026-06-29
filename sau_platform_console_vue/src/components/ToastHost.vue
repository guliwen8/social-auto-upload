<template>
  <transition name="fade">
    <div v-if="uiState.toastVisible" class="toast" :class="uiState.toastType" @click="closeToast">
      {{ uiState.toastMessage }}
    </div>
  </transition>
</template>

<script setup lang="ts">
import { closeToast, uiState } from "../state/ui";
</script>

