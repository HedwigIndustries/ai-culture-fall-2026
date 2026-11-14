# Структура репозитория

```
mr-reviewer/
├── agent/                      # сервис агента
│   ├── src/                    # код агента: diff, rules, llm, agent, models, api, cli
│   ├── tests/                  # pytest: test_agent, test_rules_and_parser, test_api
│   ├── examples/               # демо-MR: mr_payments.diff (с дефектами), mr_clean.diff
│   ├── eval/                   # eval_agent.py — метрики на eval-наборе; results/ — результаты прогонов (коммитятся)
│   ├── .env.example            # шаблон ключей (сам .env — не в git)
├── client/                     # CLI `mr-review` для разработчика: diff → сервис агента → черновик (stdlib)
├── data/
│   ├── fetch_raw.py            # загрузка наборов с Hugging Face → CSV
│   ├── raw/                    # исходный CSV (только Python)
│   └── processed/              # очищенный набор, eval-набор, сравнение до/после
├── notebooks/
│   ├── data_analysis.ipynb     # описание и анализ набора
│   └── data_preparation.ipynb  # очистка, eval-набор → data/processed/
├── docs/data/                  # 01 описание набора, 02 выводы, 03 очистка, 04 до/после; fig/ — графики анализа
├── docs/product/problem.md     # проблема, пользователи, AI-решение
├── docs/agent/quality.md       # качество агента: метрики, известные проблемы, что дальше
├── docs/economics/economics.md # ориентировочная экономика и план внедрения
├── docs/ai_declaration.md      # декларация использования ИИ
├── docs/decisions_and_limitations.md # решения, как работает, границы
├── openspec/                   # SDD: config.yaml, context/, changes/, specs/
├── CLAUDE.md                   # правила для агента, работа с кодом, карта
├── pyproject.toml, uv.lock     # зависимости (uv)
├── Dockerfile, docker-compose.yml, .dockerignore
└── README.md
```

**Правила:**
- все данные — только CSV;
- сгенерированное (`agent/eval/results/`, `data/processed/`, `docs/data/fig/`) пересобирается командами из [local-dev.md](local-dev.md).
