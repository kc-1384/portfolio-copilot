"""FastAPI application entry point for AI Portfolio Co-Pilot."""

from typing import Annotated

from fastapi import Depends, FastAPI, Response, status

from app.core.db import ping_database

app = FastAPI(
    title="AI Portfolio Co-Pilot API",
    version="0.1.0",
    description="Portfolio tracking and risk analysis for Indian and US stocks.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness check: returns {"status": "ok"} if the API process is up."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["system"])
def ready(
    response: Response,
    database_ok: Annotated[bool, Depends(ping_database)],
) -> dict[str, str]:
    """Readiness check: the API is up AND can reach the database. Returns 503 if not."""
    if not database_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "unreachable"}
    return {"status": "ok", "database": "ok"}
