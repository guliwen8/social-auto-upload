export function requirePresent(value, message, notify) {
  if (value === undefined || value === null || value === '') {
    notify(message)
    return false
  }
  return true
}

export function requireText(value, message, notify) {
  if (!String(value || '').trim()) {
    notify(message)
    return false
  }
  return true
}

export function requireMinLength(value, min, message, notify) {
  if (String(value || '').trim().length < min) {
    notify(message)
    return false
  }
  return true
}

export function requirePattern(value, pattern, message, notify) {
  if (!pattern.test(String(value || '').trim())) {
    notify(message)
    return false
  }
  return true
}

export function requireListLength(items, min, message, notify) {
  if ((items || []).length < min) {
    notify(message)
    return false
  }
  return true
}

export function validateEmail(value, notify) {
  return (
    requireText(value, '请先填写邮箱', notify) &&
    requirePattern(value, /^[^\s@]+@[^\s@]+\.[^\s@]+$/, '请输入有效的邮箱地址', notify)
  )
}

export function validateAssetPathForType(assetType, path, notify) {
  if (!requireText(path, '请先填写素材路径', notify)) return false
  const lowerPath = String(path || '').trim().toLowerCase()
  if (assetType === 'video') {
    return requirePattern(lowerPath, /\.(mp4|mov|m4v|avi)$/, '视频素材建议使用 mp4、mov、m4v 或 avi 文件', notify)
  }
  return requirePattern(lowerPath, /\.(png|jpg|jpeg|webp|gif)$/, '图片素材建议使用 png、jpg、jpeg、webp 或 gif 文件', notify)
}
