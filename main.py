"""
SolarMind AI — FastAPI Backend
Smart Energy AI platform — RAG + Image Generation proxy

🚀 Run:
    pip install fastapi uvicorn requests
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

📋 Then open: http://localhost:8000
🧪 API Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from routes.chat import router as chat_router
from routes.image import router as image_router
from routes.assistant import router as assistant_router
from routes.signal import router as signal_router

app = FastAPI(
    title="SolarMind AI API",
    description="Smart Energy AI platform — RAG + Image Generation proxy",
    version="2.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# ─── CORS ──────────────────────────────────────────────────────────
# Allow frontend to communicate; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "file://",
        "*"  # Development only - remove in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ROUTERS ────────────────────────────────────────────────────────
app.include_router(chat_router,      prefix="/api")
app.include_router(image_router,     prefix="/api")
app.include_router(assistant_router, prefix="/api")
app.include_router(signal_router,    prefix="/api")


# ─── HEALTH & INFO ──────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    """Serve the frontend HTML"""
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend.html")
    try:
        with open(frontend_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Frontend not found</h1>"


@app.get("/api/status")
def health_check():
    """
    Health check endpoint
    Returns API status and available endpoints
    """
    return {
        "status": "online",
        "platform": "SolarMind AI",
        "version": "2.1.0",
        "features": [
            "RAG Chat Assistant",
            "Image Generation",
            "Smart Auto-Router",
            "Signal Prediction"
        ],
        "endpoints": {
            "chat": "POST /api/chat",
            "image": "POST /api/image",
            "assistant": "POST /api/assistant (auto-routing)",
            "signal": "POST /api/signal/predict",
            "docs": "GET /docs"
        },
        "external_apis": {
            "rag": "https://freddyouedraogo-smart-energy-api.hf.space/chat",
            "image": "https://Soso26-generator-api.hf.space/generate",
            "signal": "https://freddyouedraogo-modele-signal-ia.hf.space/predict"
        }
    }


@app.get("/health")
def simple_health():
    """Simple health endpoint"""
    return {"status": "ok"}