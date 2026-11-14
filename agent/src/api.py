"""HTTP API сервиса агента. Его вызывает CLI `mr-review` у разработчика.

POST /review: JSON с diff → JSON отчёта (verdict, findings, markdown, токены). Сервис отчёт не хранит —
его сохраняет клиент. Публикации в GitLab здесь нет: это делает ревьюер через `python -m src.cli ... --post`.
"""
from __future__ import annotations

import os
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .agent import render_markdown, review

MAX_DIFF_CHARS = int(os.environ.get("MAX_DIFF_CHARS", "200000"))

app = FastAPI(title="MR Reviewer", version="0.1.0")


class ReviewRequest(BaseModel):
    diff: str = Field(..., max_length=MAX_DIFF_CHARS, description="unified diff MR")
    title: str = ""
    description: str = ""
    llm: Literal["none", "gigachat", "openai"] = Field(
        default_factory=lambda: os.environ.get("MR_REVIEWER_LLM", "none"))
    model: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "default_llm": os.environ.get("MR_REVIEWER_LLM", "none")}


@app.post("/review")
def review_mr(req: ReviewRequest) -> dict:
    res = review(req.diff, req.title, req.description, req.llm, req.model)
    return {**res.to_dict(), "markdown": render_markdown(res)}
