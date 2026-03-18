<template>
  <div class="rules-page">
    <div class="page-header">
      <div class="header-row">
        <div>
          <h1 class="page-title">Reguły</h1>
          <p class="page-subtitle">Zarządzaj regułami eskalacji i automatyzacji</p>
        </div>
        <button class="btn btn-primary" @click="showForm = !showForm">
          {{ showForm ? 'Anuluj' : '+ Nowa reguła' }}
        </button>
      </div>
    </div>

    <!-- Create / edit form -->
    <div v-if="showForm" class="rule-form card">
      <h3 class="form-title">{{ editing ? 'Edytuj regułę' : 'Utwórz regułę' }}</h3>
      <div class="form-grid">
        <div class="form-field span-2">
          <label>Nazwa reguły</label>
          <input v-model="form.name" placeholder="np. Auto-eskalacja powtarzających się skarg" />
        </div>
        <div class="form-field span-2">
          <label>Opis</label>
          <input v-model="form.description" placeholder="Co robi ta reguła..." />
        </div>

        <div class="form-section-label">Gdy...</div>
        <div class="form-field">
          <label>Pole</label>
          <select v-model="form.condition_field">
            <option value="followup_count">Liczba ponowień</option>
            <option value="priority">Priorytet</option>
            <option value="type">Typ kanału</option>
            <option value="content">Treść</option>
            <option value="sender">Nadawca</option>
          </select>
        </div>
        <div class="form-field">
          <label>Operator</label>
          <select v-model="form.condition_operator">
            <option value="gte">>=</option>
            <option value="lte">&lt;=</option>
            <option value="eq">równa się</option>
            <option value="contains">zawiera</option>
          </select>
        </div>
        <div class="form-field">
          <label>Wartość</label>
          <input v-model="form.condition_value" placeholder="np. 3, urgent, woda" />
        </div>

        <div class="form-section-label">Wtedy...</div>
        <div class="form-field">
          <label>Akcja</label>
          <select v-model="form.action">
            <option value="set_priority">Ustaw priorytet</option>
            <option value="assign_to">Przypisz do</option>
            <option value="notify_admin">Powiadom admina</option>
            <option value="auto_respond">Automatyczna odpowiedź</option>
          </select>
        </div>
        <div class="form-field span-2">
          <label>Wartość akcji</label>
          <input v-model="form.action_value" :placeholder="actionPlaceholder" />
        </div>

        <div class="form-field">
          <label>Status</label>
          <label class="toggle-label">
            <input type="checkbox" v-model="form.enabled" class="toggle-input" />
            <span class="toggle-switch"></span>
            <span>{{ form.enabled ? 'Aktywna' : 'Wyłączona' }}</span>
          </label>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn" @click="cancelForm">Anuluj</button>
        <button class="btn btn-primary" @click="saveRule" :disabled="!form.name || !form.condition_value || !form.action_value">
          {{ editing ? 'Zapisz' : 'Utwórz' }}
        </button>
      </div>
    </div>

    <!-- Default rules info -->
    <div class="built-in card">
      <h3 class="section-title">Wbudowane reguły</h3>
      <div class="built-in-rule">
        <div class="rule-indicator active"></div>
        <div>
          <span class="rule-name">Auto-eskalacja przy ponowieniach</span>
          <p class="rule-desc">Wiadomości z liczbą ponowień >= 3 są automatycznie eskalowane do priorytetu PILNE</p>
        </div>
        <span class="badge badge-urgent">Zawsze aktywna</span>
      </div>
    </div>

    <!-- Custom rules -->
    <div class="section-header">
      <h3 class="section-title">Własne reguły</h3>
      <span class="rule-count">{{ rules.length }} {{ rules.length === 1 ? 'reguła' : 'reguł' }}</span>
    </div>

    <div v-if="rules.length === 0" class="empty-state card" style="padding: 32px;">
      <p>Brak własnych reguł. Utwórz regułę, aby zautomatyzować obsługę zgłoszeń.</p>
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
            <button class="btn btn-sm" @click="editRule(rule)">Edytuj</button>
            <button class="btn btn-sm btn-danger" @click="handleDelete(rule._id || rule.id)">Usuń</button>
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
    set_priority: 'np. urgent, high',
    assign_to: 'np. jan.kowalski',
    notify_admin: 'np. admin@nava.pl',
    auto_respond: 'Treść odpowiedzi...',
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
  if (!confirm('Usunąć tę regułę?')) return
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

const operatorLabel = (op) => ({ gte: '>=', lte: '<=', eq: '=', contains: 'zawiera' }[op] || op)
const actionLabel = (a) => ({ set_priority: 'Ustaw priorytet', assign_to: 'Przypisz do', notify_admin: 'Powiadom admina', auto_respond: 'Auto-odpowiedź' }[a] || a)

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
