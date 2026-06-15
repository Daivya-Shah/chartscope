import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router

APP_NAME = os.getenv("APP_NAME", "ChartScope")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Clinical NLP pipeline API for ChartScope",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }
