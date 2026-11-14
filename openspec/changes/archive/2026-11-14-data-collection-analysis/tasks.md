# Tasks

## 1. Загрузка

- [x] 1.1 В `data/fetch_raw.py`: скачать набор, оставить только Python, сохранить в `data/raw/github_codereview_python.csv`; если файл есть — не скачивать
- [x] 1.2 В `data/raw/` только `github_codereview_python.csv`

## 2. Ноутбук

- [x] 2.1 Создать `notebooks/data_analysis.ipynb`: чтение `data/raw/github_codereview_python.csv`, описание набора (поля, типы, пропуски, репозитории)
- [x] 2.2 В `notebooks/data_analysis.ipynb`: анализ замечаний (типы, темы), размер полей (перцентили, доля сверх порогов), графики в `docs/data/fig/analysis_*.png`, выводы с рекомендуемым лимитом входа

## 3. Документы

- [x] 3.1 `docs/data/01_dataset_description.md` — описание набора: источник, ссылка и способ получения; количество записей, признаки, типы данных и ограничения
- [x] 3.2 `docs/data/02_findings.md` — выводы: какие закономерности обнаружены и насколько данных достаточно для решения задачи

## 4. Проверка

- [x] 4.1 `uv run jupyter nbconvert --to notebook --execute --inplace notebooks/data_analysis.ipynb` без ошибок; повторный `uv run python data/fetch_raw.py` не меняет CSV; цифры в документах совпадают с выводами ячеек
