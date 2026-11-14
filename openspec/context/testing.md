# Тесты и оценка

## Тесты

```bash
uv run pytest -q                              # тесты агента и клиента (agent/tests, client/tests)
docker compose run --rm --build agent-check   # те же тесты в контейнере
```

| Файл | Что проверяет |
|---|---|
| `test_rules_and_parser.py` | парсер diff, срабатывания и ложные срабатывания правил, маскирование, валидация ответа LLM, `--post` |
| `test_agent.py` | демо-MR, чистый MR, маскирование перед LLM, отброс галлюцинаций, лимит входа LLM, номера строк в промпте (модель-заглушка) |
| `test_api.py` | `/health`, `/review`, 422 на неизвестный провайдер |
| `client/tests/test_cli.py` | `mr-review`: режим директории, stdin, пустой diff, сервис недоступен, не git-репозиторий (сервис подменяется локальным HTTP-сервером) |

Тесты не ходят в сеть: LLM подменяется заглушкой через `monkeypatch`.

## Оценка (eval)

```bash
uv run python agent/eval/eval_agent.py              # только правила
uv run python agent/eval/eval_agent.py --llm openai # правила + LLM (нужен agent/.env)
```

Набор — `data/processed/eval.csv` (120 кейсов, по 20 на каждый severity).

| Метрика | Что значит |
|---|---|
| recall | доля кейсов с замечанием человека, где агент тоже оставил замечание |
| recall по blocker | то же только для bug/security |
| ложные тревоги | доля кейсов `none` (код без замечаний), где агент что-то написал |

Считается отдельно для правил и для LLM. Результаты — `agent/eval/results/eval_<провайдер>.json`. Между прогонами LLM разброс 10–15 п. п. Известные проблемы качества и план — `docs/agent/quality.md`.

## Перед archive изменения

1. `uv run pytest -q` — зелёный.
2. `openspec validate --all --strict` — без ошибок.
3. Если менялись данные — прогнать изменённый ноутбук (`notebooks/data_analysis.ipynb` или `data_preparation.ipynb`, команды в [local-dev.md](local-dev.md)), цифры в `docs/data/` сверены с выводами ноутбука.
4. Если менялся агент — прогнать eval с `--llm openai`, `agent/eval/results/` обновлён.
