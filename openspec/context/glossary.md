# Термины

| Термин | Значение |
|---|---|
| MR | merge request в GitLab |
| diff / hunk | unified diff изменения; hunk — блок `@@ -a,b +c,d @@` |
| добавленная строка | строка diff с `+`; агент комментирует только их |
| правило | детерминированная проверка `SECnnn` / `BUGnnn` / `STYnnn` в `rules.py` |
| severity | blocker > major > minor > nit > question (+ none в данных) |
| вердикт | `request_changes` / `needs_attention` / `no_major_issues`; approve не бывает |
| черновик ревью | результат агента до подтверждения человеком |
| dry-run | запись подтверждённых замечаний в `.mr-review/outbox.json` вместо GitLab |
| маскирование | замена секретов и номеров карт перед отправкой в LLM |
| recall / ложная тревога | есть ли замечание там, где оно есть у человека / есть ли оно на чистом коде |
| eval-набор | `data/processed/eval.csv`: по 20 примеров на каждый severity |
| PAN | номер платёжной карты |
| ПДн | персональные данные |
