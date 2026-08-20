from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from core.database import engine, Base
from core.config import settings
from api import routes_media, routes_text, routes_reports

# Create SQLite tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0"
)

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (storage directory) so frontend can access generated faces and outputs
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# API Routers
app.include_router(routes_media.router, prefix=f"{settings.API_V1_STR}/media", tags=["media"])
app.include_router(routes_text.router, prefix=f"{settings.API_V1_STR}/text", tags=["text"])
app.include_router(routes_reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
