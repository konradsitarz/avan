from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import messages_router, rules_router, briefing_router
from .core import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: cleanup if needed

app = FastAPI(title="Nava Property Management API", lifespan=lifespan)

# CORS middleware for Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(messages_router)
app.include_router(rules_router)
app.include_router(briefing_router)

@app.get("/")
def read_root():
    return {"message": "Nava Property Management API", "status": "running"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
