import json
import os
import shutil
import subprocess

import pytest
from conftest import run_hook

GUARD = ".claude/hooks/pretooluse_guard.py"


def payload(repo, rel, tool="Write"):
    return {"tool_name": tool, "tool_input": {"file_path": str(repo / rel)}, "cwd": str(repo)}


def test_dev_cannot_write_ops_paths(tmp_repo):
    r = run_hook(tmp_repo, GUARD, payload(tmp_repo, ".github/workflows/x.yml"), "dev")
    assert r.returncode == 2 and "運用の範囲" in r.stderr


def test_ops_can_write_ops_paths(tmp_repo):
    r = run_hook(tmp_repo, GUARD, payload(tmp_repo, ".github/workflows/x.yml"), "ops")
    assert r.returncode == 0


def test_ops_cannot_write_product_paths(tmp_repo):
    """Unity が書くファイル(Packages/、ProjectSettings/)と core/ も製品の範囲。"""
    for rel in ("Assets/a.cs", "Packages/manifest.json", "ProjectSettings/ProjectVersion.txt", "core/Yurecheck.Core/Units/M.cs"):
        r = run_hook(tmp_repo, GUARD, payload(tmp_repo, rel), "ops")
        assert r.returncode == 2 and "製品の範囲" in r.stderr, rel
        assert run_hook(tmp_repo, GUARD, payload(tmp_repo, rel), "dev").returncode == 0, rel


def test_both_roles_can_write_shared_docs(tmp_repo):
    for role in ("ops", "dev"):
        assert run_hook(tmp_repo, GUARD, payload(tmp_repo, "docs/lessons/x.md"), role).returncode == 0


def test_owner_written_blocked_for_both_roles(tmp_repo):
    for role in ("dev", "ops"):
        r = run_hook(tmp_repo, GUARD, payload(tmp_repo, "docs/METRICS.md"), role)
        assert r.returncode == 2 and "メンテナが書く" in r.stderr


def test_dev_can_write_assets(tmp_repo):
    r = run_hook(tmp_repo, GUARD, payload(tmp_repo, "Assets/Yurecheck/Runtime/Foo.cs"), "dev")
    assert r.returncode == 0


def test_multiedit_checks_every_path(tmp_repo):
    p = {"tool_name": "MultiEdit", "tool_input": {"edits": [{"file_path": str(tmp_repo / "Assets/a.cs")},
                                                            {"file_path": str(tmp_repo / "tools/x.py")}]}, "cwd": str(tmp_repo)}
    r = run_hook(tmp_repo, GUARD, p, "dev")
    assert r.returncode == 2


def test_non_write_tools_pass(tmp_repo):
    r = run_hook(tmp_repo, GUARD, {"tool_name": "Bash", "tool_input": {"command": "ls"}}, "dev")
    assert r.returncode == 0


def test_owner_written_core_paths_blocked_and_other_core_allowed(tmp_repo):
    """docs/adr/0018: メンテナが書く Judge と参照実装は core/ にある。"""
    for role in ("dev", "ops"):
        r = run_hook(tmp_repo, GUARD, payload(tmp_repo, "core/Yurecheck.Core/Judge/Verdict.cs"), role)
        assert r.returncode == 2 and "メンテナが書く" in r.stderr
        r = run_hook(tmp_repo, GUARD, payload(tmp_repo, "core/Yurecheck.Core/Measure/PenetrationReference.cs"), role)
        assert r.returncode == 2
    r = run_hook(tmp_repo, GUARD, payload(tmp_repo, "core/Yurecheck.Core/Units/Millimeters.cs"), "dev")
    assert r.returncode == 0


def test_pretooluse_gates_fail_closed_in_settings():
    """起動できない hook は非ブロックで通る仕様なので、止める役の2つは `|| exit 2` で閉じる。"""
    from conftest import REPO

    d = json.load(open(os.path.join(REPO, ".claude", "settings.json"), encoding="utf-8"))
    gates = {g["matcher"]: g["hooks"][0]["command"] for g in d["hooks"]["PreToolUse"]}
    assert set(gates) == {"Write|Edit|MultiEdit", "Bash"}
    assert gates["Write|Edit|MultiEdit"].endswith(" || exit 2") and "${CLAUDE_PROJECT_DIR:-.}" in gates["Write|Edit|MultiEdit"]
    assert gates["Bash"].startswith('sh "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/commit_gate.sh"')
    others = [h["command"] for ev, gs in d["hooks"].items() if ev != "PreToolUse" for g in gs for h in g["hooks"]]
    assert others and all(not c.endswith("|| exit 2") for c in others)



def test_commit_gate_sh_without_uv_blocks_only_commit_push(tmp_repo):
    """Codex 2回目の指摘: uv が無いと Bash が全部止まり doctor に届かない。検査が起動できないときは commit/push だけ止める。
    sh は PATH から探す(Windows は Git for Windows の usr/bin)。PATH は sh のある場所だけにして、coreutils はあるが uv は無い状態を作る。"""
    sh = shutil.which("sh")
    if not sh:
        pytest.skip("sh が無い(Windows なら Git for Windows を入れる)")
    path = os.path.dirname(sh)
    if shutil.which("uv", path=path):
        pytest.skip(f"uv が {path} にある環境では再現できない")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_repo), "PATH": path}

    def run(cmd):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
        return subprocess.run([sh, str(tmp_repo / ".claude" / "hooks" / "commit_gate.sh")], input=payload, capture_output=True,
                              text=True, env=env, cwd=tmp_repo)

    r = run("git commit -m x")
    assert r.returncode == 2 and "起動できない" in r.stderr
    assert run("cd a && git push -u origin b").returncode == 2
    assert run("uv run tools/doctor.py").returncode == 0
    assert run("git status").returncode == 0
