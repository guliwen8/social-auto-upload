export function getWorkspaceSummaryItems({ activeWorkspaceId, roleLabel }) {
  return [
    { label: '当前工作区', value: activeWorkspaceId || '-' },
    { label: '当前角色', value: roleLabel || '-' }
  ]
}

export function getProfileIdentityItems({ displayName, email, roleLabel, activeWorkspaceId }) {
  return [
    { label: '显示名', value: displayName || '-' },
    { label: '邮箱', value: email || '-' },
    { label: '角色', value: roleLabel || '-' },
    { label: '当前工作区', value: activeWorkspaceId || '-' }
  ]
}

export function getAiSettingItems({ provider, model, baseUrl }) {
  return [
    { label: 'Provider', value: provider || '-' },
    { label: 'Model', value: model || '-' },
    { label: 'Base URL', value: baseUrl || '-', full: true }
  ]
}

export function getLoginResultItems({ mode, result, fallbackEmail }) {
  const items = [
    { label: '邮箱', value: result.email || fallbackEmail || '-' },
    { label: '显示名', value: result.display_name || '-' }
  ]

  if (mode === 'login') {
    items.push({ label: '工作区', value: result.workspace_id || '-' })
  }

  if (mode === 'register') {
    items.push({ label: '用户编号', value: result.id || '-' })
  }

  return items
}

export function getTaskDetailItems(task, statusLabel) {
  if (!task) return []
  return [
    { label: '任务编号', value: task.id },
    { label: '状态', value: statusLabel(task.status) },
    { label: '计划编号', value: task.publish_plan_id || '-' },
    { label: '尝试次数', value: task.attempts ?? 0 },
    { label: '错误类型', value: task.last_error_type || '无' },
    { label: '错误信息', value: task.last_error_message || '无', full: true }
  ]
}

export function getRecordPlanDetailItems(plan, statusLabel) {
  if (!plan) return []
  return [
    { label: '计划编号', value: plan.id },
    { label: '状态', value: statusLabel(plan.status) },
    { label: '账号', value: plan.account_name || '-' },
    { label: '类型', value: plan.content_type || '-' },
    { label: '计划时间', value: plan.payload?.scheduled_for || '-', full: true }
  ]
}

export function getAssetDetailItems(asset) {
  if (!asset) return []
  return [
    { label: '素材编号', value: asset.id },
    { label: '素材类型', value: asset.asset_type },
    { label: '素材路径', value: asset.path || '-', full: true },
    { label: '创建时间', value: asset.created_at || '-' }
  ]
}

export function getDraftDetailItems(draft, statusLabel) {
  if (!draft) return []
  return [
    { label: '草稿编号', value: draft.id },
    { label: '状态', value: statusLabel(draft.status) },
    { label: '标题', value: draft.title || '-', full: true },
    { label: '描述', value: draft.description || '-', full: true },
    { label: '标签', value: (draft.tags || []).join('、') || '无', full: true },
    { label: '关联素材', value: (draft.asset_ids || []).join(', ') || '无', full: true }
  ]
}

export function getCreatedAssetItems(asset) {
  if (!asset) return []
  return [
    { label: '素材编号', value: asset.id },
    { label: '素材类型', value: asset.asset_type }
  ]
}

export function getCreatedDraftItems(draft) {
  if (!draft) return []
  return [
    { label: '草稿编号', value: draft.id },
    { label: '标题', value: draft.title }
  ]
}

export function getCreatedPlanItems(plan, statusLabel) {
  if (!plan) return []
  return [
    { label: '计划编号', value: plan.id },
    { label: '计划状态', value: statusLabel(plan.status) }
  ]
}

export function getPublishPlanDetailItems(plan, statusLabel) {
  if (!plan) return []
  return [
    { label: '计划编号', value: plan.id },
    { label: '状态', value: statusLabel(plan.status) },
    { label: '账号', value: plan.account_name || '-' },
    { label: '平台', value: plan.platform || '-' },
    { label: '草稿编号', value: plan.draft_id || '-' },
    { label: '内容类型', value: plan.content_type || '-' },
    { label: '计划时间', value: plan.payload?.scheduled_for || '-', full: true }
  ]
}

export function getCreatedAccountItems(account, statusLabel) {
  if (!account) return []
  return [
    { label: '账号编号', value: account.id },
    { label: '当前状态', value: statusLabel(account.status) }
  ]
}

export function getAccountDetailItems(account, statusLabel) {
  if (!account) return []
  return [
    { label: '账号编号', value: account.id },
    { label: '状态', value: statusLabel(account.status) },
    { label: '账号名', value: account.account_name || '-' },
    { label: '平台', value: account.platform || '-' },
    { label: '创建时间', value: account.created_at || '-', full: true }
  ]
}
