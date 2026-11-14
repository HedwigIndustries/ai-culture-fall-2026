"""Сценарий ревью: diff → правила → маскирование → LLM → валидация ответа → черновик для ревьюера."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import requests

from .diff import FileDiff, parse_unified_diff
from .llm import SYSTEM_PROMPT, make_client, parse_findings
from .models import SEVERITY_ORDER, Finding
from .rules import mask_for_llm, run_rules

ALLOWED_SEV = {"blocker", "major", "minor", "nit", "question"}
ALLOWED_CAT = {"bug", "security", "performance", "refactor", "style", "question", "suggestion"}
MAX_NITS_PER_MR = 5  # мелких замечаний в ревью большинство (docs/data/02_findings.md); без лимита блокеры тонут
MAX_LLM_TOKENS = 1000  # лимит входа LLM на файл; тот же порог, что в подготовке данных
CHARS_PER_TOKEN = 3.5


@dataclass
class ReviewResult:
    title: str
    files: list[str]
    findings: list[Finding] = field(default_factory=list)
    verdict: str = ""
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    dropped: list[str] = field(default_factory=list)     # что отбросила валидация — для аудита
    llm_skipped: list[str] = field(default_factory=list)  # файлы больше лимита, проверены только правилами
    llm_errors: list[str] = field(default_factory=list)
    model: str | None = None

    def to_dict(self) -> dict:
        return {"title": self.title, "files": self.files, "verdict": self.verdict,
                "findings": [f.to_dict() for f in self.findings], "llm_calls": self.llm_calls,
                "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
                "model": self.model, "dropped_by_validation": self.dropped, "llm_skipped": self.llm_skipped,
                "llm_errors": self.llm_errors}


def verdict_for(findings: list[Finding]) -> str:
    # approve в вариантах нет: «агент ничего не нашёл» не значит «можно мержить».
    if any(f.severity == "blocker" for f in findings):
        return "request_changes"
    if any(f.severity == "major" for f in findings):
        return "needs_attention"
    return "no_major_issues"


HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)")


def _numbered_patch(f: FileDiff) -> str:
    """Diff с номерами строк новой версии файла: модели не нужно считать их самой, и она меньше ошибается."""
    out, n = [], 0
    for line in f.patch.splitlines():
        m = HUNK.match(line)
        if m:
            n = int(m.group(1))
            out.append(line)
        elif line.startswith("-") or line.startswith("\\"):
            out.append(f"     {line}")
        else:
            out.append(f"{n:>4} {line}")
            n += 1
    return "\n".join(out)


def _llm_user_prompt(title: str, description: str, f: FileDiff, already: list[Finding]) -> str:
    already_txt = "\n".join(f"- line {x.line}: [{x.rule}] {x.message}" for x in already if x.path == f.path) or "- нет"
    prompt = (f"MR: {title}\nОписание: {description or '-'}\nФайл: {f.path}\n\n"
              f"ALREADY_FOUND:\n{already_txt}\n\n"
              f"DIFF (слева — номер строки в новой версии файла; его и указывай в line):\n{_numbered_patch(f)}")
    return mask_for_llm(prompt)


def _validate(item: dict, path: str, added_lines: set[int], rule_lines: set[int],
              dropped: list[str]) -> Finding | None:
    """Ответ модели — недоверенные данные: пропускаем только то, что можно привязать к коду MR."""
    line = item.get("line")
    sev = str(item.get("severity", "")).lower()
    cat = str(item.get("category", "")).lower()
    message = str(item.get("message") or "").strip()
    if isinstance(line, bool) or not isinstance(line, int) or line not in added_lines:
        dropped.append(f"{path}:{line} — строки нет среди добавленных")
        return None
    if sev not in ALLOWED_SEV:
        dropped.append(f"{path}:{line} — неизвестный severity {sev!r}")
        return None
    if not message:
        dropped.append(f"{path}:{line} — пустое замечание")
        return None
    cat = cat if cat in ALLOWED_CAT else "suggestion"
    if line in rule_lines:  # строка уже отмечена правилом — второе замечание на ней шумит
        dropped.append(f"{path}:{line} — дубль правила")
        return None
    try:
        confidence = min(max(float(item.get("confidence")), 0.0), 1.0)
    except (TypeError, ValueError):
        confidence = 0.5
    suggestion = item.get("suggestion")
    return Finding(path, line, sev, cat, "llm", message,
                   suggestion if isinstance(suggestion, str) and suggestion.strip() else None,
                   source="llm", confidence=confidence)


def review(diff_text: str, title: str = "", description: str = "", provider: str = "none",
           model: str | None = None) -> ReviewResult:
    files = parse_unified_diff(diff_text)
    findings = run_rules(files)
    res = ReviewResult(title, [f.path for f in files])

    client = make_client(provider, model)
    if client is not None:
        res.model = client.model
        for f in files:
            if not f.path.endswith(".py") or not f.added:
                continue
            tokens = round(len(f.patch) / CHARS_PER_TOKEN)
            if tokens > MAX_LLM_TOKENS:
                res.llm_skipped.append(f"{f.path}: ~{tokens} токенов > {MAX_LLM_TOKENS}, только правила")
                continue
            try:
                out = client.chat(SYSTEM_PROMPT, _llm_user_prompt(title, description, f, findings))
            except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
                # Модель недоступна — ревью по правилам всё равно отдаём.
                res.llm_errors.append(f"{f.path}: {type(exc).__name__}: {exc}")
                continue
            res.llm_calls += 1
            res.input_tokens += out.input_tokens
            res.output_tokens += out.output_tokens
            added_lines = {a.line_no for a in f.added}
            rule_lines = {x.line for x in findings if x.path == f.path and x.source == "rules"}
            for item in parse_findings(out.content):
                finding = _validate(item, f.path, added_lines, rule_lines, res.dropped)
                if finding:
                    findings.append(finding)

    findings.sort(key=lambda x: (-x.rank, x.path, x.line))
    nits = [x for x in findings if x.severity == "nit"]
    for extra in nits[MAX_NITS_PER_MR:]:
        res.dropped.append(f"{extra.path}:{extra.line} — nit сверх лимита {MAX_NITS_PER_MR}")
        findings.remove(extra)
    res.findings = findings
    res.verdict = verdict_for(findings)
    return res


LABEL = {"blocker": "[BLOCKER]", "major": "[MAJOR]", "minor": "[minor]", "nit": "[nit]", "question": "[question]"}
VERDICT_TXT = {"request_changes": "есть блокеры, мержить до исправления не стоит",
               "needs_attention": "есть вероятные баги, нужен взгляд ревьюера",
               "no_major_issues": "серьёзного не найдено (это не approve, решение за ревьюером)"}


def render_markdown(res: ReviewResult) -> str:
    counts = ", ".join(f"{s}: {sum(f.severity == s for f in res.findings)}" for s in reversed(SEVERITY_ORDER[1:]))
    stats = f"Файлов: {len(res.files)} · LLM-вызовов: {res.llm_calls} · токены in/out: {res.input_tokens}/{res.output_tokens}"
    lines = [f"## MR Reviewer, черновик: {res.title}", "",
             f"**Итог:** {VERDICT_TXT[res.verdict]}  ", f"**Найдено:** {counts}  ", stats, ""]
    for f in res.findings:
        src = f"правило {f.rule}" if f.source == "rules" else f"LLM, уверенность {f.confidence:.0%}"
        lines += [f"### {LABEL[f.severity]} `{f.path}:{f.line}` · {f.category} ({src})", f.message]
        if f.suggestion:
            lines += ["", f"Как исправить: {f.suggestion}"]
        lines.append("")
    if not res.findings:
        lines += ["_Замечаний нет._", ""]
    if res.llm_skipped:
        lines += ["**Без LLM (файл больше лимита):** " + "; ".join(res.llm_skipped), ""]
    if res.llm_errors:
        lines += ["**LLM недоступна, ревью только по правилам:** " + "; ".join(res.llm_errors), ""]
    lines += ["---", "_Черновик. В MR публикуется только то, что подтвердит ревьюер._"]
    return "\n".join(lines)


def dump_json(res: ReviewResult) -> str:
    return json.dumps(res.to_dict(), ensure_ascii=False, indent=2)
