<template>
  <!-- Toggle tab — always visible at bottom -->
  <button class="firebar-toggle" :class="{ open: isOpen, attract: shouldAttract }" @click="isOpen = !isOpen">
    <span class="toggle-icon">{{ isOpen ? '&#9660;' : '&#9650;' }}</span>
    <span class="toggle-label">Simulation</span>
  </button>

  <div class="firebar" :class="{ collapsed: !isOpen }">
    <div class="firebar-clock">
      <svg class="clock-face" viewBox="0 0 100 100">
        <!-- Dial -->
        <circle cx="50" cy="50" r="46" fill="none" stroke="#2d333b" stroke-width="1.5" />
        <circle cx="50" cy="50" r="44" fill="#0a0d11" />
        <!-- Hour ticks -->
        <line v-for="i in 12" :key="'t'+i"
          :x1="50 + 38 * Math.sin(i * Math.PI / 6)"
          :y1="50 - 38 * Math.cos(i * Math.PI / 6)"
          :x2="50 + 42 * Math.sin(i * Math.PI / 6)"
          :y2="50 - 42 * Math.cos(i * Math.PI / 6)"
          stroke="#6e7681" stroke-width="1.5" stroke-linecap="round"
        />
        <!-- Hour numbers -->
        <text v-for="i in 12" :key="'n'+i"
          :x="50 + 33 * Math.sin(i * Math.PI / 6)"
          :y="50 - 33 * Math.cos(i * Math.PI / 6) + 3"
          text-anchor="middle" fill="#6e7681" font-size="7" font-family="monospace"
        >{{ i }}</text>
        <!-- Hour hand -->
        <line
          x1="50" y1="50"
          :x2="50 + 22 * Math.sin(hourAngle)"
          :y2="50 - 22 * Math.cos(hourAngle)"
          stroke="#e1e4e8" stroke-width="2.5" stroke-linecap="round"
        />
        <!-- Minute hand -->
        <line
          x1="50" y1="50"
          :x2="50 + 30 * Math.sin(minuteAngle)"
          :y2="50 - 30 * Math.cos(minuteAngle)"
          stroke="#58a6ff" stroke-width="1.5" stroke-linecap="round"
        />
        <!-- Center dot -->
        <circle cx="50" cy="50" r="2" fill="#58a6ff" />
        <!-- AM/PM -->
        <text x="50" y="66" text-anchor="middle" fill="#6e7681" font-size="6" font-family="monospace">
          {{ simHour < 12 ? 'AM' : 'PM' }}
        </text>
      </svg>
      <span class="clock-time">{{ clockDisplay }}</span>
    </div>

    <div class="firebar-left">
      <div class="mag-status">
        <span class="mag-icon">&#9646;&#9646;&#9646;</span>
        <span class="mag-label">MAG</span>
        <div class="mag-gauge">
          <div class="mag-fill" :style="{ width: magPercent + '%' }"></div>
        </div>
        <span class="mag-count">{{ magazine.length - currentIndex }}/{{ magazine.length }}</span>
      </div>
    </div>

    <div class="firebar-track" ref="trackRef">
      <div
        v-for="round in activeRounds"
        :key="round.id"
        class="round"
        :class="[`round-${round.priority}`, `round-${round.phase}`]"
        :style="{ left: round.x + '%' }"
      >
        <span class="round-tracer"></span>
        <span class="round-label">
          {{ round.typeIcon }} {{ round.sender }}
          <span v-if="round.priority !== 'unknown'" class="round-priority-tag">[{{ round.priority.toUpperCase() }}]</span>
        </span>
      </div>
      <div class="impact-zone">
        <div v-for="impact in impacts" :key="impact.id" class="impact" :class="`impact-${impact.priority}`">
          <span>&#10005;</span>
        </div>
      </div>
    </div>

    <div class="firebar-right">
      <button class="fire-btn" @click="fireSingle" :disabled="currentIndex >= magazine.length" title="Send one">
        <span class="fire-icon">&#9658;</span>
      </button>
      <button class="fire-btn burst-btn" @click="fireBurst" :disabled="currentIndex >= magazine.length" title="Burst (3 messages)">
        <span class="fire-icon">&#9658;&#9658;&#9658;</span>
      </button>
      <button
        class="fire-btn auto-btn"
        :class="{ active: autoFiring }"
        @click="toggleAuto"
        :disabled="currentIndex >= magazine.length && !autoFiring"
        title="Auto-fire"
      >
        <span class="fire-icon">{{ autoFiring ? '&#9632;' : '&#8634;' }}</span>
      </button>
      <div class="rate-control" v-if="autoFiring">
        <label>{{ fireRate }}ms</label>
        <input type="range" min="500" max="5000" step="100" v-model.number="fireRate" />
      </div>
      <button class="fire-btn reload-btn" @click="reload" title="Reload magazine">
        <span class="fire-icon">&#8635;</span>
      </button>
      <button class="fire-btn clear-btn" @click="clearAll" title="Clear all messages">
        <span class="fire-icon">&#10005;</span>
      </button>
    </div>

    <div class="firebar-compose" :class="{ expanded: composeOpen }">
      <button class="fire-btn compose-toggle" @click="composeOpen = !composeOpen" title="Send custom message">
        <span class="fire-icon">&#9998;</span>
      </button>
      <div v-if="composeOpen" class="compose-form">
        <select v-model="customMsg.type" class="compose-select">
          <option value="email">email</option>
          <option value="sms">sms</option>
          <option value="voice">voice</option>
        </select>
        <input
          v-model="customMsg.sender"
          class="compose-input compose-sender"
          placeholder="Sender"
        />
        <input
          v-model="customMsg.content"
          class="compose-input compose-content"
          placeholder="Message content..."
          @keyup.enter="sendCustom"
        />
        <input
          v-model.number="customMsg.followup_count"
          class="compose-input compose-followup"
          type="number"
          min="0"
          placeholder="#"
          title="Follow-up count"
        />
        <button class="fire-btn" @click="sendCustom" :disabled="!customMsg.content || sending">
          <span class="fire-icon">&#9658;</span>
        </button>
      </div>
    </div>

    <div class="firebar-stats">
      <span class="stat-item"><span class="stat-dot dot-urgent"></span>{{ stats.urgent }}</span>
      <span class="stat-item"><span class="stat-dot dot-high"></span>{{ stats.high }}</span>
      <span class="stat-item"><span class="stat-dot dot-medium"></span>{{ stats.medium }}</span>
      <span class="stat-item"><span class="stat-dot dot-low"></span>{{ stats.low }}</span>
      <span class="stat-item total">&#931; {{ stats.total }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onUnmounted, computed } from 'vue'
