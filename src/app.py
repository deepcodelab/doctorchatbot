import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from api.v1.routes import router as v1_router
from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

app.include_router(v1_router, prefix="/api/v1")