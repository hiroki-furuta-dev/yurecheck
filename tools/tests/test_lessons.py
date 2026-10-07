import json
import os
import sys

from conftest import REPO, run_tool

sys.path.insert(0, os.path.join(REPO, "tools"))
import lessons  # noqa: E402


def _write(tmp_repo, name, failure, keywords, body):
    d = tmp_repo / "docs" / "lessons"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(f"---\nfailure: {failure}\nkeywords: [{', '.join(keywords)}]\n---\n# t\n{body}\n", encoding="utf-8")


def test_match_only_when_keywords_hit(tmp_repo):
    _write(tmp_repo, "a.md", "test", ["NullReference", "ScenarioFile"], "A の教訓")
    _write(tmp_repo, "b.md", "hook", ["exit 2"], "B の教訓")
    les = lessons.load(str(tmp_repo))
    assert [x["path"] for x in lessons.match(les, "NullReferenceException in ScenarioFile")] == ["a.md"]
    assert lessons.match(les, "nothing relevant") == []


def test_failure_label_filters(tmp_repo):
    _write(tmp_repo, "a.md", "test", ["timeout"], "A")
    _write(tmp_repo, "b.md", "ci", ["timeout"], "B")
    les = lessons.load(str(tmp_repo))
    assert [x["path"] for x in lessons.match(les, "timeout", failure="ci")] == ["b.md"]


def test_cli_and_hook_output(tmp_repo):
    _write(tmp_repo, "a.md", "tool", ["uv run"], "uv が無い")
    r = run_tool(tmp_repo, "tools/lessons.py", ["--match", "uv run failed"])
    assert "uv が無い" in r.stdout
    r = run_tool(tmp_repo, "tools/lessons.py", [])
    assert r.stdout == ""
    import subprocess
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_repo), "YURECHECK_ROLE": "dev"}
    r = subprocess.run([sys.executable, str(tmp_repo / "tools" / "lessons.py")],
                       input=json.dumps({"tool_name": "Bash", "error": "command not found: uv run"}),
                       capture_output=True, text=True, env=env, cwd=tmp_repo)
    assert "additionalContext" in r.stdout and "uv が無い" in r.stdout


def test_silent_without_lessons_dir(tmp_repo):
    r = run_tool(tmp_repo, "tools/lessons.py", ["--match", "anything"])
    assert r.returncode == 0 and r.stdout == ""
