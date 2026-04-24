import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_pool, close_pool, init_db
from app.routes import chat, documents


# -----------------------------------------------
# Lifespan (startup / shutdown)
# -----------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    print("\n[STARTUP] Starting Life Insurance AI Agent...")
    print("=" * 50)

    # Initialize PostgreSQL connection pool
    init_pool()

    # Create database tables
    init_db()

    # Ensure Documents directory exists
    os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
    print(f"[INFO] Documents directory: {settings.DOCUMENTS_DIR}")

    print("=" * 50)
    print("[OK] Application ready!\n")

    yield

    # Shutdown
    print("\n[SHUTDOWN] Shutting down...")
    close_pool()


# -----------------------------------------------
# FastAPI Application
# -----------------------------------------------

app = FastAPI(
    title="Life Insurance AI Agent",
    description="AI-powered conversational assistant for life insurance support",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(settings.BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(settings.BASE_DIR, "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# Include routers
app.include_router(chat.router)
app.include_router(documents.router)


# -----------------------------------------------
# Root Route - Serve Frontend
# -----------------------------------------------

@app.get("/")
async def root(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse(name="index.html", request=request)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Life Insurance AI Agent"}
