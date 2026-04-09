<template>
  <div class="briefing">
    <!-- Loading -->
    <div v-if="loading" class="briefing-loading">
      <div class="loading-pulse"></div>
      <p>Preparing briefing...</p>
    </div>

    <div v-else-if="error" class="empty-state" style="color: var(--urgent)">{{ error }}</div>

    <div v-else-if="briefing" class="briefing-document">

      <!-- PHASE 1: Summary -->
      <div v-if="phase === 'summary'" class="phase-summary">
        <div class="briefing-date">{{ formatDate(briefing.generated_at) }}</div>

        <div class="summary-card">
          <div class="summary-avatar">A</div>
          <div class="summary-body">
            <div class="summary-label">Morning briefing</div>
            <p class="summary-text">{{ briefing.summary }}</p>
          </div>
          <button
            class="btn-tts"
            @click="startBriefingReadAloud()"
            :class="{ playing: ttsPlaying }"
            :title="ttsPlaying ? 'Stop reading' : 'Read aloud'"
          >
            <span v-if="ttsLoading" class="tts-icon">...</span>
            <span v-else-if="ttsPlaying" class="tts-icon">&#9632;</span>
            <span v-else class="tts-icon">&#9654;</span>
          </button>
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
          <div class="stat-pill" v-if="briefing.stats.unassigned < briefing.stats.total">
            <span>{{ briefing.stats.unassigned }} unassigned</span>
          </div>
        </div>

        <button
          v-if="briefing.issues.length > 0"
          class="btn-begin"
          @click="briefingStore.beginReview()"
        >
          Review issues one by one
          <span class="btn-count">{{ briefing.issues.length }}</span>
        </button>
      </div>

      <!-- PHASE 2: Issue-by-issue review -->
      <div v-if="phase === 'review'" class="phase-review">
        <div class="review-nav">
          <button class="btn btn-sm" @click="briefingStore.backToSummary()">Back to briefing</button>
          <span class="review-progress">{{ currentIndex + 1 }} z {{ briefing.issues.length }}</span>
          <button
            v-if="!ttsPlaying"
            class="btn btn-sm btn-tts-flow"
            @click="startFlowFromCurrent()"
            title="Read from this issue"
          >&#9654; Read</button>
          <button
            v-else
            class="btn btn-sm btn-tts-flow playing"
            @click="stopTTS()"
            title="Stop reading"
          >&#9632; Stop</button>
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
            <span class="badge" :class="`badge-${currentIssue.priority}`">{{ label(priorityLabels, currentIssue.priority) }}</span>
            <span class="badge badge-urgency" :class="`urgency-${currentIssue.urgency}`" v-if="currentIssue.urgency">{{ urgencyLabel(currentIssue.urgency) }}</span>
            <span class="badge badge-category" v-if="currentIssue.category">{{ label(categoryLabels, currentIssue.category) }}</span>
            <span class="badge" :class="`badge-${currentIssue.type}`">{{ label(channelLabels, currentIssue.type) }}</span>
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
            <div class="brief-icon">A</div>
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
                    <span class="badge badge-sm" :class="`badge-${entry.type}`">{{ label(channelLabels, entry.type) }}</span>
                    <span class="timeline-time">{{ entry.time_label }}</span>
                  </div>
                  <p class="timeline-content">{{ entry.content }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="issue-details" v-if="currentIssue.followup_count > 0">
            <div class="detail-item">
              <label>Follow-ups</label>
              <span class="followup-count">{{ currentIssue.followup_count }}x</span>
            </div>
          </div>

          <!-- Suggested action -->
          <div class="issue-suggested-action" v-if="suggestedAction(currentIssue)">
            <label>Suggested action</label>
            <button class="suggested-action-btn" :class="`suggested-${suggestedAction(currentIssue).type}`" @click="suggestedAction(currentIssue).handler(currentIssue)">
              <span class="action-icon">{{ suggestedAction(currentIssue).icon }}</span>
              <div class="action-info">
                <span class="action-name">{{ suggestedAction(currentIssue).name }}</span>
                <span class="action-desc">{{ suggestedAction(currentIssue).desc }}</span>
              </div>
            </button>
            <div v-if="currentIssue.draft_response" class="draft-in-action">
              <button class="draft-toggle" @click="showDraft = !showDraft">
                <span class="draft-reply-icon">&#8617;</span>
                <span>Suggested response</span>
                <span class="draft-chevron">{{ showDraft ? '&#9650;' : '&#9660;' }}</span>
              </button>
              <div v-if="showDraft" class="draft-response-body">
                <p>{{ currentIssue.draft_response }}</p>
                <button class="btn btn-sm draft-use-btn" @click="respondToSender(currentIssue)">Use in response</button>
              </div>
            </div>
          </div>

          <!-- Actions menu -->
          <div class="issue-quick-actions">
            <button class="action-btn action-primary" @click="showActions = !showActions">
              {{ showActions ? 'Close' : 'All actions' }}
            </button>
            <div v-if="showActions" class="actions-menu">
              <button class="action-menu-item" @click="respondToSender(currentIssue)">
                <span class="action-icon">&#9993;</span>
                <div class="action-info">
                  <span class="action-name">Reply to sender</span>
                  <span class="action-desc">Send a response to {{ currentIssue.sender }}</span>
                </div>
              </button>
              <button class="action-menu-item" @click="escalateIssue(currentIssue)">
                <span class="action-icon">&#9888;</span>
                <div class="action-info">
                  <span class="action-name">Escalate to urgent</span>
                  <span class="action-desc">Change priority to URGENT and notify the team</span>
                </div>
              </button>
              <button class="action-menu-item" @click="scheduleVisit(currentIssue)">
                <span class="action-icon">&#128197;</span>
                <div class="action-info">
                  <span class="action-name">Schedule a visit</span>
                  <span class="action-desc">Arrange an on-site inspection</span>
                </div>
              </button>
              <button class="action-menu-item" @click="assignToTechnician(currentIssue)">
                <span class="action-icon">&#128736;</span>
                <div class="action-info">
                  <span class="action-name">Assign to technician</span>
                  <span class="action-desc">Send a work order to maintenance</span>
                </div>
              </button>
              <button class="action-menu-item" @click="sendAcknowledgment(currentIssue)">
                <span class="action-icon">&#9993;</span>
                <div class="action-info">
                  <span class="action-name">Send acknowledgment</span>
                  <span class="action-desc">Let the sender know the issue is being handled</span>
                </div>
              </button>
              <button class="action-menu-item" @click="markResolved(currentIssue)">
                <span class="action-icon">&#10003;</span>
                <div class="action-info">
                  <span class="action-name">Mark as resolved</span>
                  <span class="action-desc">Close the issue and notify the sender</span>
                </div>
              </button>
            </div>
          </div>

          <!-- Override controls -->
          <div class="issue-override">
            <button class="btn btn-sm" @click="showOverride = !showOverride">
              {{ showOverride ? 'Cancel change' : 'Override triage' }}
            </button>
            <div v-if="showOverride" class="override-form">
              <div class="override-row">
                <label>Priority</label>
                <select v-model="overrideData.priority">
                  <option value="">no change</option>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                  <option value="urgent">urgent</option>
                </select>
              </div>
              <div class="override-row">
                <label>Category</label>
                <select v-model="overrideData.category">
                  <option value="">no change</option>
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
                <input v-model="overrideData.reason" placeholder="Why are you overriding the triage?" />
              </div>
              <button class="btn btn-primary btn-sm" @click="submitOverride" :disabled="overrideLoading">
                {{ overrideLoading ? 'Saving...' : 'Save change' }}
              </button>
              <span v-if="overrideSaved" class="override-saved">Saved — will improve future triage</span>
            </div>
          </div>

          <!-- Navigation actions -->
          <div class="issue-actions">
            <button class="btn btn-sm" @click="briefingStore.prevIssue()" :disabled="currentIndex === 0">Previous</button>
            <button
              class="btn btn-primary btn-sm"
              @click="briefingStore.nextIssue()"
              v-if="currentIndex < briefing.issues.length - 1"
            >Next issue</button>
            <button
              class="btn btn-primary btn-sm"
              @click="briefingStore.finishReview()"
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
          <p>Reviewed all {{ briefing.issues.length }} issues.</p>
          <div class="done-actions">
            <button class="btn" @click="briefingStore.backToSummary()">Back to summary</button>
            <router-link to="/feed" class="btn btn-primary">Open issues</router-link>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useBriefingStore } from '../stores/briefing.js'
