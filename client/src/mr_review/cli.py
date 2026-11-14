"""mr-review: отправляет diff в сервис MR Reviewer и сохраняет черновик ревью в .mr-review/ репозитория.

    mr-review [ПУТЬ] [--base origin/main]   diff ветки в репозитории (по умолчанию — текущая директория)
    git diff ... | mr-review -              свой diff из stdin
    mr-review --diff fix.diff               свой diff из файла

Код возврата: 1 — есть блокеры (request_changes), 2 — ошибка, 0 — иначе.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

DEFAULT_URL = "http://localhost:8000"
OUT_DIR = ".mr-review"


class CliError(Exception):
    pass


def git(cwd: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise CliError(r.stderr.strip() or f"git {' '.join(args)} завершился с ошибкой")
    return r.stdout


def repo_root(path: Path) -> Path | None:
    try:
        return Path(git(path, "rev-parse", "--show-toplevel").strip())
    except (CliError, FileNotFoundError):
        return None


def branch_diff(path: Path, base: str) -> tuple[Path, str, str]:
    root = repo_root(path)
    if root is None:
        raise CliError(f"{path} — не git-репозиторий")
    merge_base = git(root, "merge-base", base, "HEAD").strip()
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    # от merge-base до рабочей копии: коммиты ветки и незакоммиченные изменения
    return root, git(root, "diff", merge_base), branch


def request_review(url: str, diff: str, title: str) -> dict:
    body = json.dumps({"diff": diff, "title": title}).encode()
    req = urllib.request.Request(f"{url.rstrip('/')}/review", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise CliError(f"сервис ответил {exc.code}: {exc.read().decode(errors='replace')[:300]}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise CliError(f"сервис {url} недоступен: {exc}") from exc


def save(root: Path, report: dict) -> Path:
    out = root / OUT_DIR
    out.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (out / f"{stamp}.md").write_text(report["markdown"])
    (out / f"{stamp}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    (out / "latest.md").write_text(report["markdown"])
    if repo_root(root) and subprocess.run(["git", "check-ignore", "-q", OUT_DIR], cwd=root).returncode != 0:
        print(f"подсказка: добавьте {OUT_DIR}/ в .gitignore", file=sys.stderr)
    return out


def run(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mr-review", description="Ревью diff через сервис MR Reviewer")
    p.add_argument("path", nargs="?", default=".", help="директория репозитория или «-» для diff из stdin")
    p.add_argument("--diff", help="файл с diff")
    p.add_argument("--base", default="origin/main", help="ветка, от которой считается diff (по умолчанию origin/main)")
    p.add_argument("--url", default=os.environ.get("MR_REVIEWER_URL", DEFAULT_URL), help="адрес сервиса")
    args = p.parse_args(argv)

    try:
        if args.diff or args.path == "-":
            diff = Path(args.diff).read_text() if args.diff else sys.stdin.read()
            root = repo_root(Path.cwd()) or Path.cwd()
            title = Path(args.diff).name if args.diff else "stdin"
        else:
            root, diff, title = branch_diff(Path(args.path).resolve(), args.base)
        if not diff.strip():
            print("изменений нет")
            return 0
        report = request_review(args.url, diff, title)
    except (CliError, OSError) as exc:
        print(f"mr-review: {exc}", file=sys.stderr)
        return 2

    print(report["markdown"])
    out = save(root, report)
    print(f"\nсохранено: {out / 'latest.md'}", file=sys.stderr)
    return 1 if report.get("verdict") == "request_changes" else 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
