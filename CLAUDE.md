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
│   ├── message.py     # Message with triage fields (category, sender_type, triage_action, etc.)
│   ├── briefing.py    # Cached briefing with stale flag
│   └── rule.py        # Automation rules
├── agents/            # LangGraph agents
│   └── triage/        # Triage agent: classify → relate → decide → draft
│       ├── state.py   # TriageState TypedDict
│       ├── graph.py   # LangGraph workflow with conditional edges
│       ├── nodes/     # classify (structured output), relate (DB lookup), decide (rules), draft (LLM)
│       └── prompts/   # System/user prompts for classify and draft
├── services/          # Business logic
│   ├── briefing_service.py  # Cached briefing with sender+category grouping, LangGraph generation
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
- `classify` — LLM with structured output (Pydantic schema) → category, priority, sender_type
- `relate` — DB query for related tickets by sender + category
- `decide` — Rule-based: escalate (urgent/safety/plumbing/electrical/compliance/3+ followups) / group / standard
- `draft` — LLM generates channel-appropriate response (skipped for escalations)
- Conditional edges: escalations skip drafting and go straight to END

**Briefing Agent** (runs when cached briefing is stale):
- Groups messages by (sender, category) into issue threads
- Generates executive summary + per-issue briefs with timeline context
- Cached in MongoDB, invalidated on any message create/update/delete

### Key Business Rules
- Water/leak/plumbing issues are ALWAYS urgent (time-critical damage)
- Construction failures, health hazards, significant property loss → urgent
- Safety, electrical, compliance, plumbing categories → auto-escalate
- `followup_count >= 3` → auto-escalate to urgent
- Briefing groups messages by sender+category into single issue threads with timeline
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
