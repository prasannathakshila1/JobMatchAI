from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging

from app.core.database import connect_db, close_db, get_db
from app.config import get_settings
from app.routers import auth, shared, admin, seeker, hr
from app.services.scheduler import start_scheduler, stop_scheduler

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    await connect_db()

    os.makedirs(f"{settings.upload_dir}/resumes",           exist_ok=True)
    os.makedirs(f"{settings.upload_dir}/job_descriptions",  exist_ok=True)
    os.makedirs("data/models",                              exist_ok=True)
    os.makedirs("data/datasets",                            exist_ok=True)

    start_scheduler(get_db())
    logger.info("✅ JobMatch AI backend started")

    yield

    # ── Shutdown ─────────────────────────────────────────────
    stop_scheduler()
    await close_db()
    logger.info("👋 JobMatch AI backend stopped")


app = FastAPI(
    title="JobMatch AI API",
    description=(
        "Intelligent Recruitment Platform — "
        "6 Job Seeker Features + 8 HR Features + Validated Training Pipeline"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ──────────────────────────────────────────────
app.mount(
    "/uploads",
    StaticFiles(directory=settings.upload_dir),
    name="uploads",
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth.router,   prefix="/api/auth",   tags=["Auth"])
app.include_router(shared.router, prefix="/api",        tags=["Uploads & Notifications"])
app.include_router(admin.router,  prefix="/api/admin",  tags=["Admin"])
app.include_router(seeker.router, prefix="/api/seeker", tags=["Job Seeker"])
app.include_router(hr.router,     prefix="/api/hr",     tags=["HR Recruiter"])


# ── Health ────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "status":  "running",
        "app":     "JobMatch AI API",
        "version": "1.0.0",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
async def health(db=None):
    from app.core.database import get_db
    db = get_db()
    try:
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status":   "ok",
        "database": db_status,
    }