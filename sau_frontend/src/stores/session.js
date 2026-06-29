import { reactive } from 'vue'
import { api, setToken } from '../api/client'

export const session = reactive({
  actor: null,
  workspaces: [],
  activeWorkspaceId: ''
})

export async function refreshSession() {
  const meRes = await api('/api/v1/me')
  const wsRes = await api('/api/v1/workspaces')
  session.actor = meRes.data
  session.workspaces = wsRes.data || []
  session.activeWorkspaceId = meRes.data?.workspace_id || ''
  return session
}

export async function logout() {
  setToken('')
  session.actor = null
  session.workspaces = []
  session.activeWorkspaceId = ''
}

export async function switchWorkspace(workspaceId) {
  const res = await api('/api/v1/auth/switch-workspace', {
    method: 'POST',
    body: JSON.stringify({ workspace_id: workspaceId })
  })
  setToken(res.data.token)
  await refreshSession()
}

export function canEditContent(role) {
  return ['owner', 'admin', 'editor'].includes(role || '')
}
