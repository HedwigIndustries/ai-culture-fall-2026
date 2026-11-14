"""Детерминированные проверки по добавленным строкам MR.

Секреты, ПДн и SQL-инъекции проверяются правилами, а не LLM: результат должен быть воспроизводимым.
Кодстайл (STY) — построчные проверки PEP 8 и типовые проверки линтеров: у сервиса есть только diff, а не файлы целиком.
Правила построчные: многострочные конструкции (SQL, собранный в переменную; сигнатура на нескольких строках)
они не видят — это остаётся LLM и человеку.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .diff import AddedLine, FileDiff
from .models import Finding

TEST_PATH = re.compile(r"(^|/)tests?/|(^|/)test_[^/]*\.py$|_test\.py$")

SECRET_NAME = r"\w*(?:password|passwd|secret|token|api_?key|private_key)\w*"
# Имена вида TOKEN_URL, PASSWORD_FIELD — не секреты, а их адреса и названия.
NOT_SECRET_NAME = r"(?!\w*_(?:url|uri|path|type|header|name|field|ttl)\b)"
# Отдельные слова в snake_case: card_number, client_inn. Не ловит company, beginning, discard.
PII = r"(?<![a-z])(?:card|pan|cvv|cvc|passport|snils|inn|phone|email|birth_?date|account_number|iban)(?![a-z])"
STRING_LITERAL = re.compile(r"""(?<![fFrRbB])(['"])(?:\\.|(?!\1).)*\1""")
ANY_STRING = re.compile(r"""(?<![\w])[rRbBfFuU]{0,2}(['"])(?:\\.|(?!\1).)*\1""")
STATEMENT_KW = r"(?:if|elif|else|for|while|try|except|finally|with|def|class|return|import|from|raise|pass|break|continue)"


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    category: str
    pattern: re.Pattern
    message: str
    suggestion: str | None = None
    py_only: bool = True          # SEC001 проверяем и в конфигах
    skip_tests: bool = False      # print и TODO в тестах не шумим
    ignore_strings: bool = False  # искать только в коде, не в тексте обычных строковых литералов
    strip: str = ""               # "strings" — убрать все строковые литералы; "code" — ещё и комментарий
    statement: bool = False       # склеить вызов, разнесённый на несколько строк


RULES: list[Rule] = [
    Rule("SEC001", "blocker", "security",
         re.compile(rf"""\b(?i:{NOT_SECRET_NAME}{SECRET_NAME})['"]?\s*[:=]\s*['"](?![A-Z0-9_]+['"])[^'"\s]{{6,}}['"]"""),
         "Похоже на секрет в коде. Из истории git его уже не убрать — только отозвать.",
         "Брать из Vault / переменной окружения (`os.environ[\"...\"]`), текущий секрет отозвать.",
         py_only=False),
    Rule("SEC002", "blocker", "security",
         re.compile(r"""(?i)(\.(execute|executemany|raw)|\btext)\(\s*((?:f|rf|fr)['"]|['"][^'"]*['"]\s*(%|\+|\.format\())"""),
         "SQL собирается из строки с подстановкой значений — SQL-инъекция.",
         "Параметры отдельно: `cur.execute(\"... WHERE id = %s\", (value,))`, в SQLAlchemy — bindparams."),
    Rule("SEC003", "blocker", "security",
         re.compile(rf"""(?i)^(?!.*mask)(?:.*\W)?\w*log(?:ger|ging)?\.(debug|info|warning|error|exception|critical)\(.*{PII}"""),
         "В лог попадают ПДн / данные карты. Логи читает гораздо больше людей, чем БД (ПДн, PCI DSS).",
         "Логировать маску (`mask_pan(card_number)` → `**** 1234`) или технический id.",
         ignore_strings=True),
    Rule("SEC004", "blocker", "security",
         re.compile(r"verify\s*=\s*False"),
         "Отключена проверка TLS-сертификата — открыта дорога для MITM.",
         "Передать корпоративный CA bundle: `verify=\"/etc/ssl/certs/corp-ca.pem\"`."),
    Rule("SEC005", "blocker", "security",
         re.compile(r"(?<![.\w])(eval|exec)\(|pickle\.loads?\(|yaml\.load\((?!.*Loader=\s*(yaml\.)?C?SafeLoader)"),
         "eval / pickle / yaml.load на входных данных — выполнение произвольного кода.",
         "`json.loads`, `yaml.safe_load` или явный разбор."),
    Rule("BUG001", "major", "bug",
         re.compile(r"^\s*except\s*:|^\s*except\s+(Base)?Exception\s*:\s*pass\b"),
         "except ловит всё подряд и молча продолжает — ошибка потеряется.",
         "Ловить конкретные исключения и логировать: `except (Timeout, ConnectionError): logger.warning(...)`."),
    Rule("BUG002", "major", "bug",
         re.compile(r"\brequests\.(get|post|put|patch|delete|head|request)\((?!.*\btimeout\s*=)"),
         "HTTP-вызов без timeout: если смежная система зависнет, поток повиснет вместе с ней.",
         "Явный `timeout=(connect, read)`, например `timeout=(3, 10)`.",
         statement=True),
    Rule("BUG003", "major", "bug",
         re.compile(r"\bdef \w+\(.*=\s*(\[\]|\{\}|set\(\)|list\(\)|dict\(\))"),
         "Изменяемое значение по умолчанию — один объект на все вызовы.",
         "`tags: list[str] | None = None`, внутри `tags = tags or []`."),
    Rule("STY001", "nit", "style",
         re.compile(r"^\s*(print\(|breakpoint\(|import pdb\b|pdb\.set_trace\()"),
         "Отладочный print / breakpoint в коде сервиса.",
         "Удалить или заменить на `logger.debug(...)`.",
         skip_tests=True),
    Rule("STY002", "nit", "style",
         re.compile(r"(?i)#\s*(TODO|FIXME|HACK)\b(?!.*\b[A-Z]+-\d+)"),
         "TODO без номера задачи потеряется.",
         "Добавить задачу: `# TODO(PAY-1234): ...`.",
         skip_tests=True),
    Rule("STY003", "nit", "style", re.compile(r"^.{121,}$"),
         "Строка длиннее 120 символов.", "Перенести аргументы или вынести часть выражения в переменную."),
    Rule("STY004", "nit", "style", re.compile(r"^ *\t"),
         "Табуляция в отступе.", "Отступ — 4 пробела."),
    Rule("STY005", "nit", "style", re.compile(r"[ \t]+$"),
         "Пробелы в конце строки.", "Убрать хвостовые пробелы (настроить редактор)."),
    Rule("STY006", "nit", "style", re.compile(rf"^(?: {{4}})* {{1,3}}{STATEMENT_KW}\b"),
         "Отступ не кратен 4 пробелам.", "Выровнять отступ по 4 пробела."),
    Rule("STY007", "nit", "style", re.compile(r"^\s*import\s+[\w.]+\s*,"),
         "Несколько импортов в одной строке.", "Каждый модуль — отдельным `import`."),
    Rule("STY008", "nit", "style", re.compile(r"^\s*from\s+[\w.]+\s+import\s+\*"),
         "`import *` скрывает, откуда берутся имена.", "Импортировать нужные имена явно."),
    Rule("STY009", "nit", "style", re.compile(r"[=!]=\s*None\b|\bNone\s*[=!]="),
         "Сравнение с None через `==` / `!=`.", "`is None` / `is not None`.", strip="code"),
    Rule("STY010", "nit", "style", re.compile(r"[=!]=\s*(True|False)\b|\b(True|False)\s*[=!]="),
         "Сравнение с True / False через `==`.", "`if flag:` / `if not flag:`.", strip="code"),
    Rule("STY011", "nit", "style", re.compile(r"\bnot\s+[\w.]+(?:\[[^\]]*\])?\s+in\b"),
         "`not x in y` читается двусмысленно.", "`x not in y`.", strip="code"),
    Rule("STY012", "nit", "style", re.compile(r"\btype\([^()]*\)\s*[=!]="),
         "Сравнение типов через `type(x) ==`.", "`isinstance(x, T)`.", strip="code"),
    Rule("STY013", "nit", "style", re.compile(r"^\s*[\w.]+\s*=\s*lambda\b"),
         "lambda, присвоенная переменной.", "Обычная функция через `def`.", strip="code"),
    Rule("STY014", "nit", "style", re.compile(r";"),
         "Несколько инструкций в одной строке через `;`.", "По одной инструкции на строку.", strip="code"),
    Rule("STY015", "nit", "style",
         re.compile(r"^\s*(?:(?:if|elif|for|while|with)\b.*:\s*(?:pass|return|break|continue|raise)\b|(?:else|try|finally)\s*:\s*\S)"),
         "Тело блока на той же строке, что и условие.", "Перенести тело на следующую строку.", strip="code"),
    Rule("STY016", "nit", "style", re.compile(r"(?:^\s*|\bfor\s+)(?:l|O|I)\s*(?:=(?!=)|\bin\b)"),
         "Имя `l`, `O` или `I` легко спутать с 1 и 0.", "Говорящее имя.", strip="code"),
    Rule("STY017", "nit", "style", re.compile(r"^\s*class\s+(?!_*[A-Z][A-Za-z0-9]*\b)\w+"),
         "Имя класса не в CapWords.", "`class PaymentService:`."),
    Rule("STY018", "nit", "style", re.compile(r"^\s*(?:async\s+)?def\s+(?!_*[a-z][a-z0-9_]*\b)\w+"),
         "Имя функции не в snake_case.", "`def get_balance():`."),
    Rule("STY019", "nit", "style",
         re.compile(r"\bdef\s+\w+\s+\(|\.\w+\s+\("),
         "Пробел перед скобкой вызова.", "`foo(x)` без пробела.", strip="code"),
    Rule("STY020", "nit", "style", re.compile(r"\([^()]*?(?<!:\s)(?<!\|\s)(?<!:)\b\w+(?:\s+=\s*|\s*=\s+)(?!=)[^=\s]"),
         "Пробелы вокруг `=` в именованном аргументе.", "`f(timeout=3)` без пробелов.", strip="code"),
    Rule("STY021", "nit", "style", re.compile(r"(?:^|\s)#(?=[^\s!#:])"),
         "Нет пробела после `#` в комментарии.", "`# комментарий`.", strip="strings"),
    Rule("STY022", "nit", "style", re.compile(r"[^\s#] ?#"),
         "Inline-комментарий ближе чем через два пробела от кода.", "`x = 1  # комментарий`.", strip="strings"),
    Rule("STY023", "nit", "style", re.compile(r"^\s*assert\b"),
         "`assert` в коде сервиса отключается флагом `-O`.", "Явная проверка с `raise`.", skip_tests=True),
    Rule("STY024", "nit", "style", re.compile(r"""(?<!\w)[fF][rR]?(['"])(?!\1)(?:\\.|(?!\1)[^{\\])*\1"""),
         "f-строка без подстановок.", "Обычная строка без `f`."),
    Rule("STY025", "nit", "style", re.compile(r"""(['"])(?:\\.|(?!\1).)*%[-\d.]*[sdrfixo](?:\\.|(?!\1).)*\1\s*%\s*[\w(\[]"""),
         "Форматирование строки через `%`.", "f-строка."),
    Rule("STY026", "nit", "style", re.compile(r"""['"]\.format\("""),
         "Форматирование через `.format()`.", "f-строка."),
    Rule("STY027", "nit", "style", re.compile(r"(?<![\w.])(?:dict|list)\(\s*\)"),
         "Пустой `dict()` / `list()` вместо литерала.", "`{}` / `[]`.", strip="code"),
    Rule("STY028", "nit", "style", re.compile(r"^\s*[\w.]+\s*=\s*open\("),
         "`open()` без `with` — файл может не закрыться.", "`with open(...) as fh:`.", strip="code"),
    Rule("STY029", "nit", "style", re.compile(r"^\s+global\s+\w"),
         "`global` внутри функции.", "Передавать значение аргументом или хранить в объекте.", strip="code"),
    Rule("STY030", "nit", "style", re.compile(r"\blen\([^()]*\)\s*[=!]=\s*0\b"),
         "Проверка пустоты через `len(x) == 0`.", "`if not x:`.", strip="code"),
]


def _statement(lines: list[AddedLine], i: int, max_lines: int = 10) -> str:
    """Склеивает вызов, если скобки не закрылись на той же строке (только добавленные строки подряд)."""
    text, depth = "", 0
    for j in range(i, min(i + max_lines, len(lines))):
        if j > i and lines[j].line_no != lines[j - 1].line_no + 1:
            break
        text += lines[j].text + " "
        depth += lines[j].text.count("(") - lines[j].text.count(")")
        if depth <= 0:
            break
    return text


def run_rules(files: list[FileDiff]) -> list[Finding]:
    findings: list[Finding] = []
    for f in files:
        is_py, is_test = f.path.endswith(".py"), bool(TEST_PATH.search(f.path))
        for i, line in enumerate(f.added):
            for r in RULES:
                if (r.py_only and not is_py) or (r.skip_tests and is_test):
                    continue
                text = _statement(f.added, i) if r.statement else line.text
                if r.ignore_strings:
                    text = STRING_LITERAL.sub('""', text)
                if r.strip:
                    text = ANY_STRING.sub('""', text)
                    if r.strip == "code":
                        text = text.split("#", 1)[0]
                if r.pattern.search(text):
                    findings.append(Finding(f.path, line.line_no, r.severity, r.category, r.id,
                                            r.message, r.suggestion))
    return findings


SECRET_VALUE = re.compile(rf"""(?i)(\b{SECRET_NAME}['"]?\s*[:=]\s*['"])([^'"]+)(['"])""")
BEARER = re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._~+/=-]{8,})")
PAN = re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)")


def _mask_pan(m: re.Match) -> str:
    digits = re.sub(r"\D", "", m.group(0))
    return digits[:4] + "*" * (len(digits) - 8) + digits[-4:]


def mask_for_llm(text: str) -> str:
    """Секреты и номера карт модели для ревью не нужны — убираем до отправки."""
    text = SECRET_VALUE.sub(lambda m: m.group(1) + "***MASKED***" + m.group(3), text)
    text = BEARER.sub(lambda m: m.group(1) + "***MASKED***", text)
    return PAN.sub(_mask_pan, text)
