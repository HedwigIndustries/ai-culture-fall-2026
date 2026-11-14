"""Разбор unified diff (`git diff`, GitLab MR .diff) на файлы и добавленные строки."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

HUNK_RE = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class AddedLine:
    path: str
    line_no: int  # номер строки в новой версии файла
    text: str


@dataclass
class FileDiff:
    path: str
    hunks: list[str] = field(default_factory=list)
    added: list[AddedLine] = field(default_factory=list)

    @property
    def patch(self) -> str:
        return "\n".join(self.hunks)


def parse_unified_diff(diff_text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    cur: FileDiff | None = None
    hunk: list[str] = []
    new_line = 0
    # Сколько строк hunk'а ещё ожидается по заголовку. Пока > 0, строки «--- …» / «+++ …» — это код, а не заголовок
    # файла. Если заголовок врёт (обрезанный hunk), hunk просто тянется до следующего `diff --git`.
    old_left = new_left = 0

    def flush():
        if cur is not None and hunk:
            cur.hunks.append("\n".join(hunk))
        hunk.clear()

    for raw in diff_text.splitlines():
        in_hunk = old_left > 0 or new_left > 0
        if raw.startswith("diff --git"):
            flush()
            cur, old_left, new_left = None, 0, 0
            continue
        if not in_hunk and raw.startswith("+++ "):
            flush()
            path = raw[4:].split("\t")[0].strip()
            cur = FileDiff(path=path[2:] if path.startswith("b/") else path)
            files.append(cur)
            continue
        if cur is None or (not in_hunk and raw.startswith("--- ")):
            continue
        m = HUNK_RE.match(raw)
        if m:
            flush()
            hunk.append(raw)
            new_line = int(m.group(2))
            old_left = int(m.group(1) or 1)
            new_left = int(m.group(3) or 1)
            continue
        if not hunk or raw.startswith("\\"):  # «\ No newline at end of file» — не строка файла
            if hunk:
                hunk.append(raw)
            continue
        hunk.append(raw)
        if raw.startswith("+"):
            cur.added.append(AddedLine(cur.path, new_line, raw[1:]))
            new_line += 1
            new_left -= 1
        elif raw.startswith("-"):
            old_left -= 1
        else:
            new_line += 1
            old_left -= 1
            new_left -= 1
    flush()
    return [f for f in files if f.path != "/dev/null"]
