import json

from conftest import git, run_tool

DOCTOR = "tools/doctor.py"


def test_doctor_reports_hookspath_and_json(tmp_repo):
    r = run_tool(tmp_repo, DOCTOR, ["--json"])
    d = json.loads(r.stdout)
    byname = {c["name"]: c for c in d["checks"]}
    hp = byname["core.hooksPath = .githooks"]
    assert not hp["ok"] and hp["fix"] and r.returncode == 1
    git(tmp_repo, "config", "core.hooksPath", ".githooks")
    r = run_tool(tmp_repo, DOCTOR, ["--json"])
    d = json.loads(r.stdout)
    assert {c["name"]: c for c in d["checks"]}["core.hooksPath = .githooks"]["ok"]


def test_doctor_text_marks_required_failures(tmp_repo):
    r = run_tool(tmp_repo, DOCTOR, [], role="")
    assert "NG [必須] core.hooksPath" in r.stdout and "YURECHECK_ROLE: 未設定" in r.stdout
    assert "変更" not in r.stdout  # 何も変えない


def test_find_git_bash_rejects_wsl_and_prefers_git_tree(tmp_path):
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import doctor

    git = tmp_path / "Git" / "cmd" / "git.exe"
    git.parent.mkdir(parents=True)
    git.write_text("")
    (tmp_path / "Git" / "bin").mkdir()
    (tmp_path / "Git" / "bin" / "bash.exe").write_text("")
    table = {"git": str(git), "bash": r"C:\Windows\System32\bash.exe"}
    p, why = doctor.find_git_bash({}, table.get)
    assert p == str(tmp_path / "Git" / "bin" / "bash.exe")
    p, why = doctor.find_git_bash({}, {"bash": r"C:\Windows\System32\bash.exe"}.get)
    assert p is None and "WSL" in why
    p, why = doctor.find_git_bash({"CLAUDE_CODE_GIT_BASH_PATH": str(tmp_path / "nope.exe")}, {}.get)
    assert p is None