import { useMessagesStore } from '../stores/messages.js'
import { textToSpeech } from '../api.js'
import { priorityLabels, categoryLabels, channelLabels, label } from '../labels.js'

const router = useRouter()

const briefingStore = useBriefingStore()
const messagesStore = useMessagesStore()
const { data: briefing, loading, error, phase, currentIndex, currentIssue } = storeToRefs(briefingStore)

// TTS state — continuous flow mode
const ttsPlaying = ref(false)
const ttsLoading = ref(false)
let ttsAudio = null
let ttsFlowActive = false  // when true, auto-reads next issue on finish

const playText = async (text, onEnded) => {
  if (!text) { onEnded?.(); return }
  ttsLoading.value = true
  try {
    const blob = await textToSpeech(text)
    const url = URL.createObjectURL(blob)
    ttsAudio = new Audio(url)
    ttsAudio.onended = () => {
      ttsPlaying.value = false
      URL.revokeObjectURL(url)
      onEnded?.()
    }
    ttsAudio.play()
    ttsPlaying.value = true
  } catch (e) {
    console.error('TTS failed:', e)
    ttsPlaying.value = false
    onEnded?.()
  } finally {
    ttsLoading.value = false
  }
}

const stopTTS = () => {
  ttsFlowActive = false
  if (ttsAudio) {
    ttsAudio.pause()
    ttsAudio.currentTime = 0
    ttsAudio = null
  }
  ttsPlaying.value = false
}

