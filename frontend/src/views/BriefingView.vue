<template>
  <div class="briefing">
    <!-- Loading -->
    <div v-if="loading" class="briefing-loading">
      <div class="loading-pulse"></div>
      <p>Preparing your briefing...</p>
    </div>

    <div v-else-if="error" class="empty-state" style="color: var(--urgent)">{{ error }}</div>

    <div v-else-if="briefing" class="briefing-document">

      <!-- PHASE 1: Summary -->
      <div v-if="phase === 'summary'" class="phase-summary">
        <div class="briefing-date">{{ formatDate(briefing.generated_at) }}</div>

        <div class="summary-card">
          <div class="summary-avatar">N</div>
          <div class="summary-body">
            <div class="summary-label">Your Morning Briefing</div>
            <p class="summary-text">{{ briefing.summary }}</p>
          </div>
        </div>

        <div class="stats-row">
          <div class="stat-pill" :class="{ active: briefing.stats.urgent > 0 }">
            <span class="pill-dot dot-urgent"></span>
            <span>{{ briefing.stats.urgent }} urgent</span>
          </div>
          <div class="stat-pill">
            <span class="pill-dot dot-high"></span>
            <span>{{ briefing.stats.high }} high</span>
          </div>
          <div class="stat-pill">
            <span class="pill-dot dot-medium"></span>
            <span>{{ briefing.stats.medium + briefing.stats.low }} routine</span>
          </div>
          <div class="stat-pill">
            <span>{{ briefing.stats.unassigned }} unassigned</span>
          </div>
        </div>

        <button
          v-if="briefing.issues.length > 0"
          class="btn-begin"
          @click="beginReview"
        >
          Review issues one by one
          <span class="btn-count">{{ briefing.issues.length }}</span>
        </button>
      </div>

      <!-- PHASE 2: Issue-by-issue review -->
      <div v-if="phase === 'review'" class="phase-review">
        <div class="review-nav">
          <button class="btn btn-sm" @click="phase = 'summary'">Back to briefing</button>
          <span class="review-progress">{{ currentIndex + 1 }} of {{ briefing.issues.length }}</span>
          <div class="review-dots">
            <span
              v-for="(issue, idx) in briefing.issues"
              :key="issue.id"
              class="dot"
              :class="[`dot-${issue.priority}`, { current: idx === currentIndex }]"
              @click="currentIndex = idx"
            ></span>
          </div>
        </div>

        <div class="issue-card" v-if="currentIssue">
          <div class="issue-priority-bar" :class="`bar-${currentIssue.priority}`"></div>

          <div class="issue-meta">
            <span class="badge" :class="`badge-${currentIssue.priority}`">{{ currentIssue.priority }}</span>
            <span class="badge badge-category" v-if="currentIssue.category">{{ currentIssue.category }}</span>
            <span class="badge" :class="`badge-${currentIssue.type}`">{{ currentIssue.type }}</span>
            <span class="issue-msg-count" v-if="currentIssue.message_count > 1">
              {{ currentIssue.message_count }} messages
            </span>
            <span class="issue-time">{{ currentIssue.time_label }}</span>
          </div>

          <div class="issue-from">
            <label>From</label>
            <span>{{ currentIssue.sender }}</span>
          </div>

          <!-- LLM Brief — the concierge summary -->
          <div v-if="currentIssue.llm_brief" class="issue-brief">
            <div class="brief-icon">N</div>
            <p>{{ currentIssue.llm_brief }}</p>
          </div>

          <!-- Triage reasoning -->
          <div v-if="currentIssue.action_reason" class="issue-reasoning">
            <label>Triage reasoning</label>
            <p>{{ currentIssue.action_reason }}</p>
          </div>

          <!-- Timeline -->
          <div class="issue-timeline" v-if="currentIssue.timeline && currentIssue.timeline.length > 0">
            <label>Timeline</label>
            <div class="timeline-list">
              <div
                v-for="(entry, idx) in currentIssue.timeline"
                :key="entry.id"
                class="timeline-entry"
              >
                <div class="timeline-dot-line">
                  <div class="timeline-dot" :class="`dot-${entry.priority}`"></div>
                  <div v-if="idx < currentIssue.timeline.length - 1" class="timeline-line"></div>
                </div>
                <div class="timeline-body">
                  <div class="timeline-meta">
                    <span class="badge badge-sm" :class="`badge-${entry.type}`">{{ entry.type }}</span>
                    <span class="timeline-time">{{ entry.time_label }}</span>
                  </div>
                  <p class="timeline-content">{{ entry.content }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="issue-details">
            <div class="detail-item" v-if="currentIssue.followup_count > 0">
              <label>Follow-ups</label>
              <span class="followup-count">{{ currentIssue.followup_count }}x</span>
            </div>
            <div class="detail-item">
              <label>Assigned to</label>
              <span :class="{ unassigned: !currentIssue.assigned_to }">
                {{ currentIssue.assigned_to || 'Nobody' }}
              </span>
            </div>
          </div>

          <!-- Override controls -->
          <div class="issue-override">
            <button class="btn btn-sm" @click="showOverride = !showOverride">
              {{ showOverride ? 'Cancel override' : 'Override triage' }}
            </button>
            <div v-if="showOverride" class="override-form">
              <div class="override-row">
                <label>Priority</label>
                <select v-model="overrideData.priority">
                  <option value="">keep</option>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                  <option value="urgent">urgent</option>
                </select>
              </div>
              <div class="override-row">
                <label>Category</label>
                <select v-model="overrideData.category">
                  <option value="">keep</option>
                  <option value="safety">safety</option>
                  <option value="plumbing">plumbing</option>
                  <option value="electrical">electrical</option>
                  <option value="noise">noise</option>
                  <option value="maintenance">maintenance</option>
                  <option value="billing">billing</option>
                  <option value="access">access</option>
                  <option value="compliance">compliance</option>
                  <option value="other">other</option>
                </select>
              </div>
              <div class="override-row">
                <label>Reason</label>
                <input v-model="overrideData.reason" placeholder="Why are you overriding?" />
              </div>
              <button class="btn btn-primary btn-sm" @click="submitOverride" :disabled="overrideLoading">
                {{ overrideLoading ? 'Saving...' : 'Save override' }}
              </button>
              <span v-if="overrideSaved" class="override-saved">Saved — will improve future triage</span>
            </div>
          </div>

          <!-- Quick actions -->
          <div class="issue-actions">
            <button class="btn btn-sm" @click="prevIssue" :disabled="currentIndex === 0">Previous</button>
            <button
              class="btn btn-primary btn-sm"
              @click="nextIssue"
              v-if="currentIndex < briefing.issues.length - 1"
            >Next issue</button>
            <button
              class="btn btn-primary btn-sm"
              @click="phase = 'done'"
              v-else
            >Finish review</button>
          </div>
        </div>
      </div>

      <!-- PHASE 3: Done -->
      <div v-if="phase === 'done'" class="phase-done">
        <div class="done-card">
          <div class="done-icon">&#10003;</div>
          <h2>Briefing complete</h2>
          <p>You've reviewed all {{ briefing.issues.length }} issues.</p>
          <div class="done-actions">
            <button class="btn" @click="phase = 'summary'">Back to summary</button>
            <router-link to="/feed" class="btn btn-primary">Open full feed</router-link>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { getBriefing, overrideMessage } from '../api.js'

const briefing = ref(null)
const loading = ref(false)
const error = ref(null)
const phase = ref('summary') // summary | review | done
const currentIndex = ref(0)

// Override state
const showOverride = ref(false)
const overrideLoading = ref(false)
const overrideSaved = ref(false)
const overrideData = reactive({
  priority: '',
  category: '',
  reason: '',
})

const currentIssue = computed(() => {
  if (!briefing.value || !briefing.value.issues.length) return null
  return briefing.value.issues[currentIndex.value]
})

const fetchBriefing = async () => {
  loading.value = true
  error.value = null
  try {
    briefing.value = await getBriefing()
  } catch (e) {
    error.value = 'Failed to generate briefing'
  } finally {
    loading.value = false
  }
}

const beginReview = () => {
  currentIndex.value = 0
  phase.value = 'review'
}

const nextIssue = () => {
  if (currentIndex.value < briefing.value.issues.length - 1) {
    currentIndex.value++
  }
}

const prevIssue = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

// Reset override form when switching issues
watch(currentIndex, () => {
  showOverride.value = false
  overrideSaved.value = false
  overrideData.priority = ''
  overrideData.category = ''
  overrideData.reason = ''
})

const submitOverride = async () => {
  if (!currentIssue.value) return
  overrideLoading.value = true
  overrideSaved.value = false
  try {
    const payload = {}
    if (overrideData.priority) payload.priority = overrideData.priority
    if (overrideData.category) payload.category = overrideData.category
    if (overrideData.reason) payload.reason = overrideData.reason
    const updated = await overrideMessage(currentIssue.value.id, payload)
    // Update the issue in place
    if (overrideData.priority) currentIssue.value.priority = overrideData.priority
    if (overrideData.category) currentIssue.value.category = overrideData.category
    overrideSaved.value = true
  } catch (e) {
    // ignore
  } finally {
    overrideLoading.value = false
  }
}

const formatDate = (dateStr) => {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

onMounted(fetchBriefing)
</script>

<style scoped>
.briefing {
  max-width: 680px;
  margin: 0 auto;
}

/* Loading */
.briefing-loading {
  text-align: center;
  padding: 80px 24px;
  color: var(--text-muted);
}

.loading-pulse {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0.3;
  margin: 0 auto 16px;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(0.8); opacity: 0.3; }
  50% { transform: scale(1.1); opacity: 0.6; }
}

/* Summary phase */
.briefing-date {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 20px;
}

.summary-card {
  display: flex;
  gap: 16px;
  padding: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 24px;
}

.summary-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #58a6ff, #3b82f6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  color: white;
  flex-shrink: 0;
}

