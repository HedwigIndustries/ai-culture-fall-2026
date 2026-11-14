import io
import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mr_review.cli import run


@pytest.fixture
def service():
    """Подменяет сервис агента: запоминает запросы и отвечает заданным вердиктом."""
    state = {"requests": [], "verdict": "request_changes"}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append(body)
            report = {"verdict": state["verdict"], "findings": [], "markdown": f"# черновик\n{state['verdict']}"}
            data = json.dumps(report).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    state["url"] = f"http://127.0.0.1:{server.server_port}"
    yield state
    server.shutdown()


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "dev@example.com")
    git(repo, "config", "user.name", "dev")
    (repo / "app.py").write_text("x = 1\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    git(repo, "checkout", "-b", "feature")
    return repo


def test_directory_mode_sends_branch_diff_and_saves_report(repo, service):
    (repo / "app.py").write_text('x = 1\nDB_PASSWORD = "Sup3rS3cret"\n')
    code = run([str(repo), "--base", "main", "--url", service["url"]])
    assert code == 1
    sent = service["requests"][0]
    assert "+DB_PASSWORD" in sent["diff"] and sent["title"] == "feature"
    out = repo / ".mr-review"
    assert (out / "latest.md").read_text().startswith("# черновик")
    assert len(list(out.glob("*.json"))) == 1


def test_stdin_mode_outside_repo(tmp_path, service, monkeypatch, capsys):
    service["verdict"] = "no_major_issues"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("diff --git a/a.py b/a.py\n+x = 1\n"))
    assert run(["-", "--url", service["url"]]) == 0
    assert (tmp_path / ".mr-review" / "latest.md").exists()
    assert "no_major_issues" in capsys.readouterr().out


def test_empty_diff_does_not_call_service(repo, service, capsys):
    assert run([str(repo), "--base", "main", "--url", service["url"]]) == 0
    assert service["requests"] == []
    assert "изменений нет" in capsys.readouterr().out


def test_service_unavailable(repo, capsys):
    (repo / "app.py").write_text("x = 2\n")
    assert run([str(repo), "--base", "main", "--url", "http://127.0.0.1:9"]) == 2
    assert "недоступен" in capsys.readouterr().err


def test_not_a_repo(tmp_path, capsys):
    assert run([str(tmp_path), "--url", "http://127.0.0.1:9"]) == 2
    assert "не git-репозиторий" in capsys.readouterr().err
