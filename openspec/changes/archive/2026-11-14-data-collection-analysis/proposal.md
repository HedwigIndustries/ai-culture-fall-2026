# Proposal

## Why

Чтобы оценивать агента и решить, на что он смотрит в первую очередь, нужны реальные замечания ревьюеров к Python-коду. Внутренние MR банка брать нельзя (NDA), поэтому берём открытый набор.

## What Changes

- Скрипт загрузки набора `ronantakizawa/github-codereview` с Hugging Face: только Python, результат в CSV.
- Ноутбук: описание набора, анализ замечаний, размеры diff и замечаний (основа для лимита входа), графики, выводы.
- Два документа: описание набора и выводы.

## Capabilities

### New Capabilities
- `review-data-collection`: загрузка набора, описание, анализ замечаний и размеров полей, выводы.

### Modified Capabilities

## Impact

- **Вход:** —
- **Код:** `data/fetch_raw.py`, `notebooks/data_analysis.ipynb`
- **Данные и артефакты:** `data/raw/github_codereview_python.csv`, `docs/data/fig/analysis_*.png`
- **Документы:** `docs/data/01_dataset_description.md`, `docs/data/02_findings.md`
- **Внешние сервисы:** Hugging Face (загрузка набора)
