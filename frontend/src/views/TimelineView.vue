<template>
  <div class="timeline-page">
    <div class="page-header">
      <h1 class="page-title">Oś czasu</h1>
      <p class="page-subtitle">Chronologiczna historia wiadomości pogrupowana wg nadawcy</p>
    </div>

    <div class="timeline-controls">
      <input v-model="search" placeholder="Filtruj po nadawcy..." class="search-input" />
      <select v-model="groupBy">
        <option value="sender">Grupuj wg nadawcy</option>
        <option value="date">Grupuj wg daty</option>
        <option value="none">Bez grupowania</option>
      </select>
    </div>

    <div v-if="loading" class="empty-state">Ładowanie...</div>
    <div v-else-if="groupBy === 'none'">
      <div class="timeline-track">
        <div v-for="msg in flatFiltered" :key="msg._id || msg.id" class="timeline-entry">
          <div class="timeline-marker">
            <div class="marker-dot" :class="`dot-${msg.priority}`"></div>
            <div class="marker-line"></div>
          </div>
          <div class="timeline-card card">
            <div class="tc-header">
              <span class="tc-sender">{{ msg.sender }}</span>
              <div class="tc-badges">
                <span class="badge" :class="`badge-${msg.type}`">{{ label(channelLabels, msg.type) }}</span>
                <span class="badge" :class="`badge-${msg.priority}`">{{ label(priorityLabels, msg.priority) }}</span>
              </div>
            </div>
            <p class="tc-content">{{ msg.content }}</p>
            <span class="tc-time">{{ formatDate(msg.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="groupBy === 'sender'">
      <div v-for="group in senderGroups" :key="group.key" class="timeline-group">
        <div class="group-header" @click="group.open = !group.open">
          <span class="group-toggle">{{ group.open ? '\u25BC' : '\u25B6' }}</span>
          <span class="group-name">{{ group.key }}</span>
          <span class="group-count">{{ group.messages.length }} {{ group.messages.length > 1 ? 'wiadomości' : 'wiadomość' }}</span>
          <span class="badge" :class="`badge-${group.maxPriority}`">{{ label(priorityLabels, group.maxPriority) }}</span>
        </div>
        <div v-if="group.open" class="timeline-track">
          <div v-for="msg in group.messages" :key="msg._id || msg.id" class="timeline-entry">
            <div class="timeline-marker">
              <div class="marker-dot" :class="`dot-${msg.priority}`"></div>
              <div class="marker-line"></div>
            </div>
            <div class="timeline-card card">
              <div class="tc-header">
                <div class="tc-badges">
                  <span class="badge" :class="`badge-${msg.type}`">{{ label(channelLabels, msg.type) }}</span>
                  <span class="badge" :class="`badge-${msg.priority}`">{{ label(priorityLabels, msg.priority) }}</span>
                </div>
              </div>
              <p class="tc-content">{{ msg.content }}</p>
              <span class="tc-time">{{ formatDate(msg.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else>
      <div v-for="group in dateGroups" :key="group.key" class="timeline-group">
        <div class="group-header">
          <span class="group-name">{{ group.key }}</span>
          <span class="group-count">{{ group.messages.length }} {{ group.messages.length > 1 ? 'wiadomości' : 'wiadomość' }}</span>
        </div>
        <div class="timeline-track">
          <div v-for="msg in group.messages" :key="msg._id || msg.id" class="timeline-entry">
            <div class="timeline-marker">
              <div class="marker-dot" :class="`dot-${msg.priority}`"></div>
              <div class="marker-line"></div>
            </div>
            <div class="timeline-card card">
              <div class="tc-header">
                <span class="tc-sender">{{ msg.sender }}</span>
                <div class="tc-badges">
                  <span class="badge" :class="`badge-${msg.type}`">{{ label(channelLabels, msg.type) }}</span>
                  <span class="badge" :class="`badge-${msg.priority}`">{{ label(priorityLabels, msg.priority) }}</span>
                </div>
              </div>
              <p class="tc-content">{{ msg.content }}</p>
              <span class="tc-time">{{ formatTime(msg.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { getMessages } from '../api.js'
import { priorityLabels, channelLabels, label } from '../labels.js'

const messages = ref([])
const loading = ref(false)
const search = ref('')
const groupBy = ref('sender')

const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 }

const filtered = computed(() => {
  let list = [...messages.value]
  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter(m => m.sender.toLowerCase().includes(q) || m.content.toLowerCase().includes(q))
  }
  list.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  return list
})

const flatFiltered = computed(() => filtered.value)

const senderGroups = computed(() => {
  const map = {}
  for (const msg of filtered.value) {
    if (!map[msg.sender]) map[msg.sender] = { key: msg.sender, messages: [], open: true, maxPriority: 'low' }
    map[msg.sender].messages.push(msg)
    if (priorityOrder[msg.priority] < priorityOrder[map[msg.sender].maxPriority]) {
      map[msg.sender].maxPriority = msg.priority
    }
  }
  const groups = Object.values(map)
  groups.sort((a, b) => priorityOrder[a.maxPriority] - priorityOrder[b.maxPriority])
  // Make groups reactive for toggle
  return groups.map(g => reactive(g))
})

const dateGroups = computed(() => {
  const map = {}
  for (const msg of filtered.value) {
    const dateKey = new Date(msg.created_at).toLocaleDateString()
    if (!map[dateKey]) map[dateKey] = { key: dateKey, messages: [] }
    map[dateKey].messages.push(msg)
  }
  return Object.values(map)
})

const fetchMessages = async () => {
  loading.value = true
  try {
    messages.value = await getMessages()
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

const formatDate = (d) => new Date(d).toLocaleString()
const formatTime = (d) => new Date(d).toLocaleTimeString()

onMounted(fetchMessages)
</script>

<style scoped>
.timeline-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}

.search-input {
  flex: 1;
  max-width: 320px;
}

.timeline-controls select {
  width: auto;
  min-width: 160px;
}

.timeline-group {
  margin-bottom: 8px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  margin-bottom: 4px;
  cursor: pointer;
  font-size: 14px;
}

.group-toggle {
  font-size: 10px;
  color: var(--text-muted);
  width: 14px;
}

.group-name {
  font-weight: 600;
  color: var(--text-primary);
}

.group-count {
  color: var(--text-muted);
  font-size: 12px;
  margin-left: auto;
  margin-right: 8px;
}

.timeline-track {
  padding-left: 16px;
  margin-bottom: 16px;
}

.timeline-entry {
  display: flex;
  gap: 12px;
}

.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 16px;
}

.marker-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-urgent { background: var(--urgent); box-shadow: 0 0 6px var(--urgent); }
.dot-high { background: var(--high); }
.dot-medium { background: var(--medium); }
.dot-low { background: var(--low); }

.marker-line {
  width: 2px;
  flex: 1;
  background: var(--border);
  min-height: 12px;
}

.timeline-entry:last-child .marker-line {
  display: none;
}

.timeline-card {
  flex: 1;
  padding: 12px 16px;
  margin-bottom: 6px;
}

.tc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.tc-sender {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

.tc-badges {
  display: flex;
  gap: 4px;
}

.tc-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  margin-bottom: 6px;
}

.tc-time {
  font-size: 11px;
  color: var(--text-muted);
}
</style>
