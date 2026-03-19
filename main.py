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
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"422 em {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )


@app.get("/", tags=["Health Check"])
def health_check():
    return {
        "status":  "ok",
        "app":     "MedTrack Health AI API",
        "version": "1.0.0",
        "docs":    "/docs",
    }