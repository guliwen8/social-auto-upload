export function getToken() {
  return localStorage.getItem('sau_token') || ''
}

export function setToken(token) {
  localStorage.setItem('sau_token', token || '')
}

export async function api(path, init = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(init.headers || {})
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(path, { ...init, headers })
  const data = await response.json()
  if (!response.ok || data.code !== 200) {
    throw new Error(data.msg || `请求失败: ${response.status}`)
  }
  return data
}
