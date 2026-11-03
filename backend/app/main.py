"""FastAPI application entry point for AI Portfolio Co-Pilot."""

from fastapi import FastAPI

app = FastAPI(
    title="AI Portfolio Co-Pilot API",
    version="0.1.0",
    description="Portfolio tracking and risk analysis for Indian and US stocks.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness check: returns {"status": "ok"} if the API process is up."""
    return {"status": "ok"}
