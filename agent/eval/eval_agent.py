"""Оценка агента на data/processed/eval.csv: recall, recall по blocker и доля ложных тревог.

    uv run python agent/eval/eval_agent.py               # только правила
    uv run python agent/eval/eval_agent.py --llm openai  # правила + LLM (ключ в agent/.env)

Метрики считаются отдельно для правил, LLM и вместе. Результат — agent/eval/results/eval_<провайдер>.json.
Стоимость не считается: в результате есть средние токены, по ним её считают отдельно.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AGENT = Path(__file__).resolve().parents[1]
ROOT = AGENT.parent
sys.path.insert(0, str(AGENT))

from src.agent import review  # noqa: E402
from src.cli import load_env  # noqa: E402

EVAL = ROOT / "data/processed/eval.csv"
RESULTS = AGENT / "eval/results"


def as_diff(path: str, hunk: str) -> str:
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n{hunk}\n"


def run_case(case: dict, llm: str) -> dict:
    t0 = time.time()
    res = review(as_diff(case["file_path"], case["diff_context"]), provider=llm)
    return {
        "review_id": case["review_id"],
        "severity": case["severity"],
        "rules": [f.rule for f in res.findings if f.source == "rules"],
        "llm": [f.severity for f in res.findings if f.source == "llm"],
        "llm_calls": res.llm_calls,
        "input_tokens": res.input_tokens,
        "output_tokens": res.output_tokens,
        "seconds": round(time.time() - t0, 2),
        "llm_skipped": bool(res.llm_skipped),
        "llm_errors": res.llm_errors,
        "model": res.model,
    }


def share(cases: list[dict], hit) -> float:
    return round(sum(map(hit, cases)) / len(cases), 3) if cases else 0.0


def metrics(cases: list[dict], key) -> dict:
    with_comment = [c for c in cases if c["severity"] != "none"]
    blocker = [c for c in cases if c["severity"] == "blocker"]
    clean = [c for c in cases if c["severity"] == "none"]
    return {
        "recall": share(with_comment, key),
        "recall_blocker": share(blocker, key),
        "false_alarm": share(clean, key),
    }


def summarize(cases: list[dict], llm: str) -> dict:
    summary = {
        "cases": len(cases),
        "by_severity": {s: sum(c["severity"] == s for c in cases) for s in sorted({c["severity"] for c in cases})},
        "rules": metrics(cases, lambda c: bool(c["rules"])),
    }
    if llm != "none":
        summary["llm"] = metrics(cases, lambda c: bool(c["llm"]))
        summary["all"] = metrics(cases, lambda c: bool(c["rules"] or c["llm"]))
        # вызов был, только если в diff есть добавленные строки и файл не пропущен по лимиту
        called = [c for c in cases if c.get("llm_calls", int(c["input_tokens"] > 0)) > 0]
        summary["model"] = next((c["model"] for c in cases if c["model"]), None)
        summary["llm_calls"] = len(called)
        summary["no_added_lines"] = sum(not c["llm_skipped"] and not c["llm_errors"] and c not in called for c in cases)
        summary["llm_skipped"] = sum(c["llm_skipped"] for c in cases)
        summary["llm_errors"] = sum(bool(c["llm_errors"]) for c in cases)
        if called:
            summary["input_tokens_mean"] = round(st.mean(c["input_tokens"] for c in called))
            summary["output_tokens_mean"] = round(st.mean(c["output_tokens"] for c in called))
            summary["seconds_mean"] = round(st.mean(c["seconds"] for c in called), 1)
    return summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--llm", choices=["none", "openai", "gigachat"], default="none")
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()
    load_env(AGENT / ".env")

    with EVAL.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    workers = args.workers if args.llm != "none" else 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        cases = list(pool.map(lambda r: run_case(r, args.llm), rows))

    summary = summarize(cases, args.llm)
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"eval_{args.llm}.json"
    out.write_text(json.dumps({"summary": summary, "cases": cases}, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"сохранено: {out.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
