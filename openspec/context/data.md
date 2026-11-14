# Данные

Все наборы — CSV. Пустые строки читаем как `''`: `pd.read_csv(..., keep_default_na=False, na_values=[])`.

## Источник

| Файл | Источник | Строк |
|---|---|---|
| `data/raw/github_codereview_python.csv` | [ronantakizawa/github-codereview](https://huggingface.co/datasets/ronantakizawa/github-codereview), только Python | 5 248 |

Реальные inline-комментарии людей к PR из популярных open-source репозиториев (permissive-лицензии, боты исключены). Строка: `before_code`, `after_code`, `diff_context` (hunk), `reviewer_comment`, `comment_type` (9 классов), `quality_score`, `is_negative` (код прошёл ревью без замечаний), метаданные репозитория и PR.

## Подготовленные наборы (`data/processed/`)

| Файл | Строк | Ключевые колонки |
|---|---|---|
| `reviews_clean.csv` | 4 981 | `review_id`, `repo_name`, `file_path`, `diff_context`, `diff_tokens`, `comment_text`, `comment_type`, `comment_type_id`, `severity`, `severity_id`, `label_fixed`, `label_unverified` |
| `eval.csv` | 120 | `review_id`, `file_path`, `diff_context`, `comment_text`, `comment_type`, `severity` (по 20 на каждый severity) |
| `before_after.csv` | — | сравнение исходного и подготовленного набора |

## Соглашения

- `severity`: bug, security → blocker; performance → major; refactor, suggestion → minor; style, nitpick → nit; question → question; без замечания → none. Та же шкала у агента.
- Лимит входа: `diff_tokens` ≤ 1 000, текст замечания ≤ 1 000 символов. Тот же лимит у агента для вызова LLM.
- `diff_tokens = len(diff_context) / 3.5` — грубая оценка; реальные токены — из `usage` модели.
- ПДн (ники авторов и ревьюеров) и неиспользуемые колонки удаляются; в тексте замечаний `@ник` → `@user`, `/home/<ник>` → `/home/user`.
- `severity_id`: none 0, question 1, nit 2, minor 3, major 4, blocker 5. `comment_type_id` — Label Encoding по алфавиту.
- У кода без замечаний `comment_text` пустой.
