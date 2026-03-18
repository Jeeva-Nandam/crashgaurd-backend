from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import connect_db, close_db, get_database
from app.core.config import settings
from app.api.auth_routes import router as auth_router
from app.api.analysis_routes import router as analysis_router
from app.api.admin_routes import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    await connect_db()
    await create_indexes()
    yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    await close_db()


async def create_indexes():
    """Create MongoDB indexes for performance and constraints."""
    db = get_database()

    # users: unique email index
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("created_at")

    # analyses: index by user + date for fast history queries
    await db["analyses"].create_index([("user_id", 1), ("created_at", -1)])

    # refresh_tokens: index for fast lookup + cleanup
    await db["refresh_tokens"].create_index("token", unique=True)
    await db["refresh_tokens"].create_index("user_id")

    print("✅ MongoDB indexes created")


app = FastAPI(
    title="CrashGuard API",
    description="Startup financial crash prediction engine with user authentication",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(analysis_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "2.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
