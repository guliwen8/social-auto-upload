export const PAGE_TEXTS = {
  home: {
    title: '首页',
    description: '查看内容资产、发布计划、执行任务和账号健康状态。',
    sections: {
      quickActions: '快捷入口',
      statusSummary: '状态摘要',
      alerts: '待处理事项',
      recentPlans: '最近发布计划',
      failedTasks: '最近失败任务',
      invalidAccounts: '异常账号'
    },
    emptyStates: {
      alerts: {
        title: '暂无待处理事项',
        description: '当前没有明显异常或堆积流程。',
        actionLabel: '去创建计划',
        actionTo: '/publish'
      },
      recentPlans: {
        title: '暂无发布计划',
        description: '创建计划后，这里会展示最近的发布安排。',
        actionLabel: '去创建计划',
        actionTo: '/publish'
      },
      failedTasks: {
        title: '暂无失败任务',
        description: '当前执行链路比较稳定。',
        actionLabel: '查看全部记录',
        actionTo: '/records'
      },
      invalidAccounts: {
        title: '暂无异常账号',
        description: '账号状态目前正常。',
        actionLabel: '查看账号',
        actionTo: '/accounts'
      }
    }
  },
  content: {
    title: '内容准备',
    description: '创建素材、整理草稿，并为后续发布计划做好准备。',
    readonlyMessage: '当前角色只能查看素材和草稿，不能创建新的内容资产。',
    forms: {
      createAsset: {
        title: '创建素材',
        hint: '建议使用完整路径，视频素材用 `.mp4`，图片素材用 `.png`、`.jpg` 等后缀。',
        fields: {
          assetPath: '素材路径，例如 /uploads/demo.mp4'
        }
      },
      createDraft: {
        title: '创建草稿',
        hint: '至少填写标题，并建议关联至少一个已创建素材，便于后续直接生成发布计划。',
        fields: {
          draftTitle: '草稿标题',
          draftDesc: '草稿描述',
          draftTags: '标签，使用逗号分隔',
          draftAssetIds: '关联素材编号，使用逗号分隔'
        }
      }
    },
    sections: {
      assetList: '素材列表',
      draftList: '草稿列表',
      assetDetail: '素材详情',
      draftDetail: '草稿详情'
    },
    emptyStates: {
      assets: {
        emptyTitle: '暂无素材',
        emptyDescription: '先创建素材，再整理成草稿。',
        filteredTitle: '没有匹配素材',
        filteredDescription: '换一个关键词试试，或者先清空筛选条件。',
        createLabel: '去创建素材',
        createTo: '/content',
        resetTo: { path: '/content' }
      },
      drafts: {
        emptyTitle: '暂无草稿',
        emptyDescription: '创建草稿后，这里会显示内容准备结果。',
        filteredTitle: '没有匹配草稿',
        filteredDescription: '当前筛选条件没有匹配结果，可以调整关键词后再试。',
        createLabel: '去创建草稿',
        createTo: '/content',
        resetTo: { path: '/content' }
      },
      assetSelection: {
        title: '请选择素材',
        description: '点击素材列表中的“查看详情”查看完整信息。',
        actionLabel: '查看素材列表',
        actionTo: '/content'
      },
      draftSelection: {
        title: '请选择草稿',
        description: '点击草稿列表中的“查看详情”查看完整内容。',
        actionLabel: '去创建草稿',
        actionTo: '/content'
      }
    },
    toolbars: {
      assets: {
        refreshLabel: '刷新素材',
        searchPlaceholder: '搜索素材路径或编号'
      },
      drafts: {
        refreshLabel: '刷新草稿',
        searchPlaceholder: '搜索草稿标题、编号或标签'
      }
    }
  },
  publish: {
    title: '发布中心',
    description: '从草稿、账号和发布时间生成新的发布计划，并跟踪审批状态。',
    readonlyMessage: '当前角色只能查看发布计划，不能新建计划或提交审批。',
    forms: {
      createPlan: {
        title: '新建发布计划',
        hint: '建议明确选择账号、草稿和计划时间，避免创建后还要反复回改。',
        routeDraftHintPrefix: '当前已从草稿带入：',
        fields: {
          accountPlaceholder: '选择账号',
          draftPlaceholder: '选择草稿',
          scheduledFor: '计划时间，可选，例如 2026-06-29T10:00:00+08:00'
        }
      }
    },
    sections: {
      myPlans: '我的计划',
      planDetail: '计划详情',
      pendingPlans: '待提交计划'
    },
    emptyStates: {
      plans: {
        emptyTitle: '暂无发布计划',
        emptyDescription: '创建新计划后，这里会显示你的发布安排。',
        filteredTitle: '没有匹配计划',
        filteredDescription: '当前筛选条件没有匹配到计划，可以调整关键词或状态。',
        createLabel: '去创建计划',
        createTo: '/publish',
        resetTo: { path: '/publish' }
      },
      planSelection: {
        title: '请选择计划',
        description: '点击计划列表中的“查看详情”查看完整信息。',
        actionLabel: '查看计划列表',
        actionTo: '/publish'
      },
      draftPlans: {
        title: '暂无待提交计划',
        description: '草稿计划创建后，这里会优先展示尚未提交审批的计划。',
        actionLabel: '去准备内容',
        actionTo: '/content'
      }
    },
    toolbars: {
      plans: {
        refreshLabel: '刷新计划',
        searchPlaceholder: '搜索账号、计划编号或草稿编号'
      }
    }
  },
  accounts: {
    title: '账号管理',
    description: '查看账号状态、补充新账号，并检查账号健康情况。',
    readonlyMessage: '当前角色只能查看账号状态，不能注册账号或执行健康检查。',
    forms: {
      createAccount: {
        title: '注册账号',
        hint: '建议使用清晰可识别的账号名称，方便后续在计划和执行记录中快速定位。',
        fields: {
          accountName: '账号名称'
        }
      }
    },
    sections: {
      accountList: '账号列表',
      accountDetail: '账号详情',
      relatedPlans: '关联计划'
    },
    emptyStates: {
      accounts: {
        emptyTitle: '暂无账号',
        emptyDescription: '注册账号后，这里会展示账号列表和状态。',
        filteredTitle: '没有匹配账号',
        filteredDescription: '当前筛选条件没有匹配到账号，可以调整关键词或状态。',
        createLabel: '去注册账号',
        createTo: '/accounts',
        resetTo: { path: '/accounts' }
      },
      accountSelection: {
        title: '请选择账号',
        description: '点击账号列表中的“查看详情”查看更多信息。',
        actionLabel: '查看账号列表',
        actionTo: '/accounts'
      },
      relatedPlans: {
        title: '暂无关联计划',
        description: '选中账号后，这里会展示与该账号相关的最近计划。',
        actionLabel: '去创建计划',
        actionTo: '/publish'
      }
    },
    toolbars: {
      accounts: {
        refreshLabel: '刷新账号',
        searchPlaceholder: '搜索账号名、编号或平台'
      }
    }
  },
  records: {
    title: '执行记录',
    description: '查看任务执行结果、失败原因和最近的计划推进状态。',
    sections: {
      taskList: '任务记录',
      planStatus: '计划推进状态',
      taskDetail: '任务详情',
      planDetail: '计划详情'
    },
    emptyStates: {
      tasks: {
        emptyTitle: '暂无任务记录',
        emptyDescription: '计划开始执行后，这里会展示任务结果。',
        filteredTitle: '没有匹配任务',
        filteredDescription: '当前筛选条件没有匹配到任务，可以调整关键词或状态。',
        createLabel: '去查看计划',
        createTo: '/publish',
        resetTo: { path: '/records' }
      },
      plans: {
        emptyTitle: '暂无计划状态',
        emptyDescription: '创建计划后，这里会显示推进记录。',
        filteredTitle: '没有匹配计划状态',
        filteredDescription: '当前筛选条件没有匹配到计划，可以换一个关键词试试。',
        createLabel: '去创建计划',
        createTo: '/publish',
        resetTo: { path: '/records' }
      },
      taskSelection: {
        title: '请选择任务',
        description: '点击任务列表中的“查看详情”查看完整执行结果。',
        actionLabel: '查看任务列表',
        actionTo: '/records'
      },
      planSelection: {
        title: '请选择计划',
        description: '点击计划状态中的“查看详情”查看完整信息。',
        actionLabel: '查看计划状态',
        actionTo: '/records'
      }
    },
    toolbars: {
      tasks: {
        refreshLabel: '刷新任务',
        searchPlaceholder: '搜索任务编号、计划编号或错误类型'
      },
      plans: {
        refreshLabel: '刷新计划',
        searchPlaceholder: '搜索计划编号、账号或类型'
      }
    }
  },
  profile: {
    title: '个人中心',
    description: '查看当前身份、工作区和 AI 配置，确认你正在正确的工作环境中。',
    workspaceHint: '如果你在错误工作区里，请先在顶部切换工作区后再继续操作。',
    emptyStates: {
      workspaces: {
        title: '暂无工作区',
        description: '登录成功后，这里会显示你可访问的工作区。',
        actionLabel: '返回首页',
        actionTo: '/'
      },
      aiSettings: {
        title: '暂无 AI 配置',
        description: '尚未读取到工作区 AI 配置信息。',
        actionLabel: '刷新个人中心',
        actionTo: '/profile'
      }
    }
  },
  login: {
    title: '登录用户端',
    description: '使用平台账号进入内容准备、发布和执行记录工作台。',
    hint: '建议使用有效邮箱地址。登录后如果没有工作区，会在顶部提示你当前状态。',
    fields: {
      email: '邮箱',
      password: '密码'
    },
    emptyState: {
      title: '等待登录',
      description: '登录或注册成功后，这里会显示结果摘要。'
    }
  }
}
