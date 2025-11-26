from fastapi import FastAPI
from src.api.v1.routes import router as v1_router
from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

app.include_router(v1_router, prefix="/api/v1")