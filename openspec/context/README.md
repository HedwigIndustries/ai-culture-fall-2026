# Контекст проекта MR Reviewer

Короткие справки для реализации изменений из `openspec/changes/`. Читать перед `/openspec-apply-change`.

| Файл | Когда открывать |
|---|---|
| [product.md](product.md) | зачем проект, для кого, что входит в MVP |
| [architecture.md](architecture.md) | компоненты агента и поток данных |
| [structure.md](structure.md) | где что лежит в репозитории |
| [data.md](data.md) | набор данных, колонки CSV, eval-набор |
| [llm.md](llm.md) | провайдеры, промпт, маскирование, токены |
| [dev-standards.md](dev-standards.md) | как писать код, тесты и тексты |
| [testing.md](testing.md) | тесты, eval, что прогнать перед archive |
| [security.md](security.md) | секреты, ПДн, NDA, человек в контуре |
| [local-dev.md](local-dev.md) | uv, ноутбуки, агент, Docker, прокси |
| [configs.md](configs.md) | переменные окружения и конфиг-файлы |
| [git.md](git.md) | ветки, коммиты, что не коммитить |
| [glossary.md](glossary.md) | термины |

Изменения ведутся так: `openspec/changes/<id>/` (proposal → design → specs → tasks) → apply → archive в `openspec/specs/`.
Если реализация меняет архитектуру, структуру или конфиги — обновить соответствующий файл здесь в том же изменении.
