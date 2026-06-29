export function getAssetListLines(asset) {
  return [`素材编号：${asset.id}`]
}

export function getDraftListLines(draft) {
  return [`草稿编号：${draft.id}`, `关联素材：${(draft.asset_ids || []).join(', ') || '无'}`]
}

export function getPublishPlanListLines(plan) {
  return [`计划编号：${plan.id}`, `草稿：${plan.draft_id || '-'}`]
}

export function getDraftPlanListLines(plan) {
  return [`计划编号：${plan.id}`]
}

export function getAccountListLines(account) {
  return [`账号编号：${account.id}`, `平台：${account.platform}`]
}

export function getRelatedPlanListLines(plan) {
  return [`计划编号：${plan.id}`]
}

export function getTaskListLines(task) {
  return [`任务编号：${task.id}`, `错误类型：${task.last_error_type || '无'}`, `最近更新时间：${task.updated_at || '-'}`]
}

export function getRecordPlanListLines(plan) {
  return [`计划编号：${plan.id}`, `计划类型：${plan.content_type}`, `最近更新时间：${plan.updated_at || '-'}`]
}

export function getHomeAlertLines(alert) {
  return [alert.desc]
}

export function getHomeRecentPlanLines(plan) {
  return [`计划编号：${plan.id}`, `${plan.platform} / ${plan.content_type}`]
}

export function getHomeFailedTaskLines(task) {
  return [`错误类型：${task.last_error_type || '无'}`]
}

export function getHomeInvalidAccountLines(account) {
  return [`平台：${account.platform}`]
}
