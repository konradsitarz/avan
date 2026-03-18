<template>
  <div class="respond-page">
    <div class="page-header">
      <h1 class="page-title">Odpowiedzi</h1>
      <p class="page-subtitle">Twórz i wysyłaj odpowiedzi na zgłoszenia</p>
    </div>

    <div class="respond-layout">
      <div class="respond-inbox">
        <div class="inbox-header">
          <span class="inbox-title">Skrzynka</span>
          <select v-model="channelFilter" class="channel-select">
            <option value="">Wszystkie kanały</option>
            <option value="email">Email</option>
            <option value="sms">SMS</option>
            <option value="voice">Telefon</option>
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
              <span class="badge" :class="`badge-${msg.type}`">{{ label(channelLabels, msg.type) }}</span>
            </div>
            <p class="inbox-preview">{{ truncate(msg.content, 80) }}</p>
          </div>
          <div v-if="filteredMessages.length === 0" class="empty-state">
            <p>Brak wiadomości</p>
          </div>
        </div>
      </div>

      <div class="respond-compose card" v-if="selected">
        <div class="compose-original">
          <div class="compose-original-header">
            <span class="compose-label">Oryginalna wiadomość</span>
            <span class="badge" :class="`badge-${selected.priority}`">{{ label(priorityLabels, selected.priority) }}</span>
          </div>
          <div class="original-from">
            <label>Od</label>
            <span>{{ selected.sender }}</span>
          </div>
          <div class="original-content">
            <p>{{ selected.content }}</p>
          </div>
          <div class="original-meta">
            <span>{{ formatDate(selected.created_at) }}</span>
            <span v-if="selected.followup_count > 0">{{ selected.followup_count }} ponowień</span>
          </div>
        </div>

        <div class="compose-divider"></div>

        <div class="compose-form">
          <div class="compose-to">
            <label>Do</label>
            <input :value="selected.sender" disabled />
          </div>
          <div class="compose-channel">
            <label>Odpowiedz przez</label>
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
            <label>Odpowiedź</label>
            <span v-if="selected.draft_response" class="draft-label">Wersja robocza wygenerowana przez AI</span>
            <textarea
              v-model="replyText"
              rows="6"
              placeholder="Wpisz odpowiedź..."
            ></textarea>
          </div>
          <div class="compose-generate">
            <label>Wygeneruj odpowiedź AI</label>
            <div class="generate-chips">
              <button class="chip" :class="{ loading: generating }" :disabled="generating" @click="generateDraft(null)">Automatyczna</button>
              <button class="chip" :class="{ loading: generating }" :disabled="generating" @click="generateDraft('ack')">Potwierdzenie</button>
              <button class="chip" :class="{ loading: generating }" :disabled="generating" @click="generateDraft('escalate')">Eskalacja</button>
              <button class="chip" :class="{ loading: generating }" :disabled="generating" @click="generateDraft('resolved')">Rozwiązano</button>
              <button class="chip" :class="{ loading: generating }" :disabled="generating" @click="generateDraft('info')">Prośba o info</button>
            </div>
            <span v-if="generating" class="generating-label">Generowanie...</span>
            <span v-if="generateError" class="generate-error">{{ generateError }}</span>
          </div>
          <div class="compose-actions">
            <button class="btn" @click="clear">Anuluj</button>
            <button class="btn btn-primary" @click="sendReply" :disabled="!replyText.trim()">
              Wyślij odpowiedź
            </button>
          </div>
        </div>
      </div>

      <div class="respond-compose card empty-detail" v-else>
        <p class="empty-state">Wybierz wiadomość, aby odpowiedzieć</p>
      </div>
    </div>

    <div v-if="sent" class="toast">Odpowiedź wysłana (symulacja)</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getMessages, generateReply } from '../api.js'
import { priorityLabels, channelLabels, label } from '../labels.js'

const route = useRoute()

const messages = ref([])
const selected = ref(null)
const replyText = ref('')
const replyChannel = ref('email')
const channelFilter = ref('')
const sent = ref(false)
const generating = ref(false)
const generateError = ref('')

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
  replyText.value = msg.draft_response || ''
  replyChannel.value = msg.type === 'voice' ? 'sms' : msg.type
}

const generateDraft = async (tone) => {
  if (!selected.value) return
  generating.value = true
  generateError.value = ''
  try {
    const id = selected.value._id || selected.value.id
    const result = await generateReply(id, tone)
    replyText.value = result.draft
  } catch (e) {
    generateError.value = e.response?.status === 503
      ? 'LLM niedostępny — brak klucza API'
      : 'Nie udało się wygenerować odpowiedzi'
  } finally {
    generating.value = false
  }
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
  try {
    messages.value = await getMessages()
    const messageId = route.query.message
    if (messageId) {
      const msg = messages.value.find(m => (m._id || m.id) === messageId)
      if (msg) selectMessage(msg)
    }
  } catch (e) { /* ignore */ }
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

.draft-label {
  display: inline-block;
  font-size: 11px;
  color: var(--success);
  font-weight: 600;
  margin-bottom: 4px;
  padding: 2px 8px;
  background: rgba(63, 185, 80, 0.1);
  border-radius: 4px;
}

.generate-chips {
  display: flex;
  gap: 6px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.generating-label {
  display: inline-block;
  margin-top: 6px;
  font-size: 11px;
  color: var(--accent);
  font-weight: 600;
}

.generate-error {
  display: inline-block;
  margin-top: 6px;
  font-size: 11px;
  color: var(--urgent);
  font-weight: 600;
}

.chip.loading {
  opacity: 0.5;
  cursor: wait;
}

.compose-body textarea {
  resize: vertical;
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
