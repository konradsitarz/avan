import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getBriefing } from '../api.js'

export const useBriefingStore = defineStore('briefing', () => {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const phase = ref('summary') // summary | review | done
  const currentIndex = ref(0)

  const currentIssue = computed(() => {
    if (!data.value || !data.value.issues.length) return null
    return data.value.issues[currentIndex.value]
  })

  const issueCount = computed(() => data.value?.issues?.length || 0)

  async function fetch() {
    loading.value = true
    error.value = null
    try {
      data.value = await getBriefing()
    } catch (e) {
      error.value = 'Nie udało się wygenerować briefingu'
    } finally {
      loading.value = false
    }
  }

  function beginReview() {
    currentIndex.value = 0
    phase.value = 'review'
  }

  function nextIssue() {
    if (data.value && currentIndex.value < data.value.issues.length - 1) {
      currentIndex.value++
    }
  }

  function prevIssue() {
    if (currentIndex.value > 0) {
      currentIndex.value--
    }
  }

  function finishReview() {
    phase.value = 'done'
  }

  function backToSummary() {
    phase.value = 'summary'
  }

  function updateCurrentIssue(fields) {
    if (!currentIssue.value) return
    Object.assign(currentIssue.value, fields)
  }

  return {
    data, loading, error, phase, currentIndex,
    currentIssue, issueCount,
    fetch, beginReview, nextIssue, prevIssue, finishReview, backToSummary,
    updateCurrentIssue,
  }
})
