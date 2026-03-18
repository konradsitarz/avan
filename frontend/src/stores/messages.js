import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getMessages,
  createMessage,
  updateMessage,
  deleteMessage,
  deleteAllMessages,
  overrideMessage,
} from '../api.js'

export const useMessagesStore = defineStore('messages', () => {
  const messages = ref([])
  const loading = ref(false)
  const error = ref(null)

  const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 }

  const sorted = computed(() =>
    [...messages.value].sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority])
  )

  const stats = computed(() => ({
    total: messages.value.length,
    urgent: messages.value.filter(m => m.priority === 'urgent').length,
    high: messages.value.filter(m => m.priority === 'high').length,
    medium: messages.value.filter(m => m.priority === 'medium').length,
    low: messages.value.filter(m => m.priority === 'low').length,
    unassigned: messages.value.filter(m => !m.assigned_to).length,
  }))

  async function fetch() {
    loading.value = true
    error.value = null
    try {
      messages.value = await getMessages()
    } catch (e) {
      error.value = 'Failed to load messages'
    } finally {
      loading.value = false
    }
  }

  async function create(msg) {
    const result = await createMessage(msg)
    messages.value.push(result)
    return result
  }

  async function update(id, data) {
    const result = await updateMessage(id, data)
    const idx = messages.value.findIndex(m => (m._id || m.id) === id)
    if (idx !== -1) messages.value[idx] = result
    return result
  }

  async function remove(id) {
    await deleteMessage(id)
    messages.value = messages.value.filter(m => (m._id || m.id) !== id)
  }

  async function clearAll() {
    await deleteAllMessages()
    messages.value = []
  }

  async function override(id, payload) {
    const result = await overrideMessage(id, payload)
    const idx = messages.value.findIndex(m => (m._id || m.id) === id)
    if (idx !== -1) messages.value[idx] = result
    return result
  }

  return {
    messages, loading, error,
    sorted, stats,
    fetch, create, update, remove, clearAll, override,
  }
})
