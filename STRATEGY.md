# Avan — Strategy

## Vision

Avan is an AI-native triage layer for residential property managers. The core loop: messages arrive from residents (email, SMS, voice) → an LLM agent classifies, groups, and prioritizes them → the manager gets a structured briefing instead of raw noise. Every manager correction feeds back as a few-shot example, so the system improves with use.

The goal is not to replace the manager — it's to eliminate the cognitive overhead of reading 50 unstructured messages and deciding what matters. Avan handles the sorting; the manager handles the judgment.

## Agent Architecture — Current vs Target

### Current: single graph, four nodes

```
classify → relate → decide → draft → END
```

Single `StateGraph` with one `TriageState`. Nodes are separate modules (`nodes/classify.py` etc.) but share state and graph. Decide is rule-based, rest is LLM.

**Pros:** simple, single invoke, easy to debug.
**Cons:** monolithic state, can't run draft standalone, retry policy is all-or-nothing.

### Target: separate agents per responsibility

```
ClassifyAgent    — category, priority, urgency, importance, sender_type
RelateAgent      — same-sender grouping + cross-sender LLM matching
DecideAgent      — rule-based escalation/group/standard (no LLM)
DraftAgent       — channel-appropriate response generation
BriefingAgent    — executive summary + per-issue briefs (already a separate graph)
```

Each agent has:
- Own `StateGraph` with minimal state (only what it needs)
- Separate prompts and structured output schema
- Independent retry/fallback (e.g. classify falls back to regex, draft falls back to template)
- Can run standalone (e.g. `DraftAgent` invoked on-demand from `/generate-reply`)

**Orchestration:** meta-graph or simple pipeline in `triage_service.py` calling agents sequentially, passing one's output as the next's input.

**When to do it:** when the need arises — e.g. async execution (classify fast, draft in background), A/B testing prompts per agent, or different models per agent (cheap model for classify, expensive for draft).

## Metrics

### System metrics (engineering health)

- **Triage accuracy** — % of messages where the manager does not override the agent's decision. Measured implicitly via override rate. Target: >85% without correction after ~50 overrides per building.
- **Pipeline latency** — time from message intake to completed briefing entry. Current state: synchronous, visible lag on burst. Target: <3s per message with async processing.
- **Cost per ticket** — GPT-4o-mini + selective cross-sender LLM calls. Trackable per building per month. Critical input for pricing model.
- **Grouping precision** — ratio of correctly merged threads vs false positives. No automated measure yet; "ungroup" override is the implicit signal. Target: track ungroup rate as a proxy.
- **Escalation recall** — are all safety-critical messages being escalated? False negatives here are the highest-risk failure mode. Target: zero missed escalations on the defined ruleset.

### Business metrics (value for the customer)

- **Manager triage time** — before Avan: 45–60 min every morning reading and sorting raw messages. After Avan: 5–10 min reviewing the briefing and approving actions. This is the number that sells the product.
- **Time to first response (TTR)** — average time between a resident message and a manager reply. Draft responses + clear priority = faster reaction. Measurable once outbound channel integration exists.
- **Critical issues caught** — escalations flagged by Avan that would have been buried in noise. One missed water leak = repair cost + tenant churn. One caught escalation = months of subscription ROI.
- **Per-building learning curve** — how many overrides until accuracy stabilizes. This is the argument for long-term contracts: the system gets better the longer it runs for a specific building. Target: measure accuracy delta at 10 / 50 / 200 overrides.

### On ground truth

The override loop is not just a UX feature — it is the ground truth collection mechanism. Every manager correction is a labeled example. This means accuracy measurement is a byproduct of normal product usage, not a separate data collection effort. At scale, override history becomes the dataset for fine-tuning or retrieval-augmented few-shot selection.

## What's Next

