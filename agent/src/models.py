from __future__ import annotations

from dataclasses import dataclass, asdict

# Та же шкала, что и в подготовленном датасете (severity / severity_id)
SEVERITY_ORDER = ["none", "question", "nit", "minor", "major", "blocker"]


@dataclass
class Finding:
    path: str
    line: int
    severity: str          # blocker | major | minor | nit | question
    category: str          # security | bug | performance | refactor | style | question | suggestion
    rule: str              # id правила или "llm"
    message: str
    suggestion: str | None = None
    source: str = "rules"  # rules | llm
    confidence: float = 1.0

    @property
    def rank(self) -> int:
        return SEVERITY_ORDER.index(self.severity)

    def to_dict(self) -> dict:
        return asdict(self)