// Start reading the full briefing: summary → then each issue in flow
const startBriefingReadAloud = () => {
  if (ttsPlaying.value) { stopTTS(); return }
  ttsFlowActive = true
  playText(briefing.value.summary, () => {
    if (!ttsFlowActive || !briefing.value?.issues?.length) return
    // After summary, enter review and start reading issues
    briefingStore.beginReview()
    readCurrentIssue()
  })
}

// Start reading from the current issue in flow mode
const startFlowFromCurrent = () => {
  if (ttsPlaying.value) { stopTTS(); return }
  ttsFlowActive = true
  readCurrentIssue()
}

const readCurrentIssue = () => {
  if (!ttsFlowActive) return
  const issue = briefing.value?.issues?.[currentIndex.value]
  if (!issue) { ttsFlowActive = false; return }
  const text = issue.llm_brief || issue.content
  playText(text, () => {
    if (!ttsFlowActive) return
    // Auto-advance to next issue
    if (currentIndex.value < briefing.value.issues.length - 1) {
      briefingStore.nextIssue()
      // Small delay before reading next issue
      setTimeout(() => readCurrentIssue(), 500)
    } else {
      // All done
      ttsFlowActive = false
      briefingStore.finishReview()
    }
  })
}

// Stop TTS when user manually switches issues or goes back to summary
watch(phase, (newPhase, oldPhase) => {
  // Only stop if user navigated away (not our auto-advance)
  if (!ttsFlowActive) stopTTS()
})

// If user manually clicks a dot or prev/next while flow is not active, stop
watch(currentIndex, () => {
  if (!ttsFlowActive) stopTTS()
})

// Actions menu
const showActions = ref(false)
const showDraft = ref(false)

// Reset actions menu and draft when switching issues
watch(currentIndex, () => { showActions.value = false; showDraft.value = false })

// Action handlers
const respondToSender = (issue) => {
  showActions.value = false
  router.push({ path: '/respond', query: { message: issue.id } })
}

const escalateIssue = (issue) => {
  showActions.value = false
  messagesStore.override(issue.id, { priority: 'urgent' })
  briefingStore.updateCurrentIssue({ priority: 'urgent' })
}

