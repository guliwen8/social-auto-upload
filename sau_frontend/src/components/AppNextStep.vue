<template>
  <div class="readonly-banner">
    <strong>{{ resolvedTitle || '下一步建议' }}</strong>
    <div class="muted">{{ resolvedDescription }}</div>
    <div v-if="resolvedActionLabel && resolvedActionTo" class="toolbar" style="margin-top: 10px;">
      <button class="secondary" @click="router.push(resolvedActionTo)">{{ resolvedActionLabel }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  step: { type: Object, default: null },
  title: { type: String, default: '下一步建议' },
  description: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
  actionTo: { type: [String, Object], default: '' }
})

const resolvedTitle = computed(() => props.step?.title || props.title)
const resolvedDescription = computed(() => props.step?.description || props.description)
const resolvedActionLabel = computed(() => props.step?.actionLabel || props.actionLabel)
const resolvedActionTo = computed(() => props.step?.actionTo || props.actionTo)
</script>
