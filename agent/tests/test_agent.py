from pathlib import Path

import src.agent as agent_mod
from src.agent import review
from src.llm import LLMResult
from src.rules import mask_for_llm

EX = Path(__file__).parent.parent / "examples"


def test_dirty_mr_has_blockers():
    res = review((EX / "mr_payments.diff").read_text(), "PAY-2041")
    rules = {f.rule for f in res.findings}
    assert {"SEC001", "SEC002", "SEC003", "SEC004", "BUG001", "BUG002", "BUG003"} <= rules
    assert res.verdict == "request_changes"


def test_clean_mr_is_quiet():
    res = review((EX / "mr_clean.diff").read_text(), "PAY-2050")
    assert res.findings == [] and res.verdict == "no_major_issues"


def test_parametrized_sql_not_flagged():
    diff = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1,1 +1,2 @@\n a=1\n+cur.execute(\"SELECT 1 WHERE id = %s\", (i,))\n"
    assert review(diff).findings == []


def test_masking_before_llm():
    s = mask_for_llm('API_KEY = "sk_live_abcdef123"\nlog card 4276550012345678')
    assert "sk_live" not in s and "4276550012345678" not in s


class FakeLLM:
    """Одно корректное замечание и одно на несуществующей строке 999."""
    model = "fake"

    def chat(self, system, user):
        assert "af_live_9f8e7d6c5b4a3210" not in user          # секрет не уходит в модель
        return LLMResult('{"findings":[{"line":46,"severity":"blocker","category":"bug","message":"Два UPDATE без транзакции",'
                         '"suggestion":null,"confidence":0.8},{"line":999,"severity":"major","category":"bug","message":"x"}]}',
                         1000, 100, "fake", 0.1)


def test_llm_validation_drops_hallucinated_lines(monkeypatch):
    monkeypatch.setattr(agent_mod, "make_client", lambda p, m=None: FakeLLM())
    res = review((EX / "mr_payments.diff").read_text(), "PAY-2041", provider="fake")
    llm = [f for f in res.findings if f.source == "llm"]
    assert len(llm) == 1 and llm[0].line == 46
    assert any("999" in d for d in res.dropped)


class CountingLLM:
    model = "fake"

    def __init__(self):
        self.calls = 0

    def chat(self, system, user):
        self.calls += 1
        return LLMResult('{"findings": []}', 10, 2, "fake", 0.0)


def test_llm_skips_file_over_limit(monkeypatch):
    llm = CountingLLM()
    monkeypatch.setattr(agent_mod, "make_client", lambda p, m=None: llm)
    big = "".join(f"+line_{i} = compute_value(argument_{i})\n" for i in range(200))
    diff = f"diff --git a/big.py b/big.py\n--- a/big.py\n+++ b/big.py\n@@ -0,0 +1,200 @@\n{big}"
    res = review(diff + (EX / "mr_clean.diff").read_text(), provider="fake")
    assert llm.calls == 1                      # только маленький файл
    assert len(res.llm_skipped) == 1 and res.llm_skipped[0].startswith("big.py")


def test_prompt_has_new_file_line_numbers():
    from src.agent import _numbered_patch
    from src.diff import parse_unified_diff
    f = parse_unified_diff((EX / "mr_payments.diff").read_text())[0]
    lines = _numbered_patch(f).splitlines()
    assert any(l.startswith("  41 +") and "except" in l for l in lines)
