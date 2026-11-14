# Proposal

## Why

Первичное ревью MR занимает время senior-разработчиков и нестабильно ловит дефекты, критичные для банка: секреты, ПДн в логах, SQL-инъекции, и тратит время на стиль кода. Нужен агент, который за минуты готовит черновик ревью, а решение о публикации оставляет человеку.

## What Changes

- Сервис агента: diff → правила (безопасность, ошибки, 30 правил кодстайла) → LLM → валидация ответа → вердикт и черновик ревью; HTTP API.
- CLI `mr-review` для разработчика: ставится глобально, отправляет diff ветки или готовый diff в сервис, печатает черновик и сохраняет его в `.mr-review/`.
- Публикация замечаний в GitLab — только после подтверждения человеком.
- Оценка качества агента на eval-наборе: recall и ложные тревоги.
- Запуск: uv локально, Docker — только сервис агента.

## Capabilities

### New Capabilities
- `review-agent`: разбор diff, правила, LLM-слой с маскированием и валидацией, вердикт и черновик, публикация после подтверждения человеком.
- `agent-evaluation`: метрики качества на eval-наборе.
- `agent-delivery`: HTTP API, CLI `mr-review`, окружение uv, Docker Compose.

### Modified Capabilities

## Impact

- **Вход:**
  - использование — diff MR от разработчика через `mr-review` или `POST /review`;
  - тестирование метрик — `data/processed/eval.csv` (только чтение).
- **Код:** `agent/src/`, `agent/eval/eval_agent.py`, `agent/tests/`, `agent/examples/`, `client/`, `pyproject.toml`, `uv.lock`, `Dockerfile`, `docker-compose.yml`, `agent/.env.example`
- **Данные и артефакты:** `agent/eval/results/`
- **Документы:** —
- **Внешние сервисы:** OpenRouter (прототип), GigaChat (целевой), GitLab API (опционально)
