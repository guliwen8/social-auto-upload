<template>
  <div class="readonly-banner">
    <strong>当前为只读模式</strong>
    <div class="muted">{{ message || '你当前只能查看内容和执行状态，不能创建、提交或触发修改类操作。' }}</div>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: '' }
})
</script>
