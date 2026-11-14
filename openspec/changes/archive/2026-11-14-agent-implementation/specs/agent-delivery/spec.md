## ADDED Requirements

### Requirement: Эндпоинты
HTTP API SHALL предоставлять `GET /health` и `POST /review`. Вход `/review` — JSON с полями `diff`, `title`, `description`, `llm`, `model`; выход — JSON отчёта: `verdict`, `findings`, `markdown`, токены LLM, пропуски LLM и ошибки модели. Сервис отчёт не хранит. Провайдер по умолчанию берётся из `MR_REVIEWER_LLM`. Публикации в API нет.

#### Scenario: Ревью через API
- **WHEN** `POST /review` с `mr_payments.diff` и `llm: none`
- **THEN** ответ 200, вердикт `request_changes`, в markdown есть `[BLOCKER]`

#### Scenario: Неизвестный провайдер
- **WHEN** `POST /review` с `llm: gpt-x`
- **THEN** ответ 422

### Requirement: Установка mr-review
CLI `mr-review` SHALL поставляться отдельным пакетом `client/` (entry point `mr-review`, только стандартная библиотека Python) и устанавливаться глобально, без исходников сервиса: `uv tool install mr-review` из индекса пакетов или `uv tool install git+https://github.com/HedwigIndustries/ai-culture-fall-2026#subdirectory=client`. Адрес сервиса задаётся `MR_REVIEWER_URL` или `--url`.

#### Scenario: Установка
- **WHEN** выполнен `uv tool install ./client`
- **THEN** команда `mr-review --help` доступна в любой директории

### Requirement: Режимы mr-review
`mr-review` SHALL принимать diff тремя способами: путь к директории (по умолчанию текущая) — `git diff` от merge-base с `origin/main`, включая незакоммиченные изменения, ветка меняется `--base`; `-` — diff из stdin; `--diff <файл>` — diff из файла.

#### Scenario: Директория
- **WHEN** выполнен `mr-review <путь к репозиторию>`, в ветке изменён `.py`-файл с секретом
- **THEN** в сервис ушёл diff ветки, в выводе есть `[BLOCKER]`

#### Scenario: Свой diff
- **WHEN** выполнен `cat agent/examples/mr_clean.diff | mr-review -`
- **THEN** в выводе черновик без блокеров

#### Scenario: Пустой diff
- **WHEN** в директории нет изменений относительно базы
- **THEN** запроса к сервису нет, выводится «изменений нет»

### Requirement: Вывод mr-review
`mr-review` SHALL отправлять diff в `POST /review` (JSON) по адресу из `MR_REVIEWER_URL` (по умолчанию `http://localhost:8000`), печатать черновик в stdout и сохранять его в `.mr-review/` в корне git-репозитория, чьи файлы проверялись: указанной директории или, для stdin и `--diff`, репозитория, из которого запущена команда (вне репозитория — текущая директория). Код возврата: 1 при вердикте `request_changes`, 2 при ошибке (не git-репозиторий, сервис недоступен), иначе 0.

#### Scenario: Результат на диске
- **WHEN** выполнен `mr-review <путь к репозиторию>`
- **THEN** в `<путь>/.mr-review/` появились `<дата-время>.md`, `<дата-время>.json` и перезаписан `latest.md`

#### Scenario: Блокер
- **WHEN** в черновике вердикт `request_changes`
- **THEN** код возврата 1

#### Scenario: Сервис недоступен
- **WHEN** по `MR_REVIEWER_URL` никто не отвечает
- **THEN** сообщение об ошибке в stderr, код возврата 2

### Requirement: Окружение uv
Зависимости SHALL описываться в `pyproject.toml` и фиксироваться в `uv.lock`: зависимости агента — основные, группы `analysis`, `notebook`, `dev` — для локальных шагов (данные, тесты).

#### Scenario: Локальная установка
- **WHEN** выполнен `uv sync`
- **THEN** `uv run pytest -q` проходит

### Requirement: Docker только для агента
`docker compose` SHALL поднимать только агента: `agent-api` (порт 8000) и `agent-check` (тесты, профиль `test`). Образ ставит через uv только зависимости агента. Ключи подключаются из `agent/.env` при запуске и MUST NOT попадать в образ.

#### Scenario: Запуск API
- **WHEN** выполнен `docker compose up --build agent-api`
- **THEN** `GET http://localhost:8000/health` возвращает `status: ok`

#### Scenario: Тесты в контейнере
- **WHEN** выполнен `docker compose run --rm --build agent-check`
- **THEN** все тесты агента проходят
