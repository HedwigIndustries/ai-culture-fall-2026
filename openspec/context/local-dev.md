# Локальная разработка

## Один раз

```bash
uv sync                                     # Python 3.11 + все группы зависимостей в .venv
cp agent/.env.example agent/.env            # и вписать ключ OpenRouter или GigaChat
npm install -g @fission-ai/openspec@2.0.0   # OpenSpec CLI, глобально
openspec init --tools claude                # скиллы /openspec-* в .claude/skills (не в git)
```

## Частые команды

| Задача | Команда |
|---|---|
| скачать данные | `uv run python data/fetch_raw.py` |
| прогнать анализ данных | `uv run jupyter nbconvert --to notebook --execute --inplace notebooks/data_analysis.ipynb` |
| прогнать подготовку данных | `uv run jupyter nbconvert --to notebook --execute --inplace notebooks/data_preparation.ipynb` |
| тесты | `uv run pytest -q` |
| отладка агента без сервиса | `cd agent && uv run python -m src.cli --diff examples/mr_payments.diff [--llm openai]` (результат — в `.mr-review/`) |
| оценка качества | `uv run python agent/eval/eval_agent.py [--llm openai]` |
| API локально | `cd agent && uv run uvicorn src.api:app --port 8000` |
| API в Docker | `docker compose up --build agent-api` → http://localhost:8000/docs |
| установить CLI | `uv tool install ./client` (у пользователя — `uv tool install mr-review`) |
| ревью своей ветки | `mr-review <путь к репозиторию>` (адрес сервиса — `MR_REVIEWER_URL`); результат — в `<путь>/.mr-review/latest.md` |
| ревью своего diff | `git diff HEAD~1 \| mr-review -` |
| проверить спеки | `openspec validate --all --strict` |

## Сеть

Интернет на этой машине идёт через прокси VPN-клиента `127.0.0.1:2080` (экспортирован в `~/.zshrc`). Docker-контейнерам нужен свой: `BUILD_PROXY=http://http.docker.internal:3128 docker compose ...`.
