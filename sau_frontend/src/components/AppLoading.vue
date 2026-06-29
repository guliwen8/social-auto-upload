<template>
  <div class="app-loading">
    <div class="app-loading__dot"></div>
    <div>{{ text || '加载中...' }}</div>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '加载中...' }
})
</script>
