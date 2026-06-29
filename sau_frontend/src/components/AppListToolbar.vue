<template>
  <div class="toolbar toolbar--panel">
    <div class="toolbar__filters">
      <slot />
    </div>
    <button
      v-if="resolvedRefreshLabel"
      class="secondary"
      @click="emit('refresh')"
      :disabled="loading"
    >
      {{ resolvedRefreshLabel }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  config: { type: Object, default: null },
  refreshLabel: { type: String, default: '' },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['refresh'])
const resolvedRefreshLabel = computed(() => props.config?.refreshLabel || props.refreshLabel)
</script>
