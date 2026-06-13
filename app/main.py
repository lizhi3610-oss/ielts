from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exam import router as exam_router
from app.api.practice import router as practice_router
from app.api.questions import router as questions_router
from app.core.config import APP_NAME, APP_VERSION
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