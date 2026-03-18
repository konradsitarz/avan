<template>
  <div class="feed">
    <div class="page-header">
      <div class="header-row">
        <div>
          <h1 class="page-title">Message Feed</h1>
          <p class="page-subtitle">Prioritized by severity</p>
        </div>
        <div class="header-actions">
          <div class="filter-group">
            <select v-model="filterPriority">
              <option value="">All priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select v-model="filterType">
              <option value="">All channels</option>
              <option value="email">Email</option>
              <option value="sms">SMS</option>
              <option value="voice">Voice</option>
            </select>
          </div>
          <button class="btn" @click="fetchMessages">Refresh</button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="empty-state">Loading...</div>
    <div v-else-if="error" class="empty-state" style="color: var(--urgent)">{{ error }}</div>
    <div v-else-if="sortedMessages.length === 0" class="empty-state">
      <p>No messages found</p>
    </div>

    <div v-else class="feed-layout">
      <div class="feed-list">
        <div
          v-for="msg in sortedMessages"
          :key="msg._id || msg.id"
          class="feed-item card"
          :class="{ selected: selected?._id === msg._id || selected?.id === msg.id }"
          @click="selected = msg"
        >
          <div class="feed-item-left">
            <div class="priority-dot" :class="`dot-${msg.priority}`"></div>
          </div>
          <div class="feed-item-body">
            <div class="feed-item-top">
              <span class="feed-sender">{{ msg.sender }}</span>
              <span class="feed-time">{{ timeAgo(msg.created_at) }}</span>
            </div>
            <p class="feed-content">{{ truncate(msg.content, 100) }}</p>
            <div class="feed-item-tags">
              <span class="badge" :class="`badge-${msg.priority}`">{{ msg.priority }}</span>
              <span class="badge" :class="`badge-${msg.type}`">{{ msg.type }}</span>
              <span v-if="msg.followup_count > 0" class="badge badge-high">{{ msg.followup_count }}x follow-up</span>
              <span v-if="msg.assigned_to" class="feed-assigned">{{ msg.assigned_to }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="feed-detail card" v-if="selected">
        <div class="detail-header">
          <div class="detail-badges">
            <span class="badge" :class="`badge-${selected.priority}`">{{ selected.priority }}</span>
            <span class="badge" :class="`badge-${selected.type}`">{{ selected.type }}</span>
          </div>
          <button class="btn btn-sm btn-danger" @click="handleDelete(selected._id || selected.id)">Delete</button>
        </div>

        <div class="detail-field">
          <label>From</label>
          <p>{{ selected.sender }}</p>
        </div>

        <div class="detail-field">
          <label>Content</label>
          <p class="detail-content">{{ selected.content }}</p>
        </div>

        <div class="detail-meta">
          <div class="detail-field">
            <label>Follow-ups</label>
            <p>{{ selected.followup_count }}</p>
          </div>
          <div class="detail-field">
            <label>Received</label>
            <p>{{ formatDate(selected.created_at) }}</p>
          </div>
          <div class="detail-field">
            <label>Assigned to</label>
            <p>{{ selected.assigned_to || 'Unassigned' }}</p>
          </div>
        </div>

        <div class="detail-actions">
          <div class="assign-row">
            <input v-model="assignInput" placeholder="Assign to..." @keyup.enter="handleAssign" />
            <button class="btn btn-primary btn-sm" @click="handleAssign">Assign</button>
          </div>
          <div class="priority-row">
            <label>Change priority</label>
            <div class="priority-buttons">
              <button
                v-for="p in ['low','medium','high','urgent']"
                :key="p"
                class="btn btn-sm"
                :class="{ 'btn-primary': selected.priority === p }"
                @click="handlePriority(p)"
              >{{ p }}</button>
            </div>
          </div>
        </div>
      </div>
      <div class="feed-detail card empty-detail" v-else>
        <p class="empty-state">Select a message to view details</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getMessages, updateMessage, deleteMessage } from '../api.js'

const messages = ref([])
const loading = ref(false)
const error = ref(null)
const selected = ref(null)
const assignInput = ref('')
const filterPriority = ref('')
const filterType = ref('')

const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 }

const sortedMessages = computed(() => {
  let list = [...messages.value]
  if (filterPriority.value) list = list.filter(m => m.priority === filterPriority.value)
  if (filterType.value) list = list.filter(m => m.type === filterType.value)
  list.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority])
  return list
})

const fetchMessages = async () => {
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

const handleAssign = async () => {
  if (!selected.value || !assignInput.value.trim()) return
  const id = selected.value._id || selected.value.id
  try {
    const updated = await updateMessage(id, { ...selected.value, assigned_to: assignInput.value.trim() })
    selected.value = updated
    assignInput.value = ''
    await fetchMessages()
  } catch (e) {
    error.value = 'Failed to assign'
  }
}

const handlePriority = async (priority) => {
  if (!selected.value) return
  const id = selected.value._id || selected.value.id
  try {
    const updated = await updateMessage(id, { ...selected.value, priority })
    selected.value = updated
    await fetchMessages()
  } catch (e) {
    error.value = 'Failed to update priority'
  }
}

const handleDelete = async (id) => {
  if (!confirm('Delete this message?')) return
  try {
    await deleteMessage(id)
    selected.value = null
    await fetchMessages()
  } catch (e) {
    error.value = 'Failed to delete'
  }
}

const truncate = (str, len) => str.length > len ? str.slice(0, len) + '...' : str

const timeAgo = (dateStr) => {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

const formatDate = (dateStr) => new Date(dateStr).toLocaleString()

onMounted(fetchMessages)
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filter-group {
  display: flex;
  gap: 8px;
}

.filter-group select {
  width: auto;
  min-width: 140px;
}

.feed-layout {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 16px;
  align-items: start;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.feed-item {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.1s;
}

.feed-item:hover {
  background: var(--bg-hover);
}

.feed-item.selected {
  border-color: var(--accent);
  background: rgba(88,166,255,0.05);
}

.feed-item-left {
  padding-top: 4px;
}

.priority-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot-urgent { background: var(--urgent); box-shadow: 0 0 6px var(--urgent); }
.dot-high { background: var(--high); }
.dot-medium { background: var(--medium); }
.dot-low { background: var(--low); }

.feed-item-body {
  flex: 1;
  min-width: 0;
}

.feed-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.feed-sender {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

.feed-time {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.feed-content {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-item-tags {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.feed-assigned {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: auto;
}

/* Detail panel */
.feed-detail {
  position: sticky;
  top: 24px;
  padding: 20px;
}

.empty-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.detail-badges {
  display: flex;
  gap: 6px;
}

.detail-field {
  margin-bottom: 16px;
}

.detail-field p {
  font-size: 14px;
  color: var(--text-primary);
  margin-top: 4px;
}

.detail-content {
  white-space: pre-wrap;
  line-height: 1.6;
}

.detail-meta {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  padding: 16px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
}

.detail-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.assign-row {
  display: flex;
  gap: 8px;
}

.assign-row input {
  flex: 1;
}

.priority-row label {
  margin-bottom: 8px;
}

.priority-buttons {
  display: flex;
  gap: 6px;
}
</style>
