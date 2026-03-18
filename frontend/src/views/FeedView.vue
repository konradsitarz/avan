<template>
  <div class="feed">
    <div class="page-header">
      <div class="header-row">
        <div>
          <h1 class="page-title">Zgłoszenia</h1>
          <p class="page-subtitle">Posortowane wg priorytetu</p>
        </div>
        <div class="header-actions">
          <div class="filter-group">
            <select v-model="filterPriority">
              <option value="">Wszystkie priorytety</option>
              <option value="urgent">Pilne</option>
              <option value="high">Ważne</option>
              <option value="medium">Średnie</option>
              <option value="low">Niskie</option>
            </select>
            <select v-model="filterType">
              <option value="">Wszystkie kanały</option>
              <option value="email">Email</option>
              <option value="sms">SMS</option>
              <option value="voice">Telefon</option>
            </select>
          </div>
          <button class="btn" @click="fetchMessages">Odśwież</button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="empty-state">Ładowanie...</div>
    <div v-else-if="error" class="empty-state" style="color: var(--urgent)">{{ error }}</div>
    <div v-else-if="sortedMessages.length === 0" class="empty-state">
      <p>Brak zgłoszeń</p>
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
          <button class="btn btn-sm btn-danger" @click="handleDelete(selected._id || selected.id)">Usuń</button>
        </div>

        <div class="detail-field">
          <label>Od</label>
          <p>{{ selected.sender }}</p>
        </div>

        <div class="detail-field">
          <label>Treść</label>
          <p class="detail-content">{{ selected.content }}</p>
        </div>

        <div class="detail-meta">
          <div class="detail-field">
            <label>Ponowienia</label>
            <p>{{ selected.followup_count }}</p>
          </div>
          <div class="detail-field">
            <label>Otrzymano</label>
            <p>{{ formatDate(selected.created_at) }}</p>
          </div>
          <div class="detail-field">
            <label>Przypisano do</label>
            <p>{{ selected.assigned_to || 'Nieprzypisane' }}</p>
          </div>
        </div>

        <div class="detail-actions">
          <div class="assign-row">
            <input v-model="assignInput" placeholder="Przypisz do..." @keyup.enter="handleAssign" />
            <button class="btn btn-primary btn-sm" @click="handleAssign">Przypisz</button>
          </div>
          <div class="priority-row">
            <label>Zmień priorytet</label>
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
        <p class="empty-state">Wybierz wiadomość, aby zobaczyć szczegóły</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useMessagesStore } from '../stores/messages.js'

const store = useMessagesStore()
const { loading, error } = storeToRefs(store)

const selected = ref(null)
const assignInput = ref('')
const filterPriority = ref('')
const filterType = ref('')

const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 }

const sortedMessages = computed(() => {
  let list = [...store.messages]
  if (filterPriority.value) list = list.filter(m => m.priority === filterPriority.value)
  if (filterType.value) list = list.filter(m => m.type === filterType.value)
  list.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority])
  return list
})

const fetchMessages = () => store.fetch()

const handleAssign = async () => {
  if (!selected.value || !assignInput.value.trim()) return
  const id = selected.value._id || selected.value.id
  try {
    selected.value = await store.update(id, { ...selected.value, assigned_to: assignInput.value.trim() })
    assignInput.value = ''
  } catch (e) {
    error.value = 'Nie udało się przypisać'
  }
}

const handlePriority = async (priority) => {
  if (!selected.value) return
  const id = selected.value._id || selected.value.id
  try {
    selected.value = await store.update(id, { ...selected.value, priority })
  } catch (e) {
    error.value = 'Nie udało się zmienić priorytetu'
  }
}

const handleDelete = async (id) => {
  if (!confirm('Usunąć tę wiadomość?')) return
  try {
    await store.remove(id)
    selected.value = null
  } catch (e) {
    error.value = 'Nie udało się usunąć'
  }
}

const truncate = (str, len) => str.length > len ? str.slice(0, len) + '...' : str

const timeAgo = (dateStr) => {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'właśnie'
  if (mins < 60) return `${mins} min temu`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} godz. temu`
  const days = Math.floor(hours / 24)
  return `${days} dni temu`
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
