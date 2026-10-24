from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import SessionLocal
from app.services.users import get_or_create_dev_user


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Create the dev user at startup so it exists before the first request.
    with SessionLocal() as db:
        get_or_create_dev_user(db)
    yield


app = FastAPI(title="Thyma", lifespan=lifespan)
