<template>
  <AppSectionCard :title="title">
    <div class="form-card">
      <slot />
      <div v-if="hint" class="muted">{{ hint }}</div>
      <div v-if="$slots.result">
        <slot name="result" />
      </div>
    </div>
  </AppSectionCard>
</template>

<script setup>
import AppSectionCard from './AppSectionCard.vue'

defineProps({
  title: { type: String, required: true },
  hint: { type: String, default: '' }
})
</script>
