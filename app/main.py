from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.exam import router as exam_router
from app.api.practice import router as practice_router
from app.api.questions import router as questions_router
from app.core.config import APP_NAME, APP_VERSION, BASE_DIR
from app.core.database import Base, SessionLocal, engine
from app.services.question_service import init_default_questions


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        init_default_questions(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=app_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["系统"])
def health_check():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
    }


app.include_router(questions_router)
app.include_router(practice_router)
app.include_router(exam_router)


FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"

if FRONTEND_INDEX_FILE.exists():
    assets_dir = FRONTEND_DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        requested_path = (FRONTEND_DIST_DIR / full_path).resolve()
        frontend_root = FRONTEND_DIST_DIR.resolve()

        if (
            requested_path.is_file()
            and requested_path != FRONTEND_INDEX_FILE.resolve()
            and frontend_root in requested_path.parents
        ):
            return FileResponse(requested_path)

        return FileResponse(FRONTEND_INDEX_FILE)
