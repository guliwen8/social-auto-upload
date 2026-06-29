<template>
  <div class="loading-block">
    <div class="loading-dot"></div>
    <div class="muted">{{ text || "加载中..." }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ text?: string }>();
</script>

