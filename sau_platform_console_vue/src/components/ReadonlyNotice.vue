<template>
  <div class="readonly-notice">
    <strong>当前为只读模式</strong>
    <div class="muted">{{ message || "你的角色仅可查看数据，不能执行创建、审批、提交或触发执行等修改类操作。" }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ message?: string }>();
</script>

