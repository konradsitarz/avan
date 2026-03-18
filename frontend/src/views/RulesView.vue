<template>
  <div class="rules-page">
    <div class="page-header">
      <div class="header-row">
        <div>
          <h1 class="page-title">System Learning</h1>
          <p class="page-subtitle">Manage escalation rules and automation</p>
        </div>
        <button class="btn btn-primary" @click="showForm = !showForm">
          {{ showForm ? 'Cancel' : '+ New Rule' }}
        </button>
      </div>
    </div>

    <!-- Create / edit form -->
    <div v-if="showForm" class="rule-form card">
      <h3 class="form-title">{{ editing ? 'Edit Rule' : 'Create Rule' }}</h3>
      <div class="form-grid">
        <div class="form-field span-2">
          <label>Rule name</label>
          <input v-model="form.name" placeholder="e.g. Auto-escalate repeat complaints" />
        </div>
        <div class="form-field span-2">
          <label>Description</label>
          <input v-model="form.description" placeholder="What this rule does..." />
        </div>

        <div class="form-section-label">When...</div>
        <div class="form-field">
          <label>Field</label>
          <select v-model="form.condition_field">
            <option value="followup_count">Follow-up count</option>
            <option value="priority">Priority</option>
            <option value="type">Channel type</option>
            <option value="content">Content</option>
            <option value="sender">Sender</option>
          </select>
        </div>
        <div class="form-field">
          <label>Operator</label>
          <select v-model="form.condition_operator">
            <option value="gte">>=</option>
            <option value="lte">&lt;=</option>
            <option value="eq">equals</option>
            <option value="contains">contains</option>
          </select>
        </div>
        <div class="form-field">
          <label>Value</label>
          <input v-model="form.condition_value" placeholder="e.g. 3, urgent, water" />
        </div>

        <div class="form-section-label">Then...</div>
        <div class="form-field">
          <label>Action</label>
          <select v-model="form.action">
            <option value="set_priority">Set priority</option>
            <option value="assign_to">Assign to</option>
            <option value="notify_admin">Notify admin</option>
            <option value="auto_respond">Auto-respond</option>
          </select>
        </div>
        <div class="form-field span-2">
          <label>Action value</label>
          <input v-model="form.action_value" :placeholder="actionPlaceholder" />
        </div>

        <div class="form-field">
          <label>Enabled</label>
          <label class="toggle-label">
            <input type="checkbox" v-model="form.enabled" class="toggle-input" />
            <span class="toggle-switch"></span>
            <span>{{ form.enabled ? 'Active' : 'Disabled' }}</span>
          </label>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn" @click="cancelForm">Cancel</button>
        <button class="btn btn-primary" @click="saveRule" :disabled="!form.name || !form.condition_value || !form.action_value">
          {{ editing ? 'Update' : 'Create' }}
        </button>
      </div>
    </div>

    <!-- Default rules info -->
    <div class="built-in card">
      <h3 class="section-title">Built-in Rules</h3>
      <div class="built-in-rule">
        <div class="rule-indicator active"></div>
        <div>
          <span class="rule-name">Auto-escalation on follow-ups</span>
          <p class="rule-desc">Messages with follow_up count >= 3 are automatically escalated to URGENT priority</p>
        </div>
        <span class="badge badge-urgent">Always active</span>
      </div>
    </div>

    <!-- Custom rules -->
    <div class="section-header">
      <h3 class="section-title">Custom Rules</h3>
      <span class="rule-count">{{ rules.length }} rule{{ rules.length !== 1 ? 's' : '' }}</span>
    </div>

    <div v-if="rules.length === 0" class="empty-state card" style="padding: 32px;">
      <p>No custom rules yet. Create one to automate message handling.</p>
    </div>

    <div v-else class="rules-list">
      <div v-for="rule in rules" :key="rule._id || rule.id" class="rule-card card">
        <div class="rule-card-header">
          <div class="rule-indicator" :class="{ active: rule.enabled }"></div>
          <div class="rule-info">
            <span class="rule-name">{{ rule.name }}</span>
            <p class="rule-desc">{{ rule.description }}</p>
          </div>
          <div class="rule-actions">
            <button class="btn btn-sm" @click="editRule(rule)">Edit</button>
            <button class="btn btn-sm btn-danger" @click="handleDelete(rule._id || rule.id)">Delete</button>
          </div>
        </div>
        <div class="rule-logic">
          <div class="rule-condition">
            <span class="logic-label">WHEN</span>
            <code>{{ rule.condition_field }}</code>
            <span class="logic-op">{{ operatorLabel(rule.condition_operator) }}</span>
            <code>{{ rule.condition_value }}</code>
          </div>
          <span class="logic-arrow">&rarr;</span>
          <div class="rule-action">
            <span class="logic-label">THEN</span>
            <code>{{ actionLabel(rule.action) }}</code>
            <span class="logic-value">{{ rule.action_value }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getRules, createRule, updateRule, deleteRule } from '../api.js'

