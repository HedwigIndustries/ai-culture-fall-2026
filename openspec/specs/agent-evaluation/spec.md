# agent-evaluation Specification

## Purpose
Как измеряется качество агента: прогон на eval-наборе, метрики recall, recall по blocker и доля ложных тревог отдельно для правил, LLM и вместе, сохранение результатов.

## Requirements

### Requirement: Метрики
`agent/eval/eval_agent.py` SHALL прогонять агента по `data/processed/eval.csv` и считать отдельно для правил и для LLM: recall (у агента есть замечание там, где оно есть у человека), recall по blocker и долю ложных тревог на коде без замечаний. Для LLM в результат пишутся средние входные и выходные токены и время; стоимость агент не считает.

#### Scenario: Ложная тревога
- **WHEN** у кейса `severity = none`, а агент оставил замечание
- **THEN** кейс засчитан как ложная тревога

#### Scenario: Только правила
- **WHEN** выполнен `uv run python agent/eval/eval_agent.py`
- **THEN** выведены recall, recall по blocker и доля ложных тревог правил

### Requirement: Результаты оценки
Результат прогона SHALL сохраняться в `agent/eval/results/eval_<провайдер>.json`: сводка метрик и ответ агента по каждому кейсу.

#### Scenario: Прогон с LLM
- **WHEN** выполнен `uv run python agent/eval/eval_agent.py --llm openai`
- **THEN** создан `agent/eval/results/eval_openai.json` с метриками правил и LLM, средними токенами и временем
