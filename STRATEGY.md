# Nava — Strategy

## Vision

AI-native property management triage for residential managers in Eastern Central Europe. Nava replaces the chaotic inbox of emails, SMS, and voicemails with an intelligent system that classifies, groups, and prioritizes issues automatically — so the manager sees a clear briefing instead of raw noise.

## Core Loop

```
Message arrives (email/SMS/voice)
    → Triage Agent classifies (category, priority, sender type)
    → Relates to existing tickets (same sender + category)
    → Decides action (escalate / group / standard)
    → Drafts channel-appropriate response (skipped for escalations)
    → Stored in DB with full triage metadata

Manager opens app
    → Briefing shows grouped issues (not individual messages)
    → Each issue has a timeline, LLM-written brief, and triage reasoning
    → Manager reviews issue-by-issue, not message-by-message
```

## Architecture Principles

1. **Agents over rules** — LLM-powered classification with structured output, regex as fallback only
2. **Issues, not messages** — Messages are grouped by (sender, category) into issue threads. The briefing shows issues with timelines, not flat message lists.
3. **Cache-then-invalidate** — Briefing is generated once and cached. Any message change marks it stale. No regeneration on every page load.
4. **Graceful degradation** — Everything works without OPENAI_API_KEY (regex triage, template briefing). LLM adds intelligence but isn't required.
5. **Thin routers, fat services** — Routers are 3-5 lines. Business logic lives in services. Agent logic lives in agents/.

## Triage Priority Rules

| Priority | Triggers |
|----------|----------|
| **Urgent** | Safety, construction failure, health hazards, water/leak damage (time-critical), gas, fire, electrical danger, mold/asbestos, building code violations, legal threats, 3+ follow-ups |
| **High** | Infrastructure failure (elevator, gate), repeated complaints, deadline pressure, broken HVAC in extreme weather |
| **Medium** | Standard maintenance, general complaints |
| **Low** | Billing, parking, admin, informational |

Auto-escalation categories (always escalate regardless of LLM priority): safety, electrical, compliance, plumbing.

## Tech Stack

- **Backend**: Python 3.14, FastAPI, Beanie ODM, MongoDB, LangGraph + LangChain
- **Frontend**: Vue 3 (Composition API), Vite, Axios
- **LLM**: OpenAI GPT-4o-mini (configurable via LLM_MODEL env var)
- **Infra**: Docker Compose (MongoDB, backend, frontend)

## What's Next

- Voice transcription pipeline (Whisper integration for incoming calls)
- Resident portal for status updates
- Assignment engine (auto-assign to maintenance staff based on category)
- Notification channels (push to manager's phone for urgent escalations)
- Learning from manager decisions (feedback loop to improve triage accuracy)
- Multi-property support with per-building context
