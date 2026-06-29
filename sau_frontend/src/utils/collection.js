export function normalizeKeyword(keyword) {
  return String(keyword || '').trim().toLowerCase()
}

export function matchesKeyword(values, keyword) {
  const normalized = normalizeKeyword(keyword)
  if (!normalized) return true
  return values.some((value) => String(value || '').toLowerCase().includes(normalized))
}

export function pickSelected(list, explicitId, current, idKey = 'id') {
  if (explicitId) {
    return list.find((item) => item[idKey] === explicitId) || null
  }
  return current || list[0] || null
}
