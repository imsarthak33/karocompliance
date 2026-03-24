import os
import sentry_sdk  # type: ignore
from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from app.config import settings  # type: ignore
from app.routers import webhooks, auth, clients, documents, payments  # type: ignore

# Initialize Sentry before the FastAPI app
if settings.ENVIRONMENT == "production" and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment=settings.ENVIRONMENT
    )

app = FastAPI(
    title="KaroCompliance API",
    description="Multi-agent CA WhatsApp automation backend",
    version="1.0.0"
)

# CORS Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Router Inclusions ---
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(clients.router, prefix="/api", tags=["Clients"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(payments.router, prefix="/api", tags=["Payments"])

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}
