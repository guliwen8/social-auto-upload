<template>
  <template v-for="field in fields" :key="field.key">
    <select
      v-if="field.type === 'select'"
      v-model="field.model.value"
    >
      <option
        v-for="option in field.options || []"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>

    <input
      v-else
      v-model="field.model.value"
      :type="field.inputType || 'text'"
      :placeholder="field.placeholder || ''"
    />
  </template>
</template>

<script setup>
defineProps({
  fields: { type: Array, default: () => [] }
})
</script>
