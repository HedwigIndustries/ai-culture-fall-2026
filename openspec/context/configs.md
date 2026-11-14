# Конфиги

## Переменные окружения (`agent/.env`)

| Переменная | Для чего | По умолчанию |
|---|---|---|
| `OPENAI_BASE_URL` | OpenAI-совместимый endpoint | `https://api.openai.com/v1` (в `.env.example` — OpenRouter) |
| `OPENAI_API_KEY` | ключ для `--llm openai` | — |
| `OPENAI_MODEL` | модель | `gpt-4o-mini` (в `.env.example` — `qwen/qwen3.5-plus-20260420`) |
| `OPENAI_REASONING` | `off` — отключить рассуждения модели | не задано |
| `GIGACHAT_CREDENTIALS` | Authorization key GigaChat | — |
| `GIGACHAT_CA_BUNDLE` | путь к сертификату НУЦ Минцифры | системные CA |
| `GIGACHAT_MODEL`, `GIGACHAT_SCOPE` | модель и scope GigaChat | `GigaChat-2-Pro`, `GIGACHAT_API_PERS` |
| `GITLAB_URL`, `GITLAB_TOKEN` | публикация в GitLab; без них — dry-run | — |
| `MR_REVIEWER_LLM` | провайдер по умолчанию для API | `none` |
| `MR_REVIEWER_URL` | адрес сервиса для `mr-review` (на машине разработчика) | `http://localhost:8000` |
| `MAX_DIFF_CHARS` | лимит размера diff в API | `200000` |
| `BUILD_PROXY` | прокси для Docker (сборка и запуск) | не задано |

## Файлы

| Файл | Что настраивает |
|---|---|
| `pyproject.toml` | зависимости агента (основные) и группы `dev`, `analysis`, `notebook` |
| `uv.lock` | точные версии; менять только через `uv add` / `uv lock` |
| `Dockerfile` | `runtime` (только агент) и `test` (+ pytest, тесты, примеры) |
| `docker-compose.yml` | `agent-api` (:8000), `agent-check` (профиль `test`) |
| `.dockerignore` | белый список: в образ попадают только `pyproject.toml`, `uv.lock`, `agent/src`, `agent/tests`, `agent/examples` |
| `.gitignore` | `.venv`, `.env`, кэши, `.claude/`, `.agents/`, сборочные артефакты |
| `openspec/config.yaml` | контекст и правила для OpenSpec-артефактов |