.summary-body {
  flex: 1;
}

.summary-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.summary-text {
  font-size: 16px;
  line-height: 1.7;
  color: var(--text-primary);
}

/* Stats row */
.stats-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}

.stat-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-pill.active {
  border-color: var(--urgent);
  color: var(--urgent);
}

.pill-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.pill-dot.dot-urgent { background: var(--urgent); }
.pill-dot.dot-high { background: var(--high); }
.pill-dot.dot-medium { background: var(--medium); }

/* Begin button */
.btn-begin {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 18px 24px;
  background: linear-gradient(135deg, rgba(88,166,255,0.1), rgba(88,166,255,0.05));
  border: 1px solid var(--accent);
  border-radius: 12px;
  color: var(--accent);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-begin:hover {
  background: linear-gradient(135deg, rgba(88,166,255,0.2), rgba(88,166,255,0.1));
}

.btn-count {
  margin-left: auto;
  background: var(--accent);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
}

/* Review phase */
.review-nav {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.review-progress {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 600;
}

.review-dots {
  display: flex;
  gap: 4px;
  margin-left: auto;
  flex-wrap: wrap;
}

.review-dots .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  cursor: pointer;
  opacity: 0.4;
  transition: all 0.15s;
}

.review-dots .dot.current {
  opacity: 1;
  transform: scale(1.3);
}

.review-dots .dot.dot-urgent { background: var(--urgent); }
.review-dots .dot.dot-high { background: var(--high); }
.review-dots .dot.dot-medium { background: var(--medium); }
.review-dots .dot.dot-low { background: var(--low); }

/* Issue card */
.issue-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}

