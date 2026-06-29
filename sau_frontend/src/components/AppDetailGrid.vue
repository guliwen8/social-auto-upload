<template>
  <div class="detail-grid">
    <div
      v-for="item in items"
      :key="item.label"
      class="detail-item"
      :class="{ full: item.full }"
    >
      <div class="detail-label">{{ item.label }}</div>
      <div class="detail-value">{{ item.value || '-' }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    default: () => []
  }
})
</script>