import { useMessagesStore } from '../stores/messages.js'

const messagesStore = useMessagesStore()

const isOpen = ref(false)
const composeOpen = ref(false)
const sending = ref(false)
const customMsg = reactive({
  type: 'email',
  sender: '',
  content: '',
  followup_count: 0,
})

const sendCustom = async () => {
  if (!customMsg.content || sending.value) return
  sending.value = true
  try {
    const result = await messagesStore.create({
      type: customMsg.type,
      sender: customMsg.sender || 'test@simulation.local',
      content: customMsg.content,
      followup_count: customMsg.followup_count,
    })
    const p = result.priority || 'medium'
    stats[p]++
    stats.total++
    customMsg.content = ''
  } catch (e) {
    // ignore
  } finally {
    sending.value = false
  }
}

// Messages arrive RAW — no priority. The backend triage engine classifies them.
const MAGAZINE = [
  { type: "email", sender: "john.smith@gmail.com", content: "Subject: Broken garage gate — urgent\n\nThe underground garage gate has been open for 3 days. Anyone can walk in. I've called twice, no response.", followup_count: 0 },
  { type: "sms", sender: "+1 555 234 567", content: "Hey, the ceiling is leaking in the stairwell on the 3rd floor, getting worse", followup_count: 0 },
  { type: "email", sender: "m.williams@yahoo.com", content: "Subject: Missing March statement\n\nNeither I nor my neighbor in 14B received the March expense statement. Please send it.", followup_count: 0 },
  { type: "sms", sender: "+1 555 112 233", content: "Apartment 4B is renting on Airbnb again. This violates the building rules. What are you going to do about it?", followup_count: 0 },
  { type: "email", sender: "board@oakridge-hoa.com", content: "Subject: Board decision — roof repair\n\nWe received three quotes for the roof repair. The board needs to decide before the April meeting.", followup_count: 0 },
  { type: "sms", sender: "+1 555 887 001", content: "Anna hasn't responded to my emails about the repair fund for a week", followup_count: 0 },
  { type: "email", sender: "p.johnson@gmail.com", content: "Subject: Noise complaints — apartment 12A\n\nThis is the fourth complaint about this apartment. Loud music every night after midnight. Nothing has been done.", followup_count: 3 },
  { type: "sms", sender: "+1 555 332 119", content: "Elevator broken again in building B. Third time this month.", followup_count: 2 },
  { type: "email", sender: "r.davis@outlook.com", content: "Subject: Insurance renewal\n\nThe building insurance expires April 30. I don't see it on the meeting agenda.", followup_count: 0 },
  { type: "sms", sender: "+1 555 201 445", content: "Can someone confirm my maintenance fee payment went through? I paid 3 weeks ago.", followup_count: 0 },
  { type: "email", sender: "john.smith@gmail.com", content: "Subject: RE: Broken garage gate\n\nI'm writing for the THIRD TIME. Gate is still open. If nothing changes by end of week, I'm reporting this to the building authority.", followup_count: 3 },
  { type: "sms", sender: "+1 555 234 567", content: "About that stairwell leak I mentioned — it's now dripping onto the electrical panel. That seems dangerous?", followup_count: 1 },
  { type: "voice", sender: "+1 555 100 200", content: "[Whisper transcription, ~72% confidence] Hello, I'm calling... I think it's Mrs. Lewis from... [unintelligible]... there's water in the basement about... twenty centimeters?", followup_count: 0 },
  { type: "email", sender: "office@buildserv.com", content: "Subject: Invoice #INV/2024/0892\n\nPlease find attached the invoice for the gas installation inspection (buildings A–C). Amount: $3,200 net.", followup_count: 0 },
  { type: "email", sender: "tom.green@outlook.com", content: "Subject: Quick question about the parking spot\n\nHi, I just moved in (apt 7C). Is there a way to rent an additional parking spot in the garage? Also the intercom doesn't seem to work for my unit. Thanks!", followup_count: 0 },
  { type: "sms", sender: "+1 555 999 111", content: "Hey, the lady in 8A also has a flooded ceiling, seems like the same issue as mine on the 3rd floor. Maybe worth checking the whole riser?", followup_count: 0 },
]

