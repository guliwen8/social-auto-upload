export const assetTypeOptions = [
  { value: 'video', label: '视频' },
  { value: 'image', label: '图片' }
]

export const publishContentTypeOptions = [
  { value: 'video', label: '视频' },
  { value: 'note', label: '图文' }
]

export const publishStatusOptions = [
  { value: '', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'pending_approval', label: '待审批' },
  { value: 'active', label: '启用' },
  { value: 'rejected', label: '已驳回' }
]

export const accountPlatformOptions = [
  { value: 'douyin', label: '抖音' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'kuaishou', label: '快手' },
  { value: 'bilibili', label: 'Bilibili' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'tencent', label: '视频号' }
]

export const publishStrategyOptions = [
  { value: 'immediate', label: '立即发布' },
  { value: 'scheduled', label: '定时发布' }
]

export const booleanChoiceOptions = [
  { value: 'false', label: '否' },
  { value: 'true', label: '是' }
]

export const youtubeVisibilityOptions = [
  { value: 'public', label: '公开' },
  { value: 'unlisted', label: '不公开' },
  { value: 'private', label: '私密' }
]

export const accountStatusOptions = [
  { value: '', label: '全部状态' },
  { value: 'active', label: '启用' },
  { value: 'invalid', label: '异常' }
]

export const taskStatusOptions = [
  { value: '', label: '全部状态' },
  { value: 'queued', label: '排队中' },
  { value: 'running', label: '执行中' },
  { value: 'succeeded', label: '已成功' },
  { value: 'failed', label: '已失败' }
]
