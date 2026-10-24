"""Request and response shapes for the API (Pydantic v2)."""

from typing import Literal

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: Literal["ok", "error"]
    db: Literal["ok", "error"]