const scheduleVisit = (issue) => {
  showActions.value = false
  alert(`Schedule visit: ${issue.sender} — ${issue.category || 'general'}`)
}

const assignToTechnician = (issue) => {
  showActions.value = false
  alert(`Assign to technician: ${issue.sender} — ${issue.category || 'general'}`)
}

const sendAcknowledgment = (issue) => {
  showActions.value = false
  alert(`Acknowledgment sent to: ${issue.sender}`)
}

const markResolved = (issue) => {
  showActions.value = false
  alert(`Marked as resolved: ${issue.sender} — ${issue.category || 'general'}`)
}

// Suggested action based on issue context
const suggestedAction = (issue) => {
  if (!issue) return null

  const urgency = issue.urgency || ''
  const importance = issue.importance || ''
  const category = issue.category || ''
  const followups = issue.followup_count || 0

  // Immediate + critical → assign to technician NOW
  if (urgency === 'immediate' && importance === 'critical') {
    return {
      type: 'urgent',
      icon: '\u{1F6E0}',
      name: 'Send technician immediately',
      desc: `Active failure (${category}) — requires on-site intervention`,
      handler: assignToTechnician,
    }
  }

  // 3+ followups → respond to sender (they're frustrated)
  if (followups >= 3) {
    return {
      type: 'urgent',
      icon: '\u2709',
      name: 'Reply to sender urgently',
      desc: `Resident has followed up ${followups}x — needs a response`,
      handler: respondToSender,
    }
  }

  // Immediate urgency → schedule visit
  if (urgency === 'immediate') {
    return {
      type: 'high',
      icon: '\u{1F4C5}',
      name: 'Schedule visit today',
      desc: `Urgent situation (${category}) — requires inspection`,
      handler: scheduleVisit,
    }
  }

  // Today urgency → assign technician
  if (urgency === 'today') {
    return {
      type: 'medium',
      icon: '\u{1F6E0}',
      name: 'Assign to technician',
      desc: `Needs attention today — ${category}`,
      handler: assignToTechnician,
    }
  }

  // Important but not urgent → acknowledge
  if (importance === 'critical' || importance === 'high') {
    return {
      type: 'medium',
      icon: '\u2709',
      name: 'Send acknowledgment',
      desc: 'Let the sender know the issue is being handled',
      handler: sendAcknowledgment,
    }
  }

  // Everything else → acknowledge
  return {
    type: 'low',
    icon: '\u2709',
    name: 'Send acknowledgment',
    desc: 'Standard issue — confirm receipt',
    handler: sendAcknowledgment,
  }
}

onUnmounted(() => stopTTS())

// Override state (local to this view)
const showOverride = ref(false)
const overrideLoading = ref(false)
const overrideSaved = ref(false)
const overrideData = reactive({
  priority: '',
  category: '',
  reason: '',
})

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
    await messagesStore.override(currentIssue.value.id, payload)
    briefingStore.updateCurrentIssue(payload)
    overrideSaved.value = true
  } catch (e) {
    // ignore
  } finally {
    overrideLoading.value = false
  }
}

const urgencyLabel = (urgency) => {
  const labels = {
    immediate: 'now',
    today: 'today',
    this_week: 'this week',
    no_rush: 'no rush',
  }
  return labels[urgency] || urgency
}