.issue-priority-bar {
  height: 4px;
}

.bar-urgent { background: var(--urgent); }
.bar-high { background: var(--high); }
.bar-medium { background: var(--medium); }
.bar-low { background: var(--low); }

.issue-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 24px 0;
}

.issue-time {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: auto;
}

.issue-from {
  padding: 12px 24px 0;
}

.issue-from label {
  margin-bottom: 2px;
}

.issue-from span {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

/* LLM Brief */
.issue-brief {
  display: flex;
  gap: 12px;
  margin: 16px 24px;
  padding: 16px;
  background: rgba(88, 166, 255, 0.06);
  border: 1px solid rgba(88, 166, 255, 0.15);
  border-radius: 10px;
}

.brief-icon {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #58a6ff, #3b82f6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 12px;
  color: white;
  flex-shrink: 0;
}

.issue-brief p {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
}

/* Original message */
.issue-original {
  padding: 0 24px;
  margin-bottom: 16px;
}

.issue-original p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  margin-top: 6px;
  max-height: 200px;
  overflow-y: auto;
}

/* Message count badge */
.issue-msg-count {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
  padding: 2px 8px;
  background: rgba(88, 166, 255, 0.08);
  border-radius: 10px;
}

/* Category badge */
.badge-category {
  background: rgba(63, 185, 80, 0.12);
  color: var(--success);
}

