## ADDED Requirements

### Requirement: Проверки качества
Ноутбук `notebooks/data_preparation.ipynb` SHALL читать `data/raw/github_codereview_python.csv` и перед очисткой выводить таблицу «проблема → строк, доля»: пропуски по каждой колонке, дубли (repo, PR, файл, замечание) после нормализации текста, пустые `diff_context`, diff длиннее 1 000 токенов, замечания длиннее 1 000 символов, CRLF, @упоминания и `/home/<ник>` в тексте замечаний, шумная метка `security`.

#### Scenario: Таблица проблем
- **WHEN** ноутбук выполнен
- **THEN** перед очисткой выведена таблица проблем с числом строк и долей

### Requirement: Ограничение размера входа
Подготовленный набор SHALL содержать только строки, где `diff_context` не длиннее 1 000 токенов (оценка: символы / 3,5) и текст замечания не длиннее 1 000 символов.

#### Scenario: Большой diff
- **WHEN** оценка токенов `diff_context` больше 1 000
- **THEN** строки нет в `data/processed/reviews_clean.csv`

#### Scenario: Длинное замечание
- **WHEN** текст замечания длиннее 1 000 символов
- **THEN** строки нет в `data/processed/reviews_clean.csv`

### Requirement: Очистка
Ноутбук SHALL нормализовать текст (CRLF → LF, без пробелов в конце строк, strip), удалять дубли и строки с пустым `diff_context`, заменять в тексте замечаний `@ник` на `@user` и `/home/<ник>` на `/home/user`. Замечание `security` с текстом без security-лексики SHALL переразмечаться в `suggestion` с флагом `label_fixed`; без текста — сохранять метку с флагом `label_unverified`. Каждый шаг SHALL попадать в журнал «шаг → строк».

#### Scenario: Шумная метка
- **WHEN** у замечания с меткой `security` в тексте нет security-лексики
- **THEN** метка заменена на `suggestion`, строка помечена `label_fixed`

#### Scenario: Упоминание
- **WHEN** в тексте замечания есть `@ник`
- **THEN** в `comment_text` вместо него `@user`

#### Scenario: Журнал
- **WHEN** ноутбук выполнен
- **THEN** выведен журнал «шаг → строк», последняя строка равна числу строк в `reviews_clean.csv`

### Requirement: Удаление лишних полей
В `data/processed/reviews_clean.csv` SHALL остаться только поля: `review_id` (int, номер строки в исходном файле), `repo_name`, `file_path`, `diff_context`, `diff_tokens` (int), `comment_text` (бывший `reviewer_comment`; у кода без замечаний пустой), `comment_type`, `comment_type_id` (int), `severity`, `severity_id` (int), `label_fixed` и `label_unverified` (bool). Остальные колонки, включая ники авторов и ревьюеров, MUST быть удалены.

#### Scenario: Нет ПДн
- **WHEN** очистка выполнена
- **THEN** в `data/processed/reviews_clean.csv` нет колонок с никами авторов и ревьюеров

### Requirement: Преобразование категорий
После переразметки ноутбук SHALL переводить `comment_type` в `severity` (bug, security → blocker; performance → major; refactor, suggestion → minor; style, nitpick → nit; question → question; none → none) и кодировать: `severity_id` — порядковое кодирование none = 0, question = 1, nit = 2, minor = 3, major = 4, blocker = 5; `comment_type_id` — Label Encoding по алфавиту классов.

#### Scenario: Шкала severity
- **WHEN** `comment_type = bug`
- **THEN** `severity = blocker`, `severity_id = 5`

### Requirement: Eval-набор
Ноутбук SHALL сохранять `data/processed/eval.csv` с колонками `review_id`, `file_path`, `diff_context`, `comment_text`, `comment_type`, `severity`: по 20 случайных строк (seed 42) из `reviews_clean.csv` на каждый severity, включая `none`, с `diff_tokens` не меньше 40.

#### Scenario: Баланс
- **WHEN** ноутбук выполнен
- **THEN** в `eval.csv` 120 строк, по 20 на каждый из 6 severity

### Requirement: Сравнение «до/после»
Ноутбук SHALL сохранять `data/processed/before_after.csv` с одинаковыми определениями метрик для исходного и подготовленного набора: строки, столбцы, пропуски (в том числе пустой diff), дубли, diff больше лимита, замечания больше лимита, CRLF, @упоминания и `/home/<ник>`, колонки с ПДн, метка `security` и `security` без security-лексики.

#### Scenario: Таблица сравнения
- **WHEN** ноутбук выполнен
- **THEN** в подготовленном наборе пропусков, дублей, diff и замечаний больше лимита, CRLF, @упоминаний, `/home/<ник>`, колонок с ПДн и `security` без security-лексики 0