const formatDate = (dateStr) => {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

onMounted(() => briefingStore.fetch())
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

.btn-tts-flow {
  font-size: 12px;
  padding: 4px 12px;
  border-color: var(--accent);
  color: var(--accent);
}

.btn-tts-flow.playing {
  background: rgba(88, 166, 255, 0.12);
  border-color: var(--accent);
  color: var(--accent);
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

/* Message count badge */
.issue-msg-count {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
  padding: 2px 8px;
  background: rgba(88, 166, 255, 0.08);
  border-radius: 10px;
}

/* Urgency badge */
.badge-urgency {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.2px;
}
.urgency-immediate { background: rgba(248,81,73,0.12); color: var(--urgent); }
.urgency-today { background: rgba(210,153,34,0.12); color: var(--high); }
.urgency-this_week { background: rgba(88,166,255,0.1); color: var(--medium); }
.urgency-no_rush { background: rgba(139,148,158,0.1); color: var(--low); }

/* Category badge */
.badge-category {
  background: rgba(63, 185, 80, 0.12);
  color: var(--success);
}

/* Draft in suggested action */
.draft-in-action {
  margin-top: 10px;
}

.draft-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 12px;
  color: var(--success);
  font-weight: 600;
  width: 100%;
  transition: all 0.15s;
}

.draft-toggle:hover {
  background: rgba(63, 185, 80, 0.06);
  border-color: var(--success);
}

.draft-reply-icon {
  font-size: 14px;
}

.draft-chevron {
  margin-left: auto;
  font-size: 10px;
  color: var(--text-muted);
}

.draft-response-body {
  margin-top: 8px;
  padding: 12px 14px;
  background: rgba(63, 185, 80, 0.06);
  border-left: 3px solid var(--success);
  border-radius: 0 8px 8px 0;
}

.draft-response-body p {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.draft-use-btn {
  margin-top: 10px;
  border-color: var(--success);
  color: var(--success);
}

.draft-use-btn:hover {
  background: rgba(63, 185, 80, 0.1);
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

/* Suggested action */
.issue-suggested-action {
  padding: 14px 24px 0;
  border-top: 1px solid var(--border);
}

.issue-suggested-action label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin-bottom: 8px;
  display: block;
}

.suggested-action-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  cursor: pointer;
  width: 100%;
  text-align: left;
  border: 1px solid;
  transition: all 0.15s;
}

.suggested-urgent {
  background: rgba(248, 81, 73, 0.08);
  border-color: rgba(248, 81, 73, 0.3);
  color: var(--text-primary);
}
.suggested-urgent:hover {
  background: rgba(248, 81, 73, 0.14);
}
.suggested-urgent .action-name { color: var(--urgent); }

.suggested-high {
  background: rgba(210, 153, 34, 0.08);
  border-color: rgba(210, 153, 34, 0.3);
  color: var(--text-primary);
}
.suggested-high:hover {
  background: rgba(210, 153, 34, 0.14);
}
.suggested-high .action-name { color: var(--high); }

.suggested-medium {
  background: rgba(88, 166, 255, 0.08);
  border-color: rgba(88, 166, 255, 0.3);
  color: var(--text-primary);
}
.suggested-medium:hover {
  background: rgba(88, 166, 255, 0.14);
}
.suggested-medium .action-name { color: var(--accent); }

.suggested-low {
  background: rgba(139, 148, 158, 0.06);
  border-color: rgba(139, 148, 158, 0.2);
  color: var(--text-primary);
}
.suggested-low:hover {
  background: rgba(139, 148, 158, 0.1);
}

/* Quick action buttons */
.issue-quick-actions {
  display: flex;
  gap: 8px;
  padding: 14px 24px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  transition: all 0.15s;
}

.action-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(88, 166, 255, 0.06);
}

.action-primary {
  color: var(--text-secondary);
  border-color: var(--border);
}

.actions-menu {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
  margin-top: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 6px;
  animation: menuSlide 0.15s ease-out;
}

@keyframes menuSlide {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.action-menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.1s;
  text-align: left;
  width: 100%;
  color: var(--text-primary);
}

.action-menu-item:hover {
  background: var(--bg-hover);
}

.action-icon {
  font-size: 18px;
  width: 28px;
  text-align: center;
  flex-shrink: 0;
}

.action-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.action-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.action-desc {
  font-size: 11px;
  color: var(--text-secondary);
}

/* TTS button on summary */
.btn-tts {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
  align-self: flex-start;
  margin-top: 4px;
}

.btn-tts:hover {
  border-color: var(--accent);
  background: rgba(88, 166, 255, 0.08);
}

.btn-tts.playing {
  background: rgba(88, 166, 255, 0.15);
  border-color: var(--accent);
}

.tts-icon {
  font-size: 14px;
  color: var(--accent);
  line-height: 1;
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
