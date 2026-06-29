export function getFilterableEmptyState({ hasItems, emptyTitle, emptyDescription, filteredTitle, filteredDescription, createLabel, createTo, resetTo }) {
  if (hasItems) {
    return {
      title: filteredTitle,
      description: filteredDescription,
      actionLabel: '清空筛选',
      actionTo: resetTo
    }
  }

  return {
    title: emptyTitle,
    description: emptyDescription,
    actionLabel: createLabel,
    actionTo: createTo
  }
}

export function getFilterableEmptyStateFromConfig(config, hasItems) {
  return getFilterableEmptyState({
    hasItems,
    emptyTitle: config.emptyTitle,
    emptyDescription: config.emptyDescription,
    filteredTitle: config.filteredTitle,
    filteredDescription: config.filteredDescription,
    createLabel: config.createLabel,
    createTo: config.createTo,
    resetTo: config.resetTo
  })
}

export function getSelectionEmptyState({ title, description, actionLabel, actionTo }) {
  return { title, description, actionLabel, actionTo }
}

export function getSelectionEmptyStateFromConfig(config) {
  return getSelectionEmptyState(config)
}
