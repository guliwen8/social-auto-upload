<template>
  <div class="empty-state">
    <div class="empty-title">{{ title }}</div>
    <div v-if="description" class="muted">{{ description }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
}>();
</script>

