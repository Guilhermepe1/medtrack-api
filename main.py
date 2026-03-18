"""
MedTrack Health AI — API Backend
FastAPI + PostgreSQL + Groq + pgvector
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

from routers import auth, exames, dashboard, chat, alertas, perfil, compartilhar

app = FastAPI(
    title="MedTrack Health AI API",
    description="Backend da plataforma de saúde inteligente MedTrack.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — permite o Next.js consumir a API ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "https://medtrack-health-ai.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(auth.router)
app.include_router(exames.router)
app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(alertas.router)
app.include_router(perfil.router)
app.include_router(compartilhar.router)


@app.get("/", tags=["Health Check"])
def health_check():
    return {
        "status": "ok",
        "app": "MedTrack Health AI API",
        "version": "1.0.0",
        "docs": "/docs",
    }
