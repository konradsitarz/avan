# Nava — Strategy

## Vision

Nava is an AI-native triage layer for residential property managers. The core loop: messages arrive from residents (email, SMS, voice) → an LLM agent classifies, groups, and prioritizes them → the manager gets a structured briefing instead of raw noise. Every manager correction feeds back as a few-shot example, so the system improves with use.

The goal is not to replace the manager — it's to eliminate the cognitive overhead of reading 50 unstructured messages and deciding what matters. Nava handles the sorting; the manager handles the judgment.

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

## What's Next

- Resident CRM: map phone/email → resident → unit → building
- Real intake: Twilio webhook (SMS), IMAP/SendGrid (email)
- NLU module for voice channel (transcription + intent extraction from incoming calls)
- Multi-tenant: each building has its own context, history, communication style
- Per-building learning: admin overrides improve classification for that building only — not globally
- Metrics: response time, triage accuracy, cost per ticket per building
- Assignment engine (auto-assign to maintenance staff based on category)
- Notification channels (push to manager's phone for urgent escalations)
- CEE multilingual: PL/EN/UA/RO — draft in sender's language, admin interface in their language. Not just translation — cultural context.
- Resident portal: resident sees status of their ticket + voting system for building matters (renovations, rule changes, budget proposals, common-area decisions). Results feed into briefing so the manager sees consensus before acting.
- Event calendar: recurring events (inspections, fire alarm tests, garbage pickup, meter readings) and one-off planned events (scheduled repairs, lease signings, contractor visits). Surfaced in briefing so the manager sees upcoming events alongside active issues. Triage agent can correlate incoming messages with scheduled events (e.g., resident complaint about noise → scheduled renovation today). Model: `Event` document with recurrence rules (RRULE or simple: daily/weekly/monthly/yearly + day), linked to building/unit.
- Override UX: currently post-hoc only (manager corrects after triage). No "flag for human review" flow, no inline correction during briefing review. Target: triage confidence score → low-confidence items surface for review before briefing is finalized.

## Hard Problems

- **M&A integration:** every acquired company has different processes, different historical data, different category naming, different SLAs. System must adapt to a new building in <1 day — onboarding can't require manual rule configuration. Requires: auto-discovery of categories from historical data, ticket migration from legacy systems, per-building prompt tuning without regression on other buildings.

- **Latency / streaming:** Triage runs synchronously — the UI blocks until the full classify→relate→decide→draft pipeline completes. No SSE or WebSocket feedback. At scale (burst of 20+ messages), this becomes a UX problem: manager fires messages and waits with no progress indication. Target: async triage with streaming status updates.

- **Regex fallback is shallow:** when `OPENAI_API_KEY` is not set, triage falls back to regex pattern matching. This only sets priority — no category, no urgency/importance, no sender_type, no grouping, no draft. Messages are essentially unsorted beyond urgent/high/medium/low. Patterns are Polish-only, so non-PL messages all land at medium. Briefing still works but without LLM briefs or meaningful grouping.

### Where it's hardest technically

Not in AI — in data. Resident mapping, ticket history, integrations with accounting systems of acquired companies. LLM is easy. Operational data is hard.
