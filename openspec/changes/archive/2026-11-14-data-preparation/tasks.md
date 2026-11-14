# Tasks

## 1. Проверки и очистка

- [x] 1.1 Создать `notebooks/data_preparation.ipynb`: чтение `data/raw/github_codereview_python.csv`, таблица проблем качества (включая пропуски по колонкам)
- [x] 1.2 В `notebooks/data_preparation.ipynb`: нормализовать текст, удалить дубли, пустые diff, diff больше 1 000 токенов и замечания длиннее 1 000 символов; заменить `@ник` и `/home/<ник>`; переразметить `security`; вывести журнал шагов
- [x] 1.3 В `notebooks/data_preparation.ipynb`: удалить ПДн и неиспользуемые поля, переименовать `reviewer_comment` → `comment_text`, добавить `review_id`

## 2. Преобразования и сохранение

- [x] 2.1 В `notebooks/data_preparation.ipynb`: добавить `severity`, `severity_id` (порядковое кодирование), `comment_type_id` (Label Encoding), `diff_tokens`; привести типы
- [x] 2.2 Сохранить `data/processed/reviews_clean.csv`, `data/processed/eval.csv` (20 × 6 = 120), `data/processed/before_after.csv`; других файлов в `data/processed/` нет

## 3. Документы

- [x] 3.1 `docs/data/03_cleaning.md` — очистка: найденные проблемы, какие изменения сделаны и почему
- [x] 3.2 `docs/data/04_before_after.md` — сравнение: какие изменения произошли и почему итоговый набор лучше подходит для задачи
- [x] 3.3 `openspec/context/data.md`, `openspec/context/security.md`: ники удаляются, а не хешируются; число строк и колонки — по выводам ноутбука

## 4. Проверка

- [x] 4.1 `uv run jupyter nbconvert --to notebook --execute --inplace notebooks/data_preparation.ipynb` без ошибок; цифры в документах совпадают с выводами ячеек