const magazine = ref([...MAGAZINE])
const currentIndex = ref(0)
const activeRounds = ref([])
const impacts = ref([])
const autoFiring = ref(false)
const fireRate = ref(3000)
let autoTimer = null
let roundCounter = 0

const stats = reactive({ urgent: 0, high: 0, medium: 0, low: 0, total: 0 })

// Simulated day clock — each message maps to a time slot across 7:00–23:00
const DAY_START = 7  // 7 AM
const DAY_END = 23   // 11 PM
const simHour = computed(() => {
  const total = magazine.value.length
  if (total === 0) return DAY_START
  const progress = currentIndex.value / total
  const h = DAY_START + progress * (DAY_END - DAY_START)
  return Math.min(h, DAY_END)
})

const simMinute = computed(() => {
  const fractional = simHour.value - Math.floor(simHour.value)
  return Math.floor(fractional * 60)
})

const hourAngle = computed(() => {
  // 12-hour clock: full rotation = 2*PI over 12 hours
  const h12 = simHour.value % 12
  return (h12 / 12) * 2 * Math.PI
})

const minuteAngle = computed(() => {
  return (simMinute.value / 60) * 2 * Math.PI
})

const clockDisplay = computed(() => {
  const h = Math.floor(simHour.value)
  const m = simMinute.value
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
})

const magPercent = computed(() => {
  if (magazine.value.length === 0) return 0
  return ((magazine.value.length - currentIndex.value) / magazine.value.length) * 100
})

// Nudge the user to open the simulation when the briefing is empty/quiet.
// "Quiet" = no urgent AND no high; total low volume.
const shouldAttract = computed(() => {
  if (isOpen.value) return false
  const s = messagesStore.stats
  return s.urgent === 0 && s.high === 0 && s.total < 3
})

const typeIcon = (type) => {
  return { email: '@', sms: '#', voice: '~' }[type] || '?'
}

