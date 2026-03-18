<template>
  <div class="respond-page">
    <div class="page-header">
      <h1 class="page-title">Respond</h1>
      <p class="page-subtitle">Draft and send responses to messages</p>
    </div>

    <div class="respond-layout">
      <div class="respond-inbox">
        <div class="inbox-header">
          <span class="inbox-title">Inbox</span>
          <select v-model="channelFilter" class="channel-select">
            <option value="">All channels</option>
            <option value="email">Email</option>
            <option value="sms">SMS</option>
            <option value="voice">Voice</option>
          </select>
        </div>
        <div class="inbox-list">
          <div
            v-for="msg in filteredMessages"
            :key="msg._id || msg.id"
            class="inbox-item"
            :class="{ selected: selected?._id === msg._id }"
            @click="selectMessage(msg)"
          >
            <div class="inbox-item-row">
              <div class="priority-dot" :class="`dot-${msg.priority}`"></div>
              <span class="inbox-sender">{{ msg.sender }}</span>
              <span class="badge" :class="`badge-${msg.type}`">{{ msg.type }}</span>
            </div>
            <p class="inbox-preview">{{ truncate(msg.content, 80) }}</p>
          </div>
          <div v-if="filteredMessages.length === 0" class="empty-state">
            <p>No messages</p>
          </div>
        </div>
      </div>

      <div class="respond-compose card" v-if="selected">
        <div class="compose-original">
          <div class="compose-original-header">
            <span class="compose-label">Original message</span>
            <span class="badge" :class="`badge-${selected.priority}`">{{ selected.priority }}</span>
          </div>
          <div class="original-from">
            <label>From</label>
            <span>{{ selected.sender }}</span>
          </div>
          <div class="original-content">
            <p>{{ selected.content }}</p>
          </div>
          <div class="original-meta">
            <span>{{ formatDate(selected.created_at) }}</span>
            <span v-if="selected.followup_count > 0">{{ selected.followup_count }} follow-up(s)</span>
          </div>
        </div>

        <div class="compose-divider"></div>

        <div class="compose-form">
          <div class="compose-to">
            <label>To</label>
            <input :value="selected.sender" disabled />
          </div>
          <div class="compose-channel">
            <label>Reply via</label>
            <div class="channel-options">
              <button
                v-for="ch in replyChannels"
                :key="ch"
                class="btn btn-sm"
                :class="{ 'btn-primary': replyChannel === ch }"
                @click="replyChannel = ch"
              >{{ ch }}</button>
            </div>
          </div>
          <div class="compose-body">
            <label>Response</label>
            <textarea
              v-model="replyText"
              rows="6"
              placeholder="Type your response..."
            ></textarea>
          </div>
          <div class="compose-templates">
            <label>Quick templates</label>
            <div class="template-chips">
              <button class="chip" @click="applyTemplate('ack')">Acknowledge</button>
              <button class="chip" @click="applyTemplate('escalate')">Escalate</button>
              <button class="chip" @click="applyTemplate('resolved')">Mark resolved</button>
              <button class="chip" @click="applyTemplate('info')">Request info</button>
            </div>
          </div>
          <div class="compose-actions">
            <button class="btn" @click="clear">Cancel</button>
            <button class="btn btn-primary" @click="sendReply" :disabled="!replyText.trim()">
              Send Response
            </button>
          </div>
        </div>
      </div>

      <div class="respond-compose card empty-detail" v-else>
        <p class="empty-state">Select a message to respond</p>
      </div>
    </div>

    <div v-if="sent" class="toast">Response sent (simulated)</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getMessages } from '../api.js'

const messages = ref([])
const selected = ref(null)
const replyText = ref('')
const replyChannel = ref('email')
const channelFilter = ref('')
const sent = ref(false)

const priorityOrder = { urgent: 0, high: 1, medium: 2, low: 3 }

const filteredMessages = computed(() => {
  let list = [...messages.value]
  if (channelFilter.value) list = list.filter(m => m.type === channelFilter.value)
  list.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority])
  return list
})

const replyChannels = computed(() => {
  if (!selected.value) return ['email', 'sms']
  if (selected.value.type === 'voice') return ['email', 'sms']
  return [selected.value.type]
})

const selectMessage = (msg) => {
  selected.value = msg
  replyText.value = ''
  replyChannel.value = msg.type === 'voice' ? 'sms' : msg.type
}

const templates = {
  ack: 'Dziękujemy za zgłoszenie. Sprawa została zarejestrowana i zajmiemy się nią niezwłocznie.',
  escalate: 'Pani/Pana zgłoszenie zostało eskalowane do wyższego priorytetu. Skontaktujemy się w ciągu 24 godzin.',
  resolved: 'Informujemy, że zgłoszona sprawa została rozwiązana. W razie dalszych problemów prosimy o kontakt.',
  info: 'W celu dalszego procedowania prosimy o podanie dodatkowych szczegółów dotyczących zgłoszenia.',
}

const applyTemplate = (key) => {
  replyText.value = templates[key]
}

const sendReply = () => {
  if (!replyText.value.trim()) return
  sent.value = true
  replyText.value = ''
  selected.value = null
  setTimeout(() => { sent.value = false }, 3000)
}

const clear = () => {
  replyText.value = ''
  selected.value = null
}

const truncate = (str, len) => str.length > len ? str.slice(0, len) + '...' : str
const formatDate = (d) => new Date(d).toLocaleString()

const fetchMessages = async () => {
  try { messages.value = await getMessages() } catch (e) { /* ignore */ }
}

onMounted(fetchMessages)
</script>

<style scoped>
.respond-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 16px;
  align-items: start;
}

.respond-inbox {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.inbox-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
}

.inbox-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.channel-select {
  width: auto;
  min-width: 100px;
  font-size: 12px;
  padding: 4px 8px;
}

.inbox-list {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.inbox-item {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.1s;
}

.inbox-item:hover {
  background: var(--bg-hover);
}

.inbox-item.selected {
  background: rgba(88,166,255,0.08);
  border-left: 2px solid var(--accent);
}

.inbox-item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.priority-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-urgent { background: var(--urgent); }
.dot-high { background: var(--high); }
.dot-medium { background: var(--medium); }
.dot-low { background: var(--low); }

.inbox-sender {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
  flex: 1;
}

.inbox-preview {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
}

.respond-compose {
  padding: 20px;
}

.empty-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.compose-original {
  margin-bottom: 16px;
}

.compose-original-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.compose-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.original-from {
  margin-bottom: 8px;
}

.original-from label {
  display: inline;
  margin-right: 8px;
}

.original-from span {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.original-content {
  background: var(--bg-primary);
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.original-content p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.original-meta {
  display: flex;
  gap: 16px;
  font-size: 11px;
  color: var(--text-muted);
}

.compose-divider {
  height: 1px;
  background: var(--border);
  margin: 16px 0;
}

.compose-form > div {
  margin-bottom: 14px;
}

.compose-to input {
  background: var(--bg-secondary);
  color: var(--text-muted);
}

.channel-options {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.compose-body textarea {
  resize: vertical;
}

.template-chips {
  display: flex;
  gap: 6px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.chip {
  padding: 4px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 14px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.chip:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--accent);
}

.compose-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
}

.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: var(--success);
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
