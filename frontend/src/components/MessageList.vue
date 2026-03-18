<template>
  <div class="message-list">
    <div class="controls">
      <button @click="showCreateForm = !showCreateForm" class="btn btn-primary">
        {{ showCreateForm ? 'Cancel' : 'New Message' }}
      </button>
      <button @click="fetchMessages" class="btn btn-secondary">Refresh</button>
    </div>

    <div v-if="showCreateForm" class="message-form">
      <h2>Create New Message</h2>
      <form @submit.prevent="createMessage">
        <div class="form-group">
          <label>Type:</label>
          <select v-model="newMessage.type" required>
            <option value="email">Email</option>
            <option value="sms">SMS</option>
            <option value="voice">Voice</option>
          </select>
        </div>
        <div class="form-group">
          <label>Sender:</label>
          <input v-model="newMessage.sender" type="text" required />
        </div>
        <div class="form-group">
          <label>Content:</label>
          <textarea v-model="newMessage.content" required rows="4"></textarea>
        </div>
        <div class="form-group">
          <label>Priority:</label>
          <select v-model="newMessage.priority">
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>
        <div class="form-group">
          <label>Follow-up Count:</label>
          <input v-model.number="newMessage.followup_count" type="number" min="0" />
        </div>
        <button type="submit" class="btn btn-primary">Create</button>
      </form>
    </div>

    <div v-if="loading" class="loading">Loading messages...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="messages.length === 0" class="empty">No messages yet</div>
    <div v-else class="messages">
      <div
        v-for="message in messages"
        :key="message.id || message._id"
        class="message-card"
        :class="`priority-${message.priority}`"
      >
        <div class="message-header">
          <span class="message-type">{{ message.type.toUpperCase() }}</span>
          <span class="message-priority">{{ message.priority.toUpperCase() }}</span>
        </div>
        <div class="message-body">
          <p class="sender"><strong>From:</strong> {{ message.sender }}</p>
          <p class="content">{{ message.content }}</p>
          <p class="meta">
            <span>Follow-ups: {{ message.followup_count }}</span>
            <span v-if="message.assigned_to">Assigned to: {{ message.assigned_to }}</span>
          </p>
          <p class="timestamp">{{ formatDate(message.created_at) }}</p>
        </div>
        <div class="message-actions">
          <button @click="deleteMessage(message.id || message._id)" class="btn btn-danger btn-sm">
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const messages = ref([])
const loading = ref(false)
const error = ref(null)
const showCreateForm = ref(false)

const newMessage = ref({
  type: 'email',
  sender: '',
  content: '',
  priority: 'medium',
  followup_count: 0
})

const fetchMessages = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await axios.get(`${API_URL}/api/messages`)
    messages.value = response.data
  } catch (err) {
    error.value = 'Failed to fetch messages: ' + err.message
  } finally {
    loading.value = false
  }
}

const createMessage = async () => {
  try {
    await axios.post(`${API_URL}/api/messages`, newMessage.value)
    showCreateForm.value = false
    newMessage.value = {
      type: 'email',
      sender: '',
      content: '',
      priority: 'medium',
      followup_count: 0
    }
    await fetchMessages()
  } catch (err) {
    error.value = 'Failed to create message: ' + err.message
  }
}

const deleteMessage = async (id) => {
  if (!confirm('Are you sure you want to delete this message?')) return

  try {
    await axios.delete(`${API_URL}/api/messages/${id}`)
    await fetchMessages()
  } catch (err) {
    error.value = 'Failed to delete message: ' + err.message
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString()
}

onMounted(() => {
  fetchMessages()
})
</script>

<style scoped>
.message-list {
  width: 100%;
}

.controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #667eea;
  color: white;
}

.btn-primary:hover {
  background-color: #5568d3;
}

.btn-secondary {
  background-color: #e2e8f0;
  color: #334155;
}

.btn-secondary:hover {
  background-color: #cbd5e1;
}

.btn-danger {
  background-color: #ef4444;
  color: white;
}

.btn-danger:hover {
  background-color: #dc2626;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.message-form {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.message-form h2 {
  margin-bottom: 1.5rem;
  color: #334155;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #475569;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
}

.loading, .error, .empty {
  text-align: center;
  padding: 2rem;
  font-size: 1.1rem;
}

.error {
  color: #ef4444;
  background: #fee;
  border-radius: 8px;
}

.messages {
  display: grid;
  gap: 1rem;
}

.message-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border-left: 4px solid #94a3b8;
  transition: transform 0.2s;
}

.message-card:hover {
  transform: translateX(4px);
}

.message-card.priority-urgent {
  border-left-color: #ef4444;
}

.message-card.priority-high {
  border-left-color: #f59e0b;
}

.message-card.priority-medium {
  border-left-color: #3b82f6;
}

.message-card.priority-low {
  border-left-color: #94a3b8;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.message-type {
  background: #e2e8f0;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
}

.message-priority {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
}

.priority-urgent .message-priority {
  background: #ef4444;
}

.priority-high .message-priority {
  background: #f59e0b;
}

.priority-medium .message-priority {
  background: #3b82f6;
}

.priority-low .message-priority {
  background: #94a3b8;
}

.message-body {
  margin-bottom: 1rem;
}

.sender {
  margin-bottom: 0.5rem;
  color: #334155;
}

.content {
  margin-bottom: 0.75rem;
  color: #475569;
  line-height: 1.6;
}

.meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.timestamp {
  font-size: 0.875rem;
  color: #94a3b8;
}

.message-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}
</style>
