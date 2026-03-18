# Nava - Property Management Triage System

AI-native property management platform for residential managers in Eastern Central Europe. Triages issues from locators through multiple channels (email, SMS, voice), with automatic prioritization and escalation.

## Features

- Multi-channel message intake (Email, SMS, Voice)
- Automatic priority assignment
- Auto-escalation rules (3rd follow-up increases priority)
- Message tracking and management
- Admin notifications for urgent issues

## Tech Stack

**Backend:**
- FastAPI (Python)
- MongoDB with Beanie ODM
- Motor (async MongoDB driver)
- UV for package management

**Frontend:**
- Vue 3
- Vite
- Axios

**Infrastructure:**
- Docker & Docker Compose
- MongoDB

## Project Structure

```
nava/
├── backend/
│   ├── src/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── message.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── messages.py
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── main.py
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── MessageList.vue
│   │   ├── App.vue
│   │   └── main.js
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nava
```

2. Start the services:
```bash
docker-compose up -d
```

This will start:
- MongoDB on `localhost:27017`
- Backend API on `http://localhost:8000`
- Frontend on `http://localhost:5173`

3. Access the application:
- Frontend: http://localhost:5173
- API Documentation: http://localhost:8000/docs
- API Health Check: http://localhost:8000/api/health

### Development

**Backend (with uv):**

```bash
cd backend

# Install dependencies
uv sync

# Run development server
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## API Endpoints

### Messages

- `GET /api/messages` - List all messages
- `POST /api/messages` - Create a new message
- `GET /api/messages/{id}` - Get a specific message
- `PUT /api/messages/{id}` - Update a message
- `DELETE /api/messages/{id}` - Delete a message

### Health

- `GET /` - API status
- `GET /api/health` - Health check

## Message Model

```json
{
  "type": "email|sms|voice",
  "sender": "string",
  "content": "string",
  "priority": "low|medium|high|urgent",
  "followup_count": 0,
  "created_at": "ISO 8601 datetime",
  "assigned_to": "string (optional)"
}
```

## Auto-Escalation Rules

- Messages with `followup_count >= 3` are automatically escalated to URGENT priority
- Timezone-aware timestamps (UTC)

## Stopping the Application

```bash
docker-compose down
```

To remove volumes (database data):
```bash
docker-compose down -v
```

## License

Proprietary - Nava Property Management

## Support

For issues and questions, contact the development team.
