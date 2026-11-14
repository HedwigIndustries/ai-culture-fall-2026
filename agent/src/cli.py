"""CLI (из agent/): python -m src.cli --diff examples/mr_payments.diff --title "..." [--llm gigachat] [--post]

Без --post агент только пишет черновик в .mr-review/. С --post ревьюер подтверждает каждое замечание (y / n / e — править
текст) и ещё раз всю пачку перед отправкой. В GitLab уходит только при заданных GITLAB_URL, GITLAB_TOKEN,
--project и --mr, иначе — dry-run в .mr-review/outbox.json. Approve и merge агент не делает ни в каком режиме.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

import requests

from .agent import dump_json, render_markdown, review


def load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def ask_reviewer(findings: list) -> list:
    approved = []
    print("\n=== Подтверждение публикации ===")
    for f in findings:
        print(f"\n[{f.severity}] {f.path}:{f.line} ({f.source})\n  {f.message}")
        ans = input("Опубликовать? [y]es / [n]o / [e]dit (по умолчанию n): ").strip().lower()
        if ans == "e":
            f.message = input("Новый текст: ").strip() or f.message
            ans = "y"
        if ans == "y":
            approved.append(f)
    return approved


def post_to_gitlab(approved: list, project: str, mr: str) -> None:
    url = f"{os.environ['GITLAB_URL']}/api/v4/projects/{quote(project, safe='')}/merge_requests/{mr}/notes"
    for f in approved:
        body = f"`{f.path}:{f.line}` **{f.severity.upper()}** ({f.category}): {f.message}"
        if f.suggestion:
            body += f"\n\n{f.suggestion}"
        requests.post(url, headers={"PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"]}, json={"body": body},
                      timeout=(5, 20)).raise_for_status()


def publish(res, args, out: Path) -> None:
    try:
        approved = ask_reviewer(res.findings)
    except (EOFError, KeyboardInterrupt):
        print("\nПодтверждение прервано, ничего не опубликовано.")
        return
    gitlab_ready = os.environ.get("GITLAB_URL") and os.environ.get("GITLAB_TOKEN") and args.project and args.mr
    if not gitlab_ready:
        (out / "outbox.json").write_text(json.dumps([f.to_dict() for f in approved], ensure_ascii=False, indent=2))
        print(f"Dry-run: {len(approved)} из {len(res.findings)} замечаний записаны в {out / 'outbox.json'}"
              " (GitLab не настроен)")
        return
    if not approved:
        print("Публиковать нечего.")
        return
    target = f"{args.project} !{args.mr}"
    if input(f"Отправить {len(approved)} комментариев в {target}? [y/N]: ").strip().lower() != "y":
        print("Отменено, в GitLab ничего не отправлено.")
        return
    post_to_gitlab(approved, args.project, args.mr)
    print(f"Опубликовано в {target}: {len(approved)}")


def main(argv: list[str] | None = None) -> None:
    load_env()
    p = argparse.ArgumentParser(prog="python -m src.cli")
    p.add_argument("--diff", required=True, help="unified diff MR (git diff / GitLab .diff)")
    p.add_argument("--title", default="")
    p.add_argument("--description", default="")
    p.add_argument("--llm", choices=["none", "gigachat", "openai"], default="none")
    p.add_argument("--model")
    p.add_argument("--out", default=".mr-review")
    p.add_argument("--post", action="store_true", help="подтвердить замечания и опубликовать")
    p.add_argument("--project", help="id или путь проекта в GitLab")
    p.add_argument("--mr", help="iid merge request'а")
    args = p.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    res = review(Path(args.diff).read_text(), args.title, args.description, args.llm, args.model)
    md = render_markdown(res)
    stem = Path(args.diff).stem
    (out / f"{stem}.review.md").write_text(md)
    (out / f"{stem}.review.json").write_text(dump_json(res))
    print(md)
    if res.dropped:
        print("\nОтброшено валидацией:", *res.dropped, sep="\n  ")
    if args.post:
        if not sys.stdin.isatty():
            print("--post работает только в интерактивном терминале: публикацию подтверждает человек. Пропущено.")
            return
        publish(res, args, out)


if __name__ == "__main__":
    main()
