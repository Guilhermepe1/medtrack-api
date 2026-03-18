"""
MedTrack Health AI — API Backend
FastAPI + PostgreSQL + Groq + pgvector
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

from routers import (
    auth,
    exames,
    dashboard,
    chat,
    alertas,
    perfil,
    compartilhar,
    valores,
    usuarios,
    odonto,
    lgpd,
)

app = FastAPI(
    title="MedTrack Health AI API",
    description="Backend da plataforma de saúde inteligente MedTrack.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8501",
    settings.FRONTEND_URL,
]

ALLOWED_PATTERNS = [
    re.compile(r"https://medtrack.*\.vercel\.app$"),
]


def origin_permitida(origin: str) -> bool:
    if origin in ALLOWED_ORIGINS:
        return True
    return any(p.match(origin) for p in ALLOWED_PATTERNS)


class DynamicCORS(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        origin = request.headers.get("origin", "")
        if request.method == "OPTIONS":
            response = StarletteResponse()
        else:
            response = await call_next(request)
        if origin_permitida(origin):
            response.headers["Access-Control-Allow-Origin"]      = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"]     = "*"
            response.headers["Access-Control-Allow-Headers"]     = "*"
        return response


app.add_middleware(DynamicCORS)

# ── Routers ──
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(exames.router)
app.include_router(valores.router)
app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(alertas.router)
app.include_router(perfil.router)
app.include_router(compartilhar.router)
app.include_router(odonto.router)
app.include_router(lgpd.router)


@app.get("/", tags=["Health Check"])
def health_check():
    return {
        "status":  "ok",
        "app":     "MedTrack Health AI API",
        "version": "1.0.0",
        "docs":    "/docs",
    }