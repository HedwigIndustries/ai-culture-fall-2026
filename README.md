# MR Reviewer

AI-ассистент первичного ревью merge request'ов для бэкенд-команды банка: правила (безопасность, ошибки, кодстайл) + LLM готовят черновик ревью, публикует только человек. Скоуп: Python-код. Итоговый проект курса «Культура ИИ: Квалифицированный заказчик».

Быстрый запуск (подробнее — [local-dev.md](openspec/context/local-dev.md)):

```bash
docker compose up --build agent-api        # сервис на http://localhost:8000
uv tool install ./client                   # команда mr-review
mr-review --diff agent/examples/mr_payments.diff
```

| О чём | Где |
|---|---|
| проблема и AI-решение | [docs/product/problem.md](docs/product/problem.md) |
| продукт и скоуп | [openspec/context/product.md](openspec/context/product.md) |
| архитектура агента | [openspec/context/architecture.md](openspec/context/architecture.md) |
| структура репозитория | [openspec/context/structure.md](openspec/context/structure.md) |
| данные | [openspec/context/data.md](openspec/context/data.md) |
| установка и запуск (uv, Docker) | [openspec/context/local-dev.md](openspec/context/local-dev.md) |
| тесты и оценка качества | [openspec/context/testing.md](openspec/context/testing.md) |
| конфиги и переменные окружения | [openspec/context/configs.md](openspec/context/configs.md) |
| данные: описание, выводы, очистка | [docs/data/](docs/data/) |
| качество агента | [docs/agent/quality.md](docs/agent/quality.md) |
| экономика и внедрение | [docs/economics/economics.md](docs/economics/economics.md) |
| декларация использования ИИ | [docs/ai_declaration.md](docs/ai_declaration.md) |
| решения и ограничения | [docs/decisions_and_limitations.md](docs/decisions_and_limitations.md) |
| все справки | [openspec/context/README.md](openspec/context/README.md) |
| спецификации (OpenSpec) | [openspec/specs/](openspec/specs/), история изменений — [openspec/changes/archive/](openspec/changes/archive/) |
