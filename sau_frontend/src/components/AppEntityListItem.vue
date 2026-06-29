<template>
  <div class="list-item">
    <div class="list-item__head">
      <strong>{{ title }}</strong>
      <span v-if="badge" :class="badgeClass">{{ badge }}</span>
    </div>
    <div v-for="line in lines" :key="line" class="muted">{{ line }}</div>
    <div v-if="$slots.actions" class="toolbar">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  badge: { type: String, default: '' },
  badgeClass: { type: [String, Array, Object], default: 'pill' },
  lines: { type: Array, default: () => [] }
})
</script>
