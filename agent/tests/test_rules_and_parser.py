import pytest
import requests

import src.agent as agent_mod
from src.cli import main
from src.agent import review
from src.diff import parse_unified_diff
from src.llm import LLMResult, parse_findings
from src.rules import mask_for_llm


def one_line_diff(code: str, path: str = "svc/x.py") -> str:
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -1,1 +1,2 @@\n a = 1\n+{code}\n"


def rule_ids(code: str, path: str = "svc/x.py") -> set[str]:
    return {f.rule for f in review(one_line_diff(code, path)).findings}


# --- парсер ---

def test_parser_line_numbers_multiple_files_and_deleted_file():
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
        "@@ -10,3 +10,3 @@ def f():\n x = 1\n-y = 2\n+y = 3\n z = 4\n"
        "@@ -40,2 +40,3 @@\n p = 1\n+q = 2\n r = 3\n"
        "diff --git a/old.py b/old.py\ndeleted file mode 100644\n--- a/old.py\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-a\n-b\n"
        "diff --git a/b.py b/b.py\nnew file mode 100644\n--- /dev/null\n+++ b/b.py\n@@ -0,0 +1,2 @@\n+one\n+two\n"
    )
    files = parse_unified_diff(diff)
    assert [f.path for f in files] == ["a.py", "b.py"]
    assert [(a.line_no, a.text) for a in files[0].added] == [(11, "y = 3"), (41, "q = 2")]
    assert [a.line_no for a in files[1].added] == [1, 2]


def test_parser_no_newline_marker_does_not_shift_lines():
    diff = ("diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1,2 +1,3 @@\n x = 1\n-y = 2\n"
            "\\ No newline at end of file\n+y = 3\n+z = 4\n\\ No newline at end of file\n")
    assert [a.line_no for a in parse_unified_diff(diff)[0].added] == [2, 3]


def test_parser_code_lines_that_look_like_headers():
    diff = "diff --git a/q.sql b/q.sql\n--- a/q.sql\n+++ b/q.sql\n@@ -1,1 +1,1 @@\n--- old comment\n+++ new comment\n"
    f = parse_unified_diff(diff)
    assert len(f) == 1 and [a.text for a in f[0].added] == ["++ new comment"]


# --- правила: срабатывают ---

@pytest.mark.parametrize("code, rule", [
    ('DB_PASSWORD = "Sup3rS3cret"', "SEC001"),
    ('cfg = {"api_key": "abcd1234ef"}', "SEC001"),
    ('cur.execute("SELECT * FROM t WHERE id = " + tid)', "SEC002"),
    ("cur.execute(\"SELECT * FROM t WHERE id = '%s'\" % tid)", "SEC002"),
    ('session.execute(text(f"DELETE FROM t WHERE id = {tid}"))', "SEC002"),
    ('self._logger.info("payment by %s", card_number)', "SEC003"),
    ('logging.warning(f"client inn={client_inn}")', "SEC003"),
    ('r = requests.get(url, verify=False, timeout=3)', "SEC004"),
    ("obj = pickle.loads(payload)", "SEC005"),
    ("cfg = yaml.load(fh)", "SEC005"),
    ("except:", "BUG001"),
    ("except Exception: pass", "BUG001"),
    ("r = requests.get(url)", "BUG002"),
    ("def f(x, items=[]): ...", "BUG003"),
    ("    print(resp)", "STY001"),
    ("# todo: retries", "STY002"),
    ("x = " + "1 + " * 40 + "1", "STY003"),
    ("\treturn x", "STY004"),
    ("x = 1   ", "STY005"),
    ("  return x", "STY006"),
    ("import os, sys", "STY007"),
    ("from os import *", "STY008"),
    ("if value == None:", "STY009"),
    ("if flag == True:", "STY010"),
    ("if not key in cache:", "STY011"),
    ("if type(x) == int:", "STY012"),
    ("square = lambda x: x * x", "STY013"),
    ("a = 1; b = 2", "STY014"),
    ("if not ok: return", "STY015"),
    ("l = []", "STY016"),
    ("class payment_service:", "STY017"),
    ("def GetBalance():", "STY018"),
    ("result = self.compute (x)", "STY019"),
    ("def compute (x):", "STY019"),
    ("connect(host, timeout = 3)", "STY020"),
    ("#comment", "STY021"),
    ("x = 1 # comment", "STY022"),
    ("assert user is not None", "STY023"),
    ('msg = f"done"', "STY024"),
    ('msg = "id=%s" % uid', "STY025"),
    ('msg = "id={}".format(uid)', "STY026"),
    ("cache = dict()", "STY027"),
    ('fh = open("a.txt")', "STY028"),
    ("    global counter", "STY029"),
    ("if len(items) == 0:", "STY030"),
])
def test_rule_fires(code, rule):
    assert rule in rule_ids(code)


def test_secret_in_yaml_config():
    assert "SEC001" in rule_ids('password: "Sup3rS3cret"', "deploy/values.yaml")


# --- правила: не срабатывают ---