const fireSingle = async () => {
  if (currentIndex.value >= magazine.value.length) return
  const msg = magazine.value[currentIndex.value]
  currentIndex.value++

  const roundId = ++roundCounter
  const shortSender = msg.sender.length > 20 ? msg.sender.slice(0, 18) + '..' : msg.sender
  const round = reactive({
    id: roundId,
    priority: 'unknown',  // starts unclassified — backend will decide
    classifiedPriority: null,
    sender: shortSender,
    typeIcon: typeIcon(msg.type),
    phase: 'fly',
    x: 0,
  })
  activeRounds.value.push(round)

  // Animate the round across the track
  const startTime = Date.now()
  const duration = 2500
  const animate = () => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    // Ease-out cubic for a visible deceleration
    const ease = 1 - Math.pow(1 - progress, 3)
    round.x = ease * 85
    if (progress < 1) {
      requestAnimationFrame(animate)
    } else {
      // Send to API — priority gets classified on impact
      sendToApi(msg, round, roundId)
    }
  }
  requestAnimationFrame(animate)
}

const sendToApi = async (msg, round, roundId) => {
  try {
    const result = await messagesStore.create(msg)
    const classified = result.priority || 'medium'
    round.priority = classified
    round.phase = 'classified'
    // Brief pause to show the classified color, then hit
    setTimeout(() => {
      round.phase = 'hit'
      const impact = reactive({ id: roundId, priority: classified })
      impacts.value.push(impact)
      setTimeout(() => { impacts.value = impacts.value.filter(i => i.id !== roundId) }, 1000)
      setTimeout(() => { activeRounds.value = activeRounds.value.filter(r => r.id !== roundId) }, 800)
    }, 400)
    stats[classified]++
    stats.total++
  } catch (e) {
    round.priority = 'medium'
    round.phase = 'hit'
    const impact = reactive({ id: roundId, priority: 'medium' })
    impacts.value.push(impact)
    setTimeout(() => { impacts.value = impacts.value.filter(i => i.id !== roundId) }, 1000)
    setTimeout(() => { activeRounds.value = activeRounds.value.filter(r => r.id !== roundId) }, 800)
    stats.medium++
    stats.total++
  }
}

const fireBurst = async () => {
  for (let i = 0; i < 3; i++) {
    if (currentIndex.value >= magazine.value.length) break
    setTimeout(() => fireSingle(), i * 600)
  }
}

const toggleAuto = () => {
  if (autoFiring.value) {
    autoFiring.value = false
    clearInterval(autoTimer)
    autoTimer = null
  } else {
    autoFiring.value = true
    autoTimer = setInterval(() => {
      if (currentIndex.value >= magazine.value.length) {
        autoFiring.value = false
        clearInterval(autoTimer)
        autoTimer = null
        return
      }
      fireSingle()
    }, fireRate.value)
  }
}

const reload = () => {
  currentIndex.value = 0
  stats.urgent = 0
  stats.high = 0
  stats.medium = 0
  stats.low = 0
  stats.total = 0
  activeRounds.value = []
  impacts.value = []
  if (autoFiring.value) {
    autoFiring.value = false
    clearInterval(autoTimer)
    autoTimer = null
  }
}

const clearAll = async () => {
  try {
    await messagesStore.clearAll()
  } catch (e) {
    // ignore — best effort
  }
  reload()
}

onUnmounted(() => {
  if (autoTimer) clearInterval(autoTimer)
})
</script>

<style scoped>
.firebar-toggle {
  position: fixed;
  bottom: 0;
  left: calc(var(--sidebar-width, 240px) + 50%);
  transform: translateX(-50%);
  z-index: 201;
  background: #0a0d11;
  border: 1px solid #1a1f27;
  border-bottom: none;
  border-radius: 8px 8px 0 0;
  padding: 4px 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #6e7681;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  transition: all 0.2s;
}

.firebar-toggle:hover {
  color: #8b949e;
  background: #161b22;
}

.firebar-toggle.open {
  bottom: 56px;
}

.firebar-toggle.attract {
  background: #d2691e;
  border-color: #ff8c3a;
  color: #fff4e6;
  animation: attractJump 1.2s ease-in-out infinite;
  box-shadow: 0 0 12px rgba(255, 140, 58, 0.55), 0 0 24px rgba(255, 140, 58, 0.25);
}

