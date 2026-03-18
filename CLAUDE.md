# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nava is an AI-native property management triage system for residential managers in Eastern Central Europe. It triages issues from locators via email, SMS, and voice using LLM-powered agents (LangGraph + LangChain) with automatic prioritization, grouping, and escalation.

## Commands

### Full stack (Docker)
```bash
docker compose up -d          # Start all services (MongoDB, backend, frontend)
docker compose down            # Stop all services
docker compose down -v         # Stop and remove database volumes
docker compose up -d --build backend  # Rebuild backend after code changes
```

### Backend (local dev)
```bash
cd backend
uv sync                      # Install dependencies
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (local dev)
```bash
cd frontend
npm install                  # Install dependencies
npm run dev                  # Dev server on :5173
npm run build                # Production build
```

## Architecture

### Backend: FastAPI + Beanie ODM + MongoDB + LangGraph

```
backend/src/
├── core/              # Infrastructure
│   ├── database.py    # MongoDB + Beanie init
│   └── llm.py         # Shared LLM factory (get_llm)
├── models/            # Beanie documents
│   ├── message.py     # Message with triage fields (category, priority, urgency, importance, sender_type, triage_action, group_with, etc.)
│   ├── briefing.py    # Cached briefing with stale flag
│   └── rule.py        # Automation rules
├── agents/            # LangGraph agents
│   └── triage/        # Triage agent: classify → relate → decide → draft
│       ├── state.py   # TriageState TypedDict
│       ├── graph.py   # LangGraph workflow with conditional edges
│       ├── nodes/     # classify (structured output), relate (DB lookup + LLM cross-sender), decide (rules), draft (LLM)
│       └── prompts/   # System/user prompts for classify and draft
├── services/          # Business logic
│   ├── briefing_service.py  # Cached briefing with group_with + Eisenhower sorting, LangGraph generation
│   └── triage_service.py    # Orchestrates triage agent, regex fallback when no API key
├── routers/           # Thin HTTP endpoints
│   ├── messages.py    # CRUD + DELETE /all for simulation reset
│   ├── briefing.py    # Delegates to BriefingService
│   └── rules.py       # Automation rules CRUD
└── main.py            # FastAPI app with CORS and lifespan
```

### Frontend: Vue 3 (Composition API) + Vite + Axios
- Multi-route SPA: Briefing, Feed, Timeline, Respond, Rules views
- Briefing view shows grouped issues with timeline, triage reasoning, and LLM briefs
- FireBar simulation component: collapsible bottom bar with message firing, custom compose, and clear all
- API base URL configured via `VITE_API_URL` env var (fallback: `http://localhost:8000`)
- No state management library; local component state only

### Key Agents

**Triage Agent** (runs on every new message):
- `classify` — LLM with structured output (Pydantic schema) → category, priority, urgency, importance, sender_type
- `relate` — Same-sender grouping (free, no LLM) + LLM cross-sender semantic matching (structured output). Cross-sender match fires only when: no same-sender match, cross-sender candidates exist in same category, and API key is set. Candidates capped at 5, content truncated, temperature 0.0.
- `decide` — Rule-based: escalate (urgent/safety/plumbing/electrical/compliance/3+ followups) / group / standard
- `draft` — LLM generates channel-appropriate response (skipped for escalations)
- Conditional edges: escalations skip drafting and go straight to END

**Briefing Agent** (runs when cached briefing is stale):
- Groups messages by `group_with` (chain-resolved) with sender+category fallback
- Sorts by Eisenhower quadrant (urgency × importance), then life-threat categories, then priority
- Generates executive summary + per-issue briefs with timeline context
- Cached in MongoDB, invalidated on any message create/update/delete

### Classification Strategy
Messages are classified on three axes:
- **Priority** (urgent/high/medium/low) — overall triage level, drives escalation rules
- **Urgency** (immediate/today/this_week/no_rush) — can it wait? Is damage growing right now?
- **Importance** (critical/high/moderate/low) — how serious if ignored?

Urgency × importance map to Eisenhower quadrants for briefing sort order:
- urgent+important (do first) → urgent+not_important (delegate) → not_urgent+important (schedule) → neither (deprioritize)
- Within same quadrant: life-threat categories (safety/plumbing/electrical) sort first

`followup_count >= 3` forces priority=urgent but does NOT override urgency/importance — a broken gate with 3 followups is urgent priority but not "immediate" urgency like active flooding.

### Key Business Rules
- Water/leak/plumbing issues are ALWAYS urgent (time-critical damage)
- Construction failures, health hazards, significant property loss → urgent
- Safety, electrical, compliance, plumbing categories → auto-escalate
- `followup_count >= 3` → auto-escalate to urgent priority
- `group_with` field drives briefing grouping with chain resolution + sender||category fallback
- Cross-sender grouping uses LLM semantic matching ("same physical issue" = same problem + same location)
- Falls back to regex-based triage when `OPENAI_API_KEY` is not set

## Environment Variables

See `.env.example`. Key vars:
- `MONGODB_URL` — MongoDB connection string (default: `mongodb://mongodb:27017`)
- `DATABASE_NAME` — Database name (default: `nava`)
- `VITE_API_URL` — Backend URL for frontend (default: `http://localhost:8000`)
- `OPENAI_API_KEY` — Required for LLM-powered triage and briefing (falls back to regex without it)
- `LLM_MODEL` — Model to use (default: `gpt-4o-mini`)

## Services (Docker Compose)

- **MongoDB** (:27017) — mongo:7.0
- **Backend** (:8000) — Python 3.14, uv-based image
- **Frontend** (:5173) — node:20-alpine, runs dev server in container

## API

- `GET /` — Status
- `GET /api/health` — Health check
- `GET|POST /api/messages` — List/create messages (POST runs triage agent)
- `GET|PUT|DELETE /api/messages/{id}` — Single message operations
- `DELETE /api/messages/all` — Clear all messages and briefings (simulation reset)
- `GET /api/briefing` — Get briefing (returns cached or regenerates if stale)
- `GET|POST /api/rules` — List/create automation rules
- `GET|PUT|DELETE /api/rules/{id}` — Single rule operations
- Swagger docs at `http://localhost:8000/docs`
