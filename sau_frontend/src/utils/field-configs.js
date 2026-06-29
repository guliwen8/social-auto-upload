export function createInputField(key, placeholder, extra = {}) {
  return { key, placeholder, ...extra }
}

export function createTextareaField(key, placeholder, extra = {}) {
  return { key, type: 'textarea', placeholder, ...extra }
}

export function createSelectField(key, options, extra = {}) {
  return { key, type: 'select', options, ...extra }
}

export function createFilterInputField(key, model, placeholder, extra = {}) {
  return { key, model, placeholder, ...extra }
}

export function createFilterSelectField(key, model, options, extra = {}) {
  return { key, type: 'select', model, options, ...extra }
}

export function prependPlaceholderOption(label, options) {
  return [{ value: '', label }, ...options]
}

export function createToolbarFields({ keywordKey, keywordModel, keywordPlaceholder, selectFields = [] }) {
  return [
    createFilterInputField(keywordKey, keywordModel, keywordPlaceholder),
    ...selectFields
  ]
}
