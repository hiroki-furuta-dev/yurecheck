import subprocess

from conftest import run_tool


def test_status_stage0_on_clean_main(tmp_repo):
    r = run_tool(tmp_repo, "tools/status.py", [])
    assert r.returncode == 0 and "段階: 0 着手前" in r.stdout and "役割: dev" in r.stdout


def test_status_env_role_reads_proposals(tmp_repo):
    (tmp_repo / "docs" / "proposals" / "2026-01-01-x.md").write_text("# x\n", encoding="utf-8")
    r = run_tool(tmp_repo, "tools/status.py", [], role="env")
    assert "proposals 未対応" in r.stdout and "2026-01-01-x.md" in r.stdout


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


def test_handoff_writes_repo_file_and_status_reads_it(tmp_repo):
    subprocess.run(["git", "checkout", "-q", "-b", "feat/2-y"], cwd=tmp_repo, check=True)
    (tmp_repo / "c.txt").write_text("c\n", encoding="utf-8")
    subprocess.run(["git", "add", "c.txt"], cwd=tmp_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "c を足した"], cwd=tmp_repo, check=True)
    r = run_tool(tmp_repo, "tools/handoff.py", [])
    assert r.returncode == 0 and "HANDOFF:" in r.stdout
    files = list((tmp_repo / "docs" / "handoff").glob("*-dev.md"))
    assert len(files) == 1 and "c を足した" in files[0].read_text(encoding="utf-8")
    r = run_tool(tmp_repo, "tools/status.py", [])
    assert "前回:" in r.stdout and "c を足した" in r.stdout


def test_handoff_drops_paths_and_urls(tmp_repo):
    subprocess.run(["git", "checkout", "-q", "-b", "feat/3-z"], cwd=tmp_repo, check=True)
    (tmp_repo / "d.txt").write_text("d\n", encoding="utf-8")
    subprocess.run(["git", "add", "d.txt"], cwd=tmp_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "see https://example.com/x"], cwd=tmp_repo, check=True)
    run_tool(tmp_repo, "tools/handoff.py", [])
    f = list((tmp_repo / "docs" / "handoff").glob("*-dev.md"))[0].read_text(encoding="utf-8")
    assert "example.com" not in f and "省いた" in f


def test_handoff_counts_models_from_transcript(tmp_repo):
    subprocess.run(["git", "checkout", "-q", "-b", "feat/4-m"], cwd=tmp_repo, check=True)
    (tmp_repo / "e.txt").write_text("e\n", encoding="utf-8")
    subprocess.run(["git", "add", "e.txt"], cwd=tmp_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "e を足した"], cwd=tmp_repo, check=True)
    t = tmp_repo / "t.jsonl"
    t.write_text('{"type":"user","message":{"role":"user","content":"x"}}\n'
                 '{"type":"assistant","message":{"role":"assistant","model":"model-a","content":[]}}\n'
                 '{"type":"assistant","message":{"role":"assistant","model":"model-a","content":[]}}\n'
                 '{"type":"assistant","message":{"role":"assistant","model":"model-b","content":[]}}\n', encoding="utf-8")
    r = run_tool(tmp_repo, "tools/handoff.py", ["--transcript", str(t)])
    assert r.returncode == 0
    f = list((tmp_repo / "docs" / "handoff").glob("*-dev.md"))[0].read_text(encoding="utf-8")
    assert "使ったモデル: model-a (2 発話), model-b (1 発話)" in f
