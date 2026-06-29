<template>
  <div class="app-empty">
    <div class="app-empty__title">{{ resolvedTitle }}</div>
    <div v-if="resolvedDescription" class="app-empty__desc">{{ resolvedDescription }}</div>
    <div v-if="resolvedActionLabel" class="toolbar" style="margin-top: 10px;">
      <button class="secondary" @click="goAction">{{ resolvedActionLabel }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const emit = defineEmits(['action'])

const props = defineProps({
  config: { type: Object, default: null },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
  actionTo: { type: [String, Object], default: '' }
})

const resolvedTitle = computed(() => props.config?.title || props.title)
const resolvedDescription = computed(() => props.config?.description || props.description)
const resolvedActionLabel = computed(() => props.config?.actionLabel || props.actionLabel)
const resolvedActionTo = computed(() => props.config?.actionTo || props.actionTo)

function goAction() {
  emit('action')
  if (!resolvedActionTo.value) return
  router.push(resolvedActionTo.value)
}
</script>
