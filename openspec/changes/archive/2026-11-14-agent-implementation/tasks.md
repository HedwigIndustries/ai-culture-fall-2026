# Tasks

## 1. Ревью

- [x] 1.1 В `agent/src/diff.py`: разбор unified diff, номера строк в новой версии файла
- [x] 1.2 В `agent/src/rules.py`: 38 правил (SEC001–SEC005, BUG001–BUG003, STY001–STY030); тест на срабатывание и на ложное срабатывание для каждого в `agent/tests/`
- [x] 1.3 В `agent/src/agent.py`: вердикт, лимит nit, черновик markdown/JSON

## 2. LLM

- [x] 2.1 В `agent/src/llm.py`: провайдеры `openai`, `gigachat`, `none`; `OPENAI_REASONING=off`
- [x] 2.2 В `agent/src/agent.py`: лимит входа 1 000 токенов на файл с отметкой о пропуске; маскирование перед вызовом; валидация ответа; ошибки модели в `llm_errors`

## 3. Публикация, API, CLI

- [x] 3.1 В `agent/src/cli.py`: `--post` с подтверждением каждого замечания и пачки; dry-run и черновик — в `.mr-review/`
- [x] 3.2 В `agent/src/api.py`: `GET /health`, `POST /review` (вход и выход — JSON, отчёт не хранится)
- [x] 3.3 Создать пакет `client/` (CLI `mr-review`, stdlib): директория, stdin, файл; вывод в stdout и `.mr-review/`; коды возврата; тесты

## 4. Оценка

- [x] 4.1 Создать `agent/eval/eval_agent.py`: recall, recall по blocker, ложные тревоги на `data/processed/eval.csv` отдельно для правил и LLM; для LLM — средние токены и время
- [x] 4.2 Сохранить результаты прогонов без LLM и с `openai` в `agent/eval/results/`

## 5. Окружение

- [x] 5.1 `pyproject.toml`, `uv.lock`, `agent/.env.example`
- [x] 5.2 `Dockerfile` и `docker-compose.yml`: `agent-api`, `agent-check`

## 6. Проверка

- [x] 6.1 `uv run pytest -q` и `docker compose run --rm --build agent-check` проходят; `mr-review --diff agent/examples/mr_payments.diff` против запущенного `agent-api` выдаёт `[BLOCKER]` и код возврата 1
