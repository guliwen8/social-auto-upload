const ROLE_MAP: Record<string, string> = {
  owner: "负责人",
  admin: "管理员",
  editor: "编辑者",
  viewer: "只读成员",
};

const STATUS_MAP: Record<string, string> = {
  draft: "草稿",
  pending_approval: "待审批",
  active: "启用",
  rejected: "已驳回",
  queued: "排队中",
  running: "执行中",
  succeeded: "已成功",
  failed: "已失败",
  canceled: "已取消",
  unknown: "未知",
  invalid: "异常",
  ready: "就绪",
  archived: "已归档",
  revoked: "已吊销",
};

const SCOPE_TYPE_MAP: Record<string, string> = {
  platform: "平台级",
  account: "账号级",
};

export function roleLabel(role?: string | null) {
  if (!role) return "-";
  return ROLE_MAP[role] || role;
}

export function statusLabel(status?: string | null) {
  if (!status) return "-";
  return STATUS_MAP[status] || status;
}

export function scopeTypeLabel(scopeType?: string | null) {
  if (!scopeType) return "-";
  return SCOPE_TYPE_MAP[scopeType] || scopeType;
}

