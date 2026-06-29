export function getHomeQuickActions() {
  return [
    { label: '准备内容', to: '/content' },
    { label: '创建计划', to: '/publish' },
    { label: '查看执行', to: '/records' },
    { label: '检查账号', to: '/accounts' }
  ]
}

export function getHomeMetrics({ assetsCount, draftsCount, plansCount, pendingCount, tasksCount, failedCount, accountCount, invalidAccountCount }) {
  return [
    { label: '内容素材', value: assetsCount, desc: `草稿 ${draftsCount}` },
    { label: '发布计划', value: plansCount, desc: `待审批 ${pendingCount}` },
    { label: '执行任务', value: tasksCount, desc: `失败 ${failedCount}` },
    { label: '账号数量', value: accountCount, desc: `异常 ${invalidAccountCount}` }
  ]
}

export function getHomeAlerts({ failedTasks, invalidAccounts, pendingPlans }) {
  const result = []

  if (failedTasks.length) {
    result.push({
      title: '存在失败任务',
      level: '高优先级',
      desc: `当前有 ${failedTasks.length} 个失败任务。`,
      to: { path: '/records', query: { taskStatus: 'failed', plan: failedTasks[0]?.publish_plan_id || '' } }
    })
  }

  if (invalidAccounts.length) {
    result.push({
      title: '存在异常账号',
      level: '需处理',
      desc: `当前有 ${invalidAccounts.length} 个异常账号。`,
      to: { path: '/accounts', query: { status: 'invalid', account: invalidAccounts[0]?.id || '' } }
    })
  }

  if (pendingPlans.length) {
    result.push({
      title: '存在待审批计划',
      level: '待关注',
      desc: `当前有 ${pendingPlans.length} 条计划等待审批。`,
      to: { path: '/publish', query: { status: 'pending_approval', plan: pendingPlans[0]?.id || '' } }
    })
  }

  return result
}

export function getProfileQuickActions() {
  return [
    { label: '去准备内容', to: '/content' },
    { label: '去创建计划', to: '/publish' },
    { label: '查看执行记录', to: '/records' }
  ]
}

export function getProfileAbilityItems({ canEdit, workspaceCount }) {
  return [
    {
      title: '内容编辑',
      badge: canEdit ? '可编辑' : '只读',
      lines: ['决定你是否可以创建素材、草稿、计划，以及执行账号检查等操作。']
    },
    {
      title: '工作区切换',
      badge: workspaceCount > 1 ? '可切换' : '单工作区',
      lines: [`你当前可访问 ${workspaceCount} 个工作区。`]
    }
  ]
}

export function getHomeStatusItems({ assetsCount, draftsCount, plansCount, pendingCount, failedCount }) {
  return [
    {
      title: '内容准备度',
      badge: assetsCount && draftsCount ? '已具备' : '待补充',
      lines: [`当前有 ${assetsCount} 个素材、${draftsCount} 个草稿。`]
    },
    {
      title: '发布推进',
      badge: plansCount ? '进行中' : '未开始',
      lines: [`待审批 ${pendingCount} 条，失败任务 ${failedCount} 条。`]
    }
  ]
}

export function getHomeNextStep({ assetsCount, draftsCount, pendingCount, failedCount }) {
  if (!assetsCount || !draftsCount) {
    return {
      description: '先去内容准备补齐素材和草稿，再开始创建发布计划。',
      actionLabel: '去准备内容',
      actionTo: '/content'
    }
  }

  if (pendingCount) {
    return {
      description: '优先处理待审批计划，避免内容已准备好但未能进入执行。',
      actionLabel: '去查看计划',
      actionTo: '/publish'
    }
  }

  if (failedCount) {
    return {
      description: '当前有失败任务，建议先检查执行记录与账号状态。',
      actionLabel: '去查看执行',
      actionTo: '/records'
    }
  }

  return {
    description: '当前链路比较顺畅，可以继续创建新计划或扩充内容库。',
    actionLabel: '去创建计划',
    actionTo: '/publish'
  }
}

export function getContentDraftNextStep(draftId) {
  return {
    description: '内容准备完成后，可以直接基于这个草稿创建发布计划，再提交审批或跟踪执行结果。',
    actionLabel: '去创建计划',
    actionTo: { path: '/publish', query: { draft: draftId } }
  }
}

export function getPublishPlanNextStep(plan) {
  if (!plan) return null

  if (plan.status === 'draft') {
    return {
      description: '当前计划仍是草稿，可以继续检查信息后提交审批。',
      actionLabel: '提交审批',
      actionTo: '/publish'
    }
  }

  if (plan.status === 'pending_approval') {
    return {
      description: '当前计划正在等待审批，建议先查看审批结果或继续准备其他内容。',
      actionLabel: '查看计划',
      actionTo: '/publish'
    }
  }

  return {
    description: '当前计划已进入执行链路，建议查看执行记录确认最终结果。',
    actionLabel: '查看执行记录',
    actionTo: { path: '/records', query: { plan: plan.id } }
  }
}

export function getAccountNextStep(account) {
  if (!account) return null

  if (account.status === 'invalid') {
    return {
      description: '当前账号状态异常，建议先执行健康检查，再继续创建发布计划。',
      actionLabel: '继续检查账号',
      actionTo: { path: '/accounts', query: { account: account.id } }
    }
  }

  return {
    description: '当前账号状态可用，可以继续去发布中心创建计划或查看关联计划。',
    actionLabel: '去创建计划',
    actionTo: '/publish'
  }
}
