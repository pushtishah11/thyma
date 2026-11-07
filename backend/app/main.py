from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import SessionLocal
from app.routers import cycles, health, logs, me, meds, tracked_symptoms, trends
from app.services.users import get_or_create_dev_user


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Create the dev user at startup so it exists before the first request.
    with SessionLocal() as db:
        get_or_create_dev_user(db)
    yield


app = FastAPI(title="Thyma", lifespan=lifespan)

# Every route lives under /api, so the Vite dev proxy can forward one prefix.
app.include_router(health.router, prefix="/api")
app.include_router(me.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(tracked_symptoms.router, prefix="/api")
app.include_router(trends.router, prefix="/api")
app.include_router(cycles.router, prefix="/api")
app.include_router(meds.router, prefix="/api")
