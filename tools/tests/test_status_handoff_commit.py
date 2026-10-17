import json
import subprocess

from conftest import run_tool


def test_status_on_main_prints_only_the_way_to_a_branch(tmp_repo):
    r = run_tool(tmp_repo, "tools/status.py", [])
    assert r.returncode == 0 and "役割: dev" in r.stdout and "Issue のブランチへ" in r.stdout
    assert "] 作業:" not in r.stdout


def _commit_all(tmp_repo):
    (tmp_repo / ".gitignore").write_text("__pycache__/\nresults/\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "all"], cwd=tmp_repo, check=True)


def test_status_fresh_branch_lists_all_untouched(tmp_repo):
    _commit_all(tmp_repo)
    subprocess.run(["git", "checkout", "-q", "-b", "worktree-5-x"], cwd=tmp_repo, check=True)
    r = run_tool(tmp_repo, "tools/status.py", [], role="env")
    assert "(Issue #5)" in r.stdout and "- [未] 作業: 未着手" in r.stdout and "- [―] テスト: ―" in r.stdout
    assert "残り: 作業" in r.stdout


def test_status_proposals_are_outside_the_list(tmp_repo):
    (tmp_repo / "docs" / "proposals" / "2026-01-01-x.md").write_text("# x\n", encoding="utf-8")
    _commit_all(tmp_repo)
    subprocess.run(["git", "checkout", "-q", "-b", "feat/6-y"], cwd=tmp_repo, check=True)
    for role in ("env", "dev"):
        r = run_tool(tmp_repo, "tools/status.py", [], role=role)
        line = next(ln for ln in r.stdout.splitlines() if ln.startswith("proposals: "))
        assert "2026-01-01-x.md" in line and "] proposals" not in r.stdout


def test_status_hook_outputs_json(tmp_repo):
    r = run_tool(tmp_repo, "tools/status.py", ["--hook"])
    assert r.stdout.startswith("{") and "additionalContext" in r.stdout


def test_commit_refuses_all_and_main(tmp_repo):
    r = run_tool(tmp_repo, "tools/commit.py", ["件名", "-A"])
    assert r.returncode == 2
    (tmp_repo / "a.txt").write_text("a\n", encoding="utf-8")
    r = run_tool(tmp_repo, "tools/commit.py", ["件名", "a.txt"])
    assert r.returncode == 2 and "main" in r.stderr


def test_commit_stages_only_given_paths(tmp_repo):
    subprocess.run(["git", "checkout", "-q", "-b", "feat/1-x"], cwd=tmp_repo, check=True)
    (tmp_repo / "a.txt").write_text("a\n", encoding="utf-8")
    (tmp_repo / "b.txt").write_text("b\n", encoding="utf-8")
    r = run_tool(tmp_repo, "tools/commit.py", ["a を足した", "a.txt"])
    assert r.returncode == 0
    st = subprocess.run(["git", "status", "--porcelain"], cwd=tmp_repo, capture_output=True, text=True).stdout
    assert "b.txt" in st and "a.txt" not in st


def test_models_counts_from_session_transcript(tmp_repo):
    t = tmp_repo / "t.jsonl"
    t.write_text('{"type":"user","message":{"role":"user","content":"x"}}\n'
                 '{"type":"assistant","message":{"role":"assistant","model":"model-a","content":[]}}\n'
                 '{"type":"assistant","message":{"role":"assistant","model":"model-a","content":[]}}\n'
                 '{"type":"assistant","message":{"role":"assistant","model":"model-b","content":[]}}\n', encoding="utf-8")
    (tmp_repo / "results").mkdir(exist_ok=True)
    (tmp_repo / "results" / ".session_meta.json").write_text(json.dumps({"transcript_path": str(t)}), encoding="utf-8")
    r = run_tool(tmp_repo, "tools/models.py", [])
    assert r.returncode == 0 and r.stdout.strip() == "使ったモデル: model-a (2 発話), model-b (1 発話)"