const rules = ref([])
const showForm = ref(false)
const editing = ref(null)

const emptyForm = () => ({
  name: '',
  description: '',
  condition_field: 'followup_count',
  condition_operator: 'gte',
  condition_value: '',
  action: 'set_priority',
  action_value: '',
  enabled: true,
})

const form = ref(emptyForm())

const actionPlaceholder = computed(() => {
  const map = {
    set_priority: 'e.g. urgent, high',
    assign_to: 'e.g. jan.kowalski',
    notify_admin: 'e.g. admin@nava.pl',
    auto_respond: 'Response text...',
  }
  return map[form.value.action] || ''
})

const fetchRules = async () => {
  try { rules.value = await getRules() } catch (e) { /* ignore */ }
}

const saveRule = async () => {
  try {
    if (editing.value) {
      await updateRule(editing.value, form.value)
    } else {
      await createRule(form.value)
    }
    cancelForm()
    await fetchRules()
  } catch (e) { /* ignore */ }
}

const editRule = (rule) => {
  editing.value = rule._id || rule.id
  form.value = { ...rule }
  showForm.value = true
}

const handleDelete = async (id) => {
  if (!confirm('Delete this rule?')) return
  try {
    await deleteRule(id)
    await fetchRules()
  } catch (e) { /* ignore */ }
}

const cancelForm = () => {
  showForm.value = false
  editing.value = null
  form.value = emptyForm()
}

const operatorLabel = (op) => ({ gte: '>=', lte: '<=', eq: '=', contains: 'contains' }[op] || op)
const actionLabel = (a) => ({ set_priority: 'Set priority', assign_to: 'Assign to', notify_admin: 'Notify admin', auto_respond: 'Auto-respond' }[a] || a)

onMounted(fetchRules)
</script>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.built-in {
  padding: 16px;
  margin-bottom: 24px;
}

.built-in-rule {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.rule-count {
  font-size: 12px;
  color: var(--text-muted);
}

/* Rule form */
.rule-form {
  padding: 20px;
  margin-bottom: 24px;
}

.form-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
}

.span-2 { grid-column: span 2; }

.form-section-label {
  grid-column: span 3;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* Toggle switch */
.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  text-transform: none;
  font-weight: 400;
  font-size: 13px;
}

.toggle-input {
  display: none;
}

.toggle-switch {
  width: 36px;
  height: 20px;
  background: var(--border);
  border-radius: 10px;
  position: relative;
  transition: background 0.2s;
}

.toggle-switch::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.toggle-input:checked + .toggle-switch {
  background: var(--accent);
}

.toggle-input:checked + .toggle-switch::after {
  transform: translateX(16px);
}

/* Rule cards */
.rules-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-card {
  padding: 16px;
}

.rule-card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.rule-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  margin-top: 6px;
  flex-shrink: 0;
}

.rule-indicator.active {
  background: var(--success);
  box-shadow: 0 0 6px var(--success);
}

.rule-info {
  flex: 1;
}

.rule-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.rule-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.rule-actions {
  display: flex;
  gap: 6px;
}

.rule-logic {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg-primary);
  border-radius: 6px;
  font-size: 13px;
}

.rule-condition, .rule-action {
  display: flex;
  align-items: center;
  gap: 6px;
}

.logic-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.logic-op {
  color: var(--accent);
  font-weight: 600;
}

.logic-arrow {
  color: var(--text-muted);
  font-size: 16px;
}

.logic-value {
  color: var(--success);
  font-weight: 500;
}

code {
  background: rgba(88,166,255,0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  color: var(--accent);
}
</style>