@pytest.mark.parametrize("code", [
    'TOKEN_URL = "https://auth.internal/oauth/token"',
    'password = os.environ["DB_PASSWORD"]',
    'if token == "expired":',
    'cur.execute("SELECT * FROM t WHERE id = %s", (tid,))',
    'logger.info("company %s synced, beginning next", company_id)',
    'logger.info("Card blocked for client %s", client_id)',
    'logger.info("card %s", mask_pan(card_number))',
    "rows = session.exec(select(Transfer)).all()",
    "value = ast.literal_eval(raw)",
    "cfg = yaml.load(fh, Loader=SafeLoader)",
    "total_seconds: float = 1.5",
    "except Exception as exc:",
    "except Exception:",
    "r = requests.get(url, timeout=(3, 10))",
    "# TODO(PAY-1234): retries",
    "    return x",
    "        if value is None:",
    "if flag:",
    "if key not in cache:",
    "if isinstance(x, int):",
    "def square(x):",
    'url = "https://a.b/c;d"',
    "if not ok:",
    "items = []",
    "class PaymentService:",
    "def _get_balance(self):",
    "def __init__(self):",
    "result = compute(x)",
    "if (a and b) or (c):",
    "connect(host, timeout=3)",
    "x = a if a >= b else b",
    "#!/usr/bin/env python3",
    "x = 1  # comment",
    'msg = f"id={uid}"',
    'logger.info("id=%s", uid)',
    'msg = "100%"',
    "cache = dict(a=1)",
    'with open("a.txt") as fh:',
    "if not items:",
    'cfg = {"token": "AIRTABLE_AUTH_TOKEN"}',
    "agent_id (int): Identifier of the Agent to delete",
    'def estimate(text: str, model: str = "small") -> int:',
    "def f(x: int | None = None):",
    "#",
    'query = f"""',
    "config = config.dict()",
])
def test_rule_silent(code):
    assert rule_ids(code) == set()


def test_style_rules_skip_tests():
    for code in ["print(x)", "assert x == 1", "# TODO: later"]:
        assert rule_ids(code, "tests/test_x.py") == set()


def test_timeout_on_next_line_is_seen():
    diff = ("diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1,0 +1,2 @@\n"
            "+r = requests.post(url, json=body,\n+                  timeout=(3, 10))\n")
    assert review(diff).findings == []


# --- маскирование ---

def test_masking_spaced_pan_and_bearer():
    s = mask_for_llm('card = "4276 5500 1234 5678"\nheaders = {"Authorization": "Bearer eyJabc.def123"}')
    assert "5500" not in s and "eyJabc" not in s and "4276********5678" in s


# --- ответ LLM ---

def test_parse_findings_with_text_around_and_garbage():
    assert parse_findings('Вот ответ:\n```json\n{"findings":[{"line":1}]}\n```\nЕсли что — {спросите}') == [{"line": 1}]
    assert parse_findings("не JSON") == []
    assert parse_findings('{"findings": "нет"}') == []


DIFF = one_line_diff("x = compute()")


class ScriptedLLM:
    model = "fake"

    def __init__(self, content=None, exc=None):
        self.content, self.exc, self.prompts = content, exc, []

    def chat(self, system, user):
        self.prompts.append(user)
        if self.exc:
            raise self.exc
        return LLMResult(self.content, 10, 5, "fake", 0.0)


def test_validation_rejects_bad_items(monkeypatch):
    llm = ScriptedLLM('{"findings":['
                      '{"line":2,"severity":"major","category":"bug","message":"ok","confidence":"high"},'
                      '{"line":2,"severity":"critical","category":"bug","message":"x"},'
                      '{"line":true,"severity":"major","category":"bug","message":"x"},'
                      '{"line":2,"severity":"minor","category":"bug","message":"  "}]}')
    monkeypatch.setattr(agent_mod, "make_client", lambda p, m=None: llm)
    res = review(DIFF, "t", "карта 4276550012345678", provider="fake")
    assert [(f.line, f.severity, f.confidence) for f in res.findings] == [(2, "major", 0.5)]
    assert len(res.dropped) == 3
    assert "4276550012345678" not in llm.prompts[0]


def test_llm_failure_keeps_rule_findings(monkeypatch):
    llm = ScriptedLLM(exc=requests.ConnectionError("down"))
    monkeypatch.setattr(agent_mod, "make_client", lambda p, m=None: llm)
    res = review(one_line_diff('API_TOKEN = "abcdef123456"'), provider="fake")
    assert [f.rule for f in res.findings] == ["SEC001"] and res.llm_errors and res.llm_calls == 0


# --- CLI ---

def test_post_without_tty_publishes_nothing(tmp_path, monkeypatch, capsys):
    d = tmp_path / "mr.diff"
    d.write_text(one_line_diff("print(1)"))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr(requests, "post", lambda *a, **k: pytest.fail("в GitLab ничего не должно уйти"))
    main(["--diff", str(d), "--out", str(tmp_path), "--post"])
    assert "Пропущено" in capsys.readouterr().out
    assert not (tmp_path / "outbox.json").exists()


def test_post_dry_run_writes_only_approved(tmp_path, monkeypatch):
    d = tmp_path / "mr.diff"
    d.write_text(one_line_diff("print(1)\n+# TODO later").replace("+1,2", "+1,3"))
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    answers = iter(["y", ""])
    monkeypatch.setattr("builtins.input", lambda _="": next(answers))
    for var in ("GITLAB_URL", "GITLAB_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    main(["--diff", str(d), "--out", str(tmp_path), "--post"])
    import json
    assert len(json.loads((tmp_path / "outbox.json").read_text())) == 1