- Resident CRM: map phone/email → resident → unit → building
- Real intake: Twilio webhook (SMS), IMAP/SendGrid (email)
- NLU module for voice channel (transcription + intent extraction from incoming calls)
- Multi-tenant: each building has its own context, history, communication style
- Per-building learning: admin overrides improve classification for that building only — not globally
- Assignment engine (auto-assign to maintenance staff based on category)
- Notification channels (push to manager's phone for urgent escalations)
- Multilingual support: draft in sender's language, admin interface in their language. Not just translation — cultural context.
- Resident portal: resident sees status of their ticket + voting system for building matters (renovations, rule changes, budget proposals, common-area decisions). Results feed into briefing so the manager sees consensus before acting.
- Event calendar: recurring events (inspections, fire alarm tests, garbage pickup, meter readings) and one-off planned events (scheduled repairs, lease signings, contractor visits). Surfaced in briefing so the manager sees upcoming events alongside active issues. Triage agent can correlate incoming messages with scheduled events (e.g., resident complaint about noise → scheduled renovation today). Model: `Event` document with recurrence rules (RRULE or simple: daily/weekly/monthly/yearly + day), linked to building/unit.
- Override UX: currently post-hoc only (manager corrects after triage). No "flag for human review" flow, no inline correction during briefing review. Target: triage confidence score → low-confidence items surface for review before briefing is finalized.

## Hard Problems

- **M&A integration:** every acquired company has different processes, different historical data, different category naming, different SLAs. System must adapt to a new building in <1 day — onboarding can't require manual rule configuration.

  The onboarding pipeline has three layers:
  1. **Auto-discovery** — ingest historical tickets (CSV, legacy system export, email archive) and cluster them into candidate categories using LLM. Manager reviews and confirms in a single session, not weeks of configuration.
  2. **Ticket migration** — historical tickets become the first few-shot examples for that building. The system starts with prior knowledge, not a cold start.
  3. **Per-building prompt tuning** — each building gets its own override store and few-shot bank. Tuning one building must not regress others. Isolation is enforced at the data layer, not the model layer.

  This is the core growth engine for an M&A-driven rollup strategy: acquire a property management company, onboard their portfolio in <1 day, immediately deliver value without manual re-configuration.

- **Multi-tenant scaling:** one building is a prototype. One thousand buildings is a product. The architectural assumptions that work at 1 break silently at 100.

  Key problems at scale:
  - **Data isolation** — per-building few-shot store, override history, resident CRM. No cross-contamination. Tenant boundary must be enforced at the DB layer (separate collections or strict tenant_id filtering), not application logic.
  - **Cost attribution** — LLM cost per building per month. Required for per-building pricing, for identifying unprofitable tenants, and for capacity planning.
  - **SLA monitoring per building** — different buildings have different contractual response times. System must surface SLA breaches per building, not globally.
  - **Prompt versioning** — when you improve the classify prompt, you need to A/B test it across a subset of buildings before rolling out globally. One bad prompt change can't degrade all tenants simultaneously.
  - **Operational overhead** — at 1000 buildings, manual intervention per building is impossible. Onboarding, model updates, and incident response must be fully automated or at minimum self-service.

- **Latency / streaming:** Triage runs synchronously — the UI blocks until the full classify→relate→decide→draft pipeline completes. No SSE or WebSocket feedback. At scale (burst of 20+ messages), this becomes a UX problem: manager fires messages and waits with no progress indication. Target: async triage with streaming status updates.

- **Regex fallback is shallow:** when `OPENAI_API_KEY` is not set, triage falls back to regex pattern matching. This only sets priority — no category, no urgency/importance, no sender_type, no grouping, no draft. Messages are essentially unsorted beyond urgent/high/medium/low. Patterns are English-only, so non-English messages all land at medium. Briefing still works but without LLM briefs or meaningful grouping.

### Where it's hardest technically

Not in AI — in data. Resident mapping, ticket history, integrations with accounting systems of acquired companies. LLM is easy. Operational data is hard.