# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nava is an AI-native property management triage system for residential managers in Eastern Central Europe. It triages issues from locators via email, SMS, and voice with automatic prioritization and escalation.

## Commands

### Full stack (Docker)
```bash
docker-compose up -d        # Start all services (MongoDB, backend, frontend)
docker-compose down          # Stop all services
docker-compose down -v       # Stop and remove database volumes
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

**Backend**: FastAPI + Beanie ODM + MongoDB (async throughout via Motor driver)
- `backend/src/main.py` — App initialization with async lifespan for DB init, CORS config, health endpoints
- `backend/src/database.py` — MongoDB connection via `AsyncIOMotorClient`, Beanie initialization
- `backend/src/models/message.py` — `Message` Beanie Document with enums `MessageType` (EMAIL/SMS/VOICE) and `Priority` (LOW/MEDIUM/HIGH/URGENT)
- `backend/src/routers/messages.py` — REST CRUD at `/api/messages` with auto-escalation business logic

**Frontend**: Vue 3 (Composition API) + Vite + Axios
- Single-route SPA: `MessageList` component handles all message CRUD
- API base URL configured via `VITE_API_URL` env var (fallback: `http://localhost:8000`)
- No state management library; local component state only

**Key business rule**: Messages with `followup_count >= 3` are automatically escalated to URGENT priority on creation.

## Environment Variables

See `.env.example`. Key vars:
- `MONGODB_URL` — MongoDB connection string (default: `mongodb://mongodb:27017`)
- `DATABASE_NAME` — Database name (default: `nava`)
- `VITE_API_URL` — Backend URL for frontend (default: `http://localhost:8000`)

## Services (Docker Compose)

- **MongoDB** (:27017) — mongo:7.0
- **Backend** (:8000) — Python 3.14, uv-based image
- **Frontend** (:5173) — node:20-alpine, runs dev server in container

## API

- `GET /` — Status
- `GET /api/health` — Health check
- `GET|POST /api/messages` — List/create messages
- `GET|PUT|DELETE /api/messages/{id}` — Single message operations
- Swagger docs at `http://localhost:8000/docs`
