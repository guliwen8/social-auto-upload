const roleMap = {
  owner: '负责人',
  admin: '管理员',
  editor: '编辑者',
  viewer: '只读成员'
}

const statusMap = {
  draft: '草稿',
  pending_approval: '待审批',
  active: '启用',
  rejected: '已驳回',
  queued: '排队中',
  running: '执行中',
  succeeded: '已成功',
  failed: '已失败',
  canceled: '已取消',
  invalid: '异常',
  ready: '就绪',
  archived: '已归档',
  revoked: '已吊销'
}

export function roleLabel(role) {
  return roleMap[role] || role || '-'
}

export function statusLabel(status) {
  return statusMap[status] || status || '-'
}