/* Triage reasoning */
.issue-reasoning {
  padding: 0 24px;
  margin-bottom: 12px;
}

.issue-reasoning p {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
  line-height: 1.5;
  padding: 8px 12px;
  background: rgba(210, 153, 34, 0.06);
  border-left: 2px solid var(--high);
  border-radius: 0 6px 6px 0;
  margin-top: 4px;
}

/* Timeline */
.issue-timeline {
  padding: 0 24px;
  margin-bottom: 16px;
}

.timeline-list {
  margin-top: 8px;
}

.timeline-entry {
  display: flex;
  gap: 12px;
}

.timeline-dot-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 12px;
  flex-shrink: 0;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
}

.timeline-dot.dot-urgent { background: var(--urgent); }
.timeline-dot.dot-high { background: var(--high); }
.timeline-dot.dot-medium { background: var(--medium); }
.timeline-dot.dot-low { background: var(--low); }

.timeline-line {
  width: 2px;
  flex: 1;
  background: var(--border);
  min-height: 16px;
}

.timeline-body {
  flex: 1;
  padding-bottom: 16px;
}

.timeline-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.badge-sm {
  font-size: 9px;
  padding: 1px 6px;
}

.timeline-time {
  font-size: 11px;
  color: var(--text-muted);
}

.timeline-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  padding: 8px 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  max-height: 120px;
  overflow-y: auto;
}

/* Details */
.issue-details {
  display: flex;
  gap: 24px;
  padding: 12px 24px;
  border-top: 1px solid var(--border);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-item span {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.followup-count {
  color: var(--high) !important;
  font-weight: 700 !important;
}

.unassigned {
  color: var(--urgent) !important;
}

/* Override */
.issue-override {
  padding: 12px 24px;
  border-top: 1px solid var(--border);
}

.override-form {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.override-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.override-row label {
  min-width: 70px;
  margin-bottom: 0;
}

.override-row select,
.override-row input {
  flex: 1;
  padding: 6px 10px;
  font-size: 12px;
}

.override-saved {
  font-size: 11px;
  color: var(--success);
  font-weight: 600;
}

/* Actions */
.issue-actions {
  display: flex;
  gap: 8px;
  padding: 16px 24px;
  border-top: 1px solid var(--border);
  justify-content: flex-end;
}

/* Done phase */
.phase-done {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.done-card {
  text-align: center;
  padding: 48px;
}

.done-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(63, 185, 80, 0.15);
  color: var(--success);
  font-size: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.done-card h2 {
  color: var(--text-primary);
  margin-bottom: 8px;
}

.done-card p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.done-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.done-actions .btn-primary {
  text-decoration: none;
}
</style>
