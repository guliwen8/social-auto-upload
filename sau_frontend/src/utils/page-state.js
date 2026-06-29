import { pickSelected } from './collection'

export function clearRefValues(...refs) {
  refs.forEach((refItem) => {
    refItem.value = ''
  })
}

export function assignSelection(targetRef, list, explicitId, current, idKey = 'id') {
  targetRef.value = pickSelected(list, explicitId, current, idKey)
}
