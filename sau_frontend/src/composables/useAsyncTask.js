import { ref } from 'vue'

export function useAsyncTask(errorHandler) {
  const loading = ref(false)

  async function run(task) {
    loading.value = true
    try {
      return await task()
    } catch (error) {
      if (errorHandler) errorHandler(error)
      return undefined
    } finally {
      loading.value = false
    }
  }

  return { loading, run }
}