.firebar-toggle.attract:hover {
  background: #ff8c3a;
  color: #fff;
}

@keyframes attractJump {
  0%, 100% {
    transform: translateX(-50%) translateY(0);
    box-shadow: 0 0 10px rgba(255, 140, 58, 0.45), 0 0 20px rgba(255, 140, 58, 0.2);
  }
  40% {
    transform: translateX(-50%) translateY(-8px);
    box-shadow: 0 6px 18px rgba(255, 140, 58, 0.65), 0 0 28px rgba(255, 140, 58, 0.35);
  }
  60% {
    transform: translateX(-50%) translateY(-4px);
  }
}

.toggle-icon {
  font-size: 8px;
}

.firebar.collapsed {
  transform: translateY(100%);
  pointer-events: none;
}

.firebar {
  transition: transform 0.25s ease;
}

.firebar-clock {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  border-right: 1px solid #1a1f27;
  height: 100%;
}

.clock-face {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.clock-time {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  font-weight: 700;
  color: #58a6ff;
  letter-spacing: 1px;
  min-width: 42px;
}

.firebar {
  position: fixed;
  bottom: 0;
  left: var(--sidebar-width, 240px);
  right: 0;
  height: 56px;
  background: #0a0d11;
  border-top: 1px solid #1a1f27;
  display: flex;
  align-items: center;
  z-index: 200;
  font-family: 'Courier New', monospace;
  overflow: hidden;
}

.firebar-left {
  padding: 0 12px;
  border-right: 1px solid #1a1f27;
  height: 100%;
  display: flex;
  align-items: center;
  min-width: 180px;
}

.mag-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mag-icon {
  color: #3fb950;
  font-size: 14px;
  letter-spacing: -2px;
}

.mag-label {
  font-size: 9px;
  font-weight: 700;
  color: #3fb950;
  letter-spacing: 1px;
}

.mag-gauge {
  width: 60px;
  height: 6px;
  background: #1a1f27;
  border-radius: 3px;
  overflow: hidden;
}

.mag-fill {
  height: 100%;
  background: linear-gradient(90deg, #f85149, #d29922, #3fb950);
  border-radius: 3px;
  transition: width 0.3s;
}

.mag-count {
  font-size: 11px;
  color: #6e7681;
  font-variant-numeric: tabular-nums;
}

.firebar-track {
  flex: 1;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.round {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition: none;
  z-index: 2;
}

.round-tracer {
  display: inline-block;
  width: 24px;
  height: 3px;
  border-radius: 2px;
}

.round-unknown .round-tracer { background: #484f58; box-shadow: 0 0 6px #484f5866; }
.round-urgent .round-tracer { background: #f85149; box-shadow: 0 0 8px #f85149, 0 0 16px #f8514966; }
.round-high .round-tracer { background: #d29922; box-shadow: 0 0 8px #d29922, 0 0 16px #d2992266; }
.round-medium .round-tracer { background: #58a6ff; box-shadow: 0 0 8px #58a6ff, 0 0 16px #58a6ff66; }
.round-low .round-tracer { background: #6e7681; box-shadow: 0 0 6px #6e768166; }

.round-label {
  font-size: 10px;
  color: #8b949e;
  transition: color 0.3s;
}

.round-classified .round-label {
  color: #e1e4e8;
}

.round-priority-tag {
  font-weight: 700;
  font-size: 9px;
  margin-left: 4px;
  animation: tagAppear 0.3s ease-out;
}

.round-urgent .round-priority-tag { color: #f85149; }
.round-high .round-priority-tag { color: #d29922; }
.round-medium .round-priority-tag { color: #58a6ff; }
.round-low .round-priority-tag { color: #6e7681; }

@keyframes tagAppear {
  from { opacity: 0; transform: scale(0.5); }
  to { opacity: 1; transform: scale(1); }
}

.round-fly .round-tracer {
  animation: pulse 0.2s ease-in-out infinite alternate;
}

.round-classified {
  animation: classifyFlash 0.4s ease-out;
}

.round-hit {
  animation: hitFlash 0.8s ease-out forwards;
}

@keyframes classifyFlash {
  0% { filter: brightness(1); }
  50% { filter: brightness(2); }
  100% { filter: brightness(1); }
}

@keyframes pulse {
  from { opacity: 0.8; }
  to { opacity: 1; }
}

@keyframes hitFlash {
  0% { opacity: 1; transform: translateY(-50%) scale(1); }
  40% { opacity: 0.9; transform: translateY(-50%) scale(1.4); }
  100% { opacity: 0; transform: translateY(-50%) scale(0.5); }
}

.impact-zone {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.impact {
  position: absolute;
  font-size: 18px;
  animation: impactBurst 1s ease-out forwards;
}

.impact-urgent span { color: #f85149; text-shadow: 0 0 12px #f85149; }
.impact-high span { color: #d29922; text-shadow: 0 0 12px #d29922; }
.impact-medium span { color: #58a6ff; text-shadow: 0 0 12px #58a6ff; }
.impact-low span { color: #6e7681; text-shadow: 0 0 8px #6e7681; }

@keyframes impactBurst {
  0% { transform: scale(0.5); opacity: 1; }
  40% { transform: scale(1.8); opacity: 0.8; }
  100% { transform: scale(2.5); opacity: 0; }
}

.firebar-right {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 10px;
  border-left: 1px solid #1a1f27;
  height: 100%;
}

.fire-btn {
  width: 32px;
  height: 32px;
  background: #161b22;
  border: 1px solid #2d333b;
  border-radius: 4px;
  color: #8b949e;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  transition: all 0.15s;
}

.fire-btn:hover:not(:disabled) {
  background: #242a33;
  color: #e1e4e8;
  border-color: #58a6ff;
}

.fire-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.fire-btn:active:not(:disabled) {
  transform: scale(0.92);
}

.burst-btn .fire-icon {
  letter-spacing: -4px;
  font-size: 8px;
}

.auto-btn.active {
  background: rgba(248, 81, 73, 0.2);
  border-color: #f85149;
  color: #f85149;
  animation: autoGlow 1s ease-in-out infinite alternate;
}

@keyframes autoGlow {
  from { box-shadow: 0 0 4px rgba(248,81,73,0.3); }
  to { box-shadow: 0 0 10px rgba(248,81,73,0.5); }
}

.reload-btn .fire-icon {
  font-size: 14px;
}

.clear-btn {
  border-color: #f85149 !important;
  color: #f85149 !important;
}

.clear-btn:hover:not(:disabled) {
  background: rgba(248, 81, 73, 0.2) !important;
}

.rate-control {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rate-control label {
  font-size: 9px;
  color: #6e7681;
  text-transform: none;
  letter-spacing: 0;
  min-width: 36px;
}

.rate-control input[type="range"] {
  width: 60px;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: #2d333b;
  border: none;
  border-radius: 2px;
  padding: 0;
  box-shadow: none;
}

.rate-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 10px;
  height: 10px;
  background: #58a6ff;
  border-radius: 50%;
  cursor: pointer;
}

.firebar-compose {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
  border-left: 1px solid #1a1f27;
  height: 100%;
}

.compose-toggle {
  flex-shrink: 0;
}

.compose-form {
  display: flex;
  align-items: center;
  gap: 4px;
}

.compose-select {
  width: 62px;
  padding: 4px 4px;
  font-size: 10px;
  font-family: 'Courier New', monospace;
  background: #161b22;
  border: 1px solid #2d333b;
  border-radius: 4px;
  color: #8b949e;
}

.compose-input {
  padding: 4px 8px;
  font-size: 11px;
  font-family: 'Courier New', monospace;
  background: #161b22;
  border: 1px solid #2d333b;
  border-radius: 4px;
  color: #e1e4e8;
}

.compose-input:focus {
  border-color: #58a6ff;
  box-shadow: none;
}

.compose-sender {
  width: 120px;
}

.compose-content {
  width: 200px;
}

.compose-followup {
  width: 40px;
  text-align: center;
}

.firebar-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  border-left: 1px solid #1a1f27;
  height: 100%;
  min-width: 160px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #8b949e;
  font-variant-numeric: tabular-nums;
}

.stat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.dot-urgent { background: #f85149; }
.dot-high { background: #d29922; }
.dot-medium { background: #58a6ff; }
.dot-low { background: #6e7681; }

.stat-item.total {
  font-weight: 700;
  color: #e1e4e8;
  margin-left: 4px;
  padding-left: 8px;
  border-left: 1px solid #2d333b;
}
</style>
