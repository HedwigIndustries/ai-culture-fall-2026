# Git

## Ветки

- `main` — то, что сдаётся; всегда собирается и проходит тесты.
- Одно изменение OpenSpec — одна ветка с тем же именем: `data-preparation`, `agent-implementation`.
- Мелкие правки вне изменений: `fix/<что>`, `docs/<что>`.

## Коммиты

[Conventional Commits](https://www.conventionalcommits.org/ru/), сообщение по-русски:

```
<тип>(<область>): <что сделано>

feat(agent): правило SEC006 для токенов в URL
fix(data): переразметка шумной метки security
docs(data): выводы по размеру полей
spec(agent-implementation): сценарий для отказа LLM
chore: обновить uv.lock
```

Типы: `feat`, `fix`, `docs`, `spec`, `test`, `refactor`, `chore`. Области: `agent`, `data`, `notebooks`, `docs`, `openspec`, `docker`.

Цикл изменения: коммит спеки (`spec(...)`) → коммиты реализации с отметкой задач в `tasks.md` → `openspec archive <id>` отдельным коммитом.

## Что не коммитить

`agent/.env` и любые ключи, `.venv/`, кэши, `.claude/`, `.agents/`, `node_modules/`, `*.zip` — всё уже в `.gitignore`. Перед пушем: `git status` и проверка, что в diff нет ключей.

## Что коммитить из сгенерированного

`data/raw/*.csv`, `data/processed/*.csv`, ноутбук `.ipynb` с выводами, `agent/eval/results/`, `docs/data/` — результаты, по которым проверяется работа.
