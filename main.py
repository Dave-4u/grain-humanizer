"""Grain — FastAPI app: natural-sounding text rewrite."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from engine import humanize

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(
    title="Grain",
    description="Rewrite AI-patterned text so it reads more natural.",
    version="1.0.0",
)


class HumanizeRequest(BaseModel):
    text: str = Field(..., min_length=0, max_length=100_000)
    mode: str = Field(default="casual", pattern="^(casual|professional|academic-light)$")
    strength: int = Field(default=2, ge=1, le=3)


class HumanizeResponse(BaseModel):
    output: str
    changes: list[str]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "grain",
        "llm": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
    }


@app.post("/api/humanize", response_model=HumanizeResponse)
def api_humanize(body: HumanizeRequest):
    if not body.text.strip():
        return HumanizeResponse(output="", changes=["Empty input"])
    try:
        result = humanize(body.text, mode=body.mode, strength=body.strength)
        return HumanizeResponse(output=result.output, changes=result.changes)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
def index():
    index_path = STATIC / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="UI missing")
    return FileResponse(index_path)


# Mount static assets under /static (CSS/JS if split later); index is at /
if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
