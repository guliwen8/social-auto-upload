export async function finishMutation({ data, createdRef, selectedRef, successMessage, notify, refresh }) {
  if (createdRef) createdRef.value = data
  if (selectedRef) selectedRef.value = data
  if (successMessage && notify) notify(successMessage)
  if (refresh) await refresh()
}
