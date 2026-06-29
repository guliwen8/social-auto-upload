<template>
  <template v-for="field in fields" :key="field.key">
    <select
      v-if="field.type === 'select'"
      v-model="model[field.key]"
    >
      <option
        v-for="option in field.options || []"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>

    <textarea
      v-else-if="field.type === 'textarea'"
      v-model="model[field.key]"
      :rows="field.rows || 4"
      :placeholder="field.placeholder || ''"
    />

    <input
      v-else
      v-model="model[field.key]"
      :type="field.inputType || 'text'"
      :placeholder="field.placeholder || ''"
      @keyup.enter="field.enterHandler ? field.enterHandler() : undefined"
    />
  </template>
</template>

<script setup>
defineProps({
  model: { type: Object, required: true },
  fields: { type: Array, default: () => [] }
})
</script>
