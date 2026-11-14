# Архитектура

Код агента — пакет `agent/src`. CLI (`src/cli.py`) и HTTP API (`src/api.py`) — тонкие обёртки над функцией `review()`.

```
unified diff
   │
   ▼
diff.parse_unified_diff ──► FileDiff[] (добавленные строки с номерами в новой версии файла)
   │
   ├─► rules.run_rules ──────────────► Finding[] (source="rules")
   │
   └─► для каждого .py-файла (если провайдер не none):
         rules.mask_for_llm → llm.make_client(...).chat(SYSTEM_PROMPT, prompt)
         → llm.parse_findings → agent._validate ──► Finding[] (source="llm")
   │
   ▼
agent.review: сортировка по severity, лимит 5 nit, verdict_for ──► ReviewResult
   │
   ├─► agent.render_markdown / dump_json ──► mr-review: .mr-review/<дата-время>.md / .json + latest.md;
   │                                          отладочный cli: <stem>.review.md / .json
   ├─► cli: --post → подтверждение человеком → GitLab или .mr-review/outbox.json
   └─► api (FastAPI): POST /review → JSON + markdown (без публикации)
```

| Модуль | Ответственность |
|---|---|
| `diff.py` | разбор unified diff, номера строк, `\ No newline`, удалённые файлы |
| `rules.py` | 38 правил (`Rule`): SEC, BUG, STY; маскирование секретов и PAN |
| `llm.py` | `OpenAICompatClient`, `GigaChatClient`, `SYSTEM_PROMPT`, `parse_findings` |
| `agent.py` | оркестрация `review()`, валидация ответа модели, вердикт, рендер |
| `models.py` | `Finding`, шкала `SEVERITY_ORDER` |
| `cli.py` | CLI, загрузка `.env`, подтверждение и публикация |
| `api.py` | FastAPI `/health`, `/review` |
| `../eval/eval_agent.py` | метрики на `data/processed/eval.csv`, результаты в `../eval/results/` |

**Инварианты:**
- агент не делает approve и merge;
- ответ модели недоверенный: строка должна быть среди добавленных, severity — из шкалы;
- ошибка LLM не ломает ревью: правила отдаются всегда;
- в модель уходит только замаскированный текст.

**Шкала severity:** `blocker > major > minor > nit > question` (+ `none` в данных). Вердикт: `request_changes` (есть blocker), `needs_attention` (есть major), `no_major_issues`.

**Развёртывание:** Docker только для агента (`agent-api`, `agent-check`). Данные и ноутбуки — локально через uv. CLI `mr-review` (`client/`) ставится у разработчика отдельно.
