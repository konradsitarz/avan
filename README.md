# Nava — AI-Native Property Management Triage

Intelligent triage system for residential property managers in Eastern Central Europe. Nava processes incoming messages from residents via email, SMS, and voice — classifying, grouping, and prioritizing them using LLM-powered agents so the manager sees a clear briefing instead of raw noise.

## What It Does

1. **Messages come in** from residents (email, SMS, voice transcription)
2. **Triage agent** classifies each message: category, priority, sender type
3. **Relates** to existing tickets from the same sender/category
4. **Decides** action: escalate, group with existing issue, or standard handling
5. **Drafts** a channel-appropriate response (skipped for escalations — admin decides)
6. **Briefing** groups related messages into issue threads with timelines and LLM-written summaries

## Quick Start

```bash
# Clone and start
git clone <repository-url>
cd nava

# Optional: set OpenAI key for LLM-powered triage (works without it using regex fallback)
echo "OPENAI_API_KEY=sk-..." > .env

# Start everything
docker compose up -d
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

## Tech Stack

| Layer | Stack |
|-------|-------|
| **Backend** | Python 3.14, FastAPI, Beanie ODM, MongoDB, LangGraph + LangChain |
| **Frontend** | Vue 3 (Composition API), Vite, Axios |
| **LLM** | OpenAI GPT-4o-mini (configurable via `LLM_MODEL`) |
| **Infra** | Docker Compose (MongoDB, backend, frontend) |

## Project Structure

```
backend/src/
├── core/              # Database init, shared LLM factory
├── models/            # Message, Briefing, Rule (Beanie documents)
├── agents/triage/     # LangGraph: classify → relate → decide → draft
│   ├── nodes/         # Each step as a separate module
│   └── prompts/       # LLM prompts for classify and draft
├── services/          # BriefingService (cached + grouped), TriageService
├── routers/           # Thin HTTP endpoints
└── main.py

frontend/src/
├── views/             # Briefing, Feed, Timeline, Respond, Rules
├── components/        # FireBar (simulation bar)
├── api.js             # Axios API client
└── App.vue            # Layout with sidebar + router
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/messages` | Create message (runs triage agent) |
| `GET` | `/api/messages` | List all messages |
| `GET` | `/api/messages/{id}` | Get single message |
| `PUT` | `/api/messages/{id}` | Update message |
| `DELETE` | `/api/messages/{id}` | Delete message |
| `DELETE` | `/api/messages/all` | Clear all messages + briefings (simulation reset) |
| `GET` | `/api/briefing` | Get briefing (cached, regenerates when stale) |
| `GET/POST` | `/api/rules` | List/create automation rules |
| `GET/PUT/DELETE` | `/api/rules/{id}` | Single rule operations |

## Triage Agent

LangGraph workflow with conditional edges:

```
classify → relate → decide
                      ├── escalate  → END (no draft, admin decides)
                      ├── group     → draft → END
                      └── standard  → draft → END
```

- **classify**: LLM with structured output (Pydantic) → category, priority, sender_type
- **relate**: DB lookup for related tickets by sender + category
- **decide**: Rule-based escalation (urgent/safety/plumbing/electrical/compliance/3+ followups)
- **draft**: LLM generates response appropriate for the channel (SMS = 160 chars, email = 2-4 sentences)

### Priority Rules

| Priority | When |
|----------|------|
| **Urgent** | Safety, construction failure, water/leak damage, gas, fire, electrical, health hazards, mold, building code violations, legal threats, 3+ follow-ups |
| **High** | Elevator/gate failure, repeated complaints, deadline pressure, HVAC in extreme weather |
| **Medium** | Standard maintenance, general complaints |
| **Low** | Billing, parking, admin, informational |

## Briefing

Messages are grouped by **(sender + category)** into issue threads. Each issue shows:
- LLM-written brief synthesizing the full thread
- Triage reasoning (why this priority/action was chosen)
- Timeline of all messages in the thread
- Category, priority, assignment status

Briefings are cached in MongoDB and only regenerated when messages change.

## Simulation

The app includes a built-in simulation bar (bottom of screen) for testing:
- **Magazine**: Pre-loaded Polish property management messages
- **Fire modes**: Single, burst (3), auto-fire with configurable rate
- **Custom compose**: Send arbitrary messages through the triage pipeline
- **Clear all**: Reset DB for fresh simulation runs
- **Simulated clock**: Shows time progression as messages arrive

## Development

```bash
# Backend (local)
cd backend && uv sync && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (local)
cd frontend && npm install && npm run dev

# Rebuild after backend changes
docker compose up -d --build backend
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://mongodb:27017` | MongoDB connection string |
| `DATABASE_NAME` | `nava` | Database name |
| `VITE_API_URL` | `http://localhost:8000` | Backend URL for frontend |
| `OPENAI_API_KEY` | — | Required for LLM triage/briefing |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model to use |

## License

Proprietary — Nava Property Management
