from pathlib import Path

from fastapi.testclient import TestClient

from src.api import app

EX = Path(__file__).parent.parent / "examples"
client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_review_returns_findings_and_markdown():
    r = client.post("/review", json={"diff": (EX / "mr_payments.diff").read_text(), "title": "PAY-2041", "llm": "none"})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "request_changes"
    assert {f["rule"] for f in body["findings"]} >= {"SEC001", "SEC002", "SEC003", "SEC004"}
    assert "[BLOCKER]" in body["markdown"]
    assert {"llm_skipped", "llm_errors", "input_tokens"} <= body.keys()


def test_unknown_llm_rejected():
    assert client.post("/review", json={"diff": "", "llm": "gpt-x"}).status_code == 422
