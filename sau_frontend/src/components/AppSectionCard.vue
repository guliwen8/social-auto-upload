<template>
  <div class="card">
    <div class="section-card__head">
      <h2>{{ title }}</h2>
      <div v-if="$slots.actions" class="section-card__actions">
        <slot name="actions" />
      </div>
    </div>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true }
})
</script>
