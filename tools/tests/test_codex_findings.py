"""Codex の adversarial review(2026-10-07)で再現された12件の回帰テスト。"""
import json
import os
import subprocess
import sys

import pytest
from conftest import REPO, commit_file, git, run_hook, run_tool

sys.path.insert(0, os.path.join(REPO, "tools"))
import guardlib  # noqa: E402
import status  # noqa: E402

GUARD = ".claude/hooks/pretooluse_guard.py"
GATE = ".claude/hooks/pretooluse_commit_gate.py"


# 1. PostToolUse は止められない → commit/push 前のゲートが止める
def test_commit_gate_blocks_staged_secret(tmp_repo):
    git(tmp_repo, "checkout", "-q", "-b", "feat/1-a")
    (tmp_repo / "cfg.json").write_text('{"token": "ghp_abcdefghijklmnopqrstuvwxyz012345"}', encoding="utf-8")
    git(tmp_repo, "add", "cfg.json")
    r = run_hook(tmp_repo, GATE, {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "cwd": str(tmp_repo)}, "dev")
    assert r.returncode == 2 and "秘密" in r.stderr


def test_commit_gate_ignores_other_commands(tmp_repo):
    r = run_hook(tmp_repo, GATE, {"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(tmp_repo)}, "dev")
    assert r.returncode == 0


def test_commit_gate_checks_push_range(tmp_repo):
    # upstream を作り、先のコミットに秘密ファイルを含める
    bare = tmp_repo.parent / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    git(tmp_repo, "remote", "add", "origin", str(bare))
    git(tmp_repo, "push", "-q", "-u", "origin", "main")
    commit_file(tmp_repo, "notes/id_rsa", "-----BEGIN OPENSSH PRIVATE KEY-----\n", "leak")
    r = run_hook(tmp_repo, GATE, {"tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": str(tmp_repo)}, "dev")
    assert r.returncode == 2 and "秘密ファイルの名前" in r.stderr


# 2. worktree へ移っても保護が効く
def test_guard_resolves_root_from_target_file_in_worktree(tmp_repo):
    wt = tmp_repo.parent / "yurecheck-1"
    git(tmp_repo, "worktree", "add", "-q", str(wt), "-b", "feat/1-wt")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(wt / "docs" / "METRICS.md")}, "cwd": str(wt)}
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_repo), "YURECHECK_ROLE": "dev"}
    r = subprocess.run([sys.executable, str(tmp_repo / GUARD)], input=json.dumps(payload), capture_output=True, text=True, env=env, cwd=wt)
    assert r.returncode == 2 and "メンテナが書く" in r.stderr


# 3. 秘密・パス・URL の行のフィルタ
def test_clean_lines_drops_secrets_and_paths():
    kept, dropped = guardlib.clean_lines([
        "- github_pat_abcdefghijklmnopqrstuvwxyz0123",
        "- AKIAABCDEFGHIJKLMNOP を使う",
        "- /home/alice/private を見た",
        "- C:/Users/Alice/private を見た",
        "- C:\\\\Users\\\\Alice\\\\x",
        "- 普通の進捗",
    ])
    assert kept == ["- 普通の進捗"] and dropped == 5


# 4. 一覧の判定(merge 可の条件を含む)
WRITTEN = ("## 何を変えたか、なぜ\n\nSDF の符号をコライダーの和に変えた。開いたメッシュで符号が壊れるため。\n\n"
           "closes #3\n\n## どう確かめたか\n\nEditMode 12 本。\n")
EMPTY = ("## 何を変えたか、なぜ\n\n例: smoke と nightly を、RUNNER_READY 変数があるときだけ走らせた。\n\n"
         "closes #\n\n## どう確かめたか\n")
REVIEWED = [{"body": "[review-pr] 食い違い 0 件"}]
MERGE = "食い違いに答えたら、メンテナが merge する。worktree を消す"


def _s(**kw):
    base = {"branch": "feat/3-x", "dirty": 0, "ahead": 0, "has_upstream": True, "head": "abc1234", "issue": 3, "commits": 2}
    base.update(kw)
    return base


def _t(ok=True):
    return {"fresh": True, "passed": ok, "platforms": ["EditMode", "PlayMode"]}


def _pr(**kw):
    pr = {"number": 1, "headRefName": "feat/3-x", "isDraft": False, "headRefOid": "abc1234def",
          "statusCheckRollup": [{"conclusion": "SUCCESS"}], "reviewDecision": None,
          "body": WRITTEN, "comments": []}
    pr.update(kw)
    return {"available": True, "my_pr": pr}


def _rows(s=None, t=None, g=None, role="dev"):
    rows = status.checklist(s or _s(), _t() if t is None else t, g or _pr(), role)
    return {name: (state, done) for name, state, done in rows}, status.next_action(rows)


def test_list_order_follows_workflow():
    rows = status.checklist(_s(), _t(), _pr(), "dev")
    assert [r[0] for r in rows] == ["作業", "未コミット", "テスト", "push", "PR", "説明", "CI", "レビュー"]


def test_list_right_after_branching_is_all_untouched():
    rows, nxt = _rows(_s(commits=0), t={}, g={"available": True, "my_pr": None})
    assert rows["作業"] == ("未着手", False)
    assert all(v == ("―", None) for k, v in rows.items() if k != "作業")
    assert nxt.startswith("作業")


def test_list_changes_requested_is_not_mergeable():
    rows, nxt = _rows(g=_pr(reviewDecision="CHANGES_REQUESTED", comments=REVIEWED))
    assert rows["レビュー"] == ("変更要求", False) and nxt.startswith("指摘に答えて")


def test_list_merge_needs_written_explanation_and_tool_review_not_approve():
    """1人では自分の PR を approve できない。merge の条件は、説明をメンテナが書いた + /review-pr のコメントがある。"""
    rows, _ = _rows(g=_pr(reviewDecision="APPROVED"))
    assert rows["説明"] == ("書いた", True) and rows["レビュー"] == ("無し", False)
    rows, _ = _rows(g=_pr(body=EMPTY, comments=REVIEWED))
    assert rows["説明"] == ("空", False)
    rows, nxt = _rows(g=_pr(comments=REVIEWED))
    assert all(done for _, done in rows.values()) and nxt == MERGE


def test_list_dirty_or_unpushed_or_other_head():
    rows, nxt = _rows(_s(dirty=2))
    assert rows["未コミット"] == ("変更 2 件", False) and nxt.startswith("uv run tools/commit.py")
    rows, nxt = _rows(_s(ahead=1))
    assert rows["push"] == ("未 push 1 件", False) and "メンテナが打つ" in nxt
    rows, _ = _rows(_s(has_upstream=False, ahead=None), g={"available": True, "my_pr": None})
    assert rows["push"] == ("upstream 無し", False)
    rows, _ = _rows(_s(head="fff0000"))
    assert rows["push"] == ("PR の head と違う", False)


def test_list_test_states_for_dev():
    rows, _ = _rows(t={"fresh": False, "passed": True, "platforms": ["EditMode", "PlayMode"]})
    assert rows["テスト"] == ("古い", False)
    rows, _ = _rows(t={"fresh": True, "passed": True, "platforms": ["EditMode"]})
    assert rows["テスト"] == ("片方だけ", False)
    rows, _ = _rows(t={"fresh": True, "passed": False, "platforms": ["EditMode", "PlayMode"],
                       "summary": {"EditMode": {"total": 0, "failed": 0, "why": "テストが0件"}}})
    assert rows["テスト"] == ("0件", False)
    rows, _ = _rows(t={"fresh": True, "passed": False, "platforms": ["EditMode", "PlayMode"],
                       "summary": {"EditMode": {"total": 3, "failed": 1, "why": ""}}})
    assert rows["テスト"] == ("失敗", False)
    rows, _ = _rows(t={"fresh": True, "passed": False, "skipped": "Unity プロジェクトが無い", "platforms": ["EditMode", "PlayMode"]})
    assert rows["テスト"] == ("飛ばした(Unity プロジェクトが無い)", True)


def test_list_env_reads_pytest_record_only():
    py = {"fresh": True, "passed": True, "platforms": ["pytest"], "summary": {"pytest": {"passed": 53, "failed": 0, "xfailed": 2}}}
    rows, _ = _rows(t=py, role="env")
    assert rows["テスト"] == ("通った(既知の失敗 2 件)", True)
    rows, _ = _rows(t=_t(), role="env")
    assert rows["テスト"] == ("未実行", False)
    rows, _ = _rows(t=py, role="dev")
    assert rows["テスト"] == ("未実行", False)


def test_list_ci_waiting_and_no_gh():
    rows, nxt = _rows(g=_pr(statusCheckRollup=[], comments=REVIEWED))
    assert rows["CI"] == ("待ち", False) and nxt == "CI の完了を待つ"
    rows, nxt = _rows(g={"available": False})
    assert rows["PR"] == ("不明(gh 無し)", False) and "gh" in nxt


def test_issue_number_from_branch_names():
    assert status.issue_number("feat/3-status-list") == 3
    assert status.issue_number("worktree-12-x") == 12
    assert status.issue_number("main") is None and status.issue_number("fix-9") is None


# 5. test.py の偽成功
WINDOWS_PYTEST = "docs/proposals/2026-10-10-windows-pytest.md"


def _unity_project(tmp_repo):
    (tmp_repo / "ProjectSettings").mkdir(exist_ok=True)
    (tmp_repo / "ProjectSettings" / "ProjectVersion.txt").write_text("m_EditorVersion: 6000.3.18f1\n", encoding="utf-8")


@pytest.mark.xfail(sys.platform == "win32", raises=FileNotFoundError, strict=True,
                   reason=f"偽の Unity(unity.sh)を Windows で起動できず last_test.json が出ない。{WINDOWS_PYTEST}")
def test_test_py_does_not_reuse_old_xml(tmp_repo):
    _unity_project(tmp_repo)
    (tmp_repo / "results").mkdir(exist_ok=True)
    (tmp_repo / "results" / "editmode.xml").write_text('<test-run total="3" failed="0"/>', encoding="utf-8")
    fake_unity = tmp_repo / "unity.sh"
    fake_unity.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    fake_unity.chmod(0o755)
    r = run_tool(tmp_repo, "tools/test.py", ["--edit"], extra_env={"UNITY_PATH": str(fake_unity)})
    assert r.returncode == 1
    last = json.loads((tmp_repo / "results" / "last_test.json").read_text(encoding="utf-8"))
    assert last["passed"] is False and "XML が出なかった" in last["summary"]["EditMode"]["why"]


def test_test_py_zero_tests_is_not_success(tmp_repo):
    _unity_project(tmp_repo)
    fake_unity = tmp_repo / "unity.sh"
    fake_unity.write_text("#!/bin/sh\nout=''\nwhile [ $# -gt 0 ]; do if [ \"$1\" = -testResults ]; then out=$2; fi; shift; done\n"
                          "echo '<test-run total=\"0\" failed=\"0\"/>' > \"$out\"\nexit 0\n", encoding="utf-8")
    fake_unity.chmod(0o755)
    r = run_tool(tmp_repo, "tools/test.py", ["--edit"], extra_env={"UNITY_PATH": str(fake_unity)})
    assert r.returncode == 1



def _marking_unity(tmp_repo):
    """起動したら印のファイルを書く偽の Unity。"""
    mark = tmp_repo / "unity_started"
    if sys.platform == "win32":
        fake = tmp_repo / "unity.cmd"
        fake.write_text(f'@echo x > "{mark}"\r\n', encoding="utf-8")
    else:
        fake = tmp_repo / "unity.sh"
        fake.write_text(f"#!/bin/sh\necho x > '{mark}'\n", encoding="utf-8")
        fake.chmod(0o755)
    return fake, mark


def test_test_py_skips_without_unity_project(tmp_repo):
    fake, mark = _marking_unity(tmp_repo)
    r = run_tool(tmp_repo, "tools/test.py", [], extra_env={"UNITY_PATH": str(fake)})
    assert r.returncode == 0 and not mark.exists()
    assert "ProjectSettings/ProjectVersion.txt が無い" in r.stdout + r.stderr
    last = json.loads((tmp_repo / "results" / "last_test.json").read_text(encoding="utf-8"))
    head = git(tmp_repo, "rev-parse", "--short", "HEAD").stdout.strip()
    assert last["skipped"] == "Unity プロジェクトが無い" and last["commit"] == head and last["passed"] is False


def _pytest_suite(tmp_repo, body):
    (tmp_repo / "tools" / "tests").mkdir(exist_ok=True)
    (tmp_repo / "tools" / "tests" / "test_x.py").write_text("import pytest\n\n\n" + body, encoding="utf-8")


def test_test_py_env_runs_pytest_and_counts_known_failures(tmp_repo):
    _pytest_suite(tmp_repo, "def test_ok():\n    pass\n\n\n"
                            "@pytest.mark.xfail(raises=KeyError, strict=True, reason='#9')\n"
                            "def test_known():\n    raise KeyError\n")
    r = run_tool(tmp_repo, "tools/test.py", [], role="env")
    assert r.returncode == 0, r.stdout + r.stderr
    last = json.loads((tmp_repo / "results" / "last_test.json").read_text(encoding="utf-8"))
    assert last["platforms"] == ["pytest"] and last["passed"] is True
    assert last["summary"]["pytest"]["passed"] == 1 and last["summary"]["pytest"]["xfailed"] == 1


def test_test_py_env_reports_unknown_failures_by_name(tmp_repo):
    _pytest_suite(tmp_repo, "@pytest.mark.xfail(raises=KeyError, strict=True, reason='#9')\n"
                            "def test_known():\n    raise ValueError\n")
    r = run_tool(tmp_repo, "tools/test.py", [], role="env")
    assert r.returncode == 1
    last = json.loads((tmp_repo / "results" / "last_test.json").read_text(encoding="utf-8"))
    assert last["passed"] is False and last["summary"]["pytest"]["failed_tests"] == ["tools/tests/test_x.py::test_known"]

# 6. commit.py: 指定外のステージ済み
def test_commit_refuses_when_other_changes_are_staged(tmp_repo):
    git(tmp_repo, "checkout", "-q", "-b", "feat/4-c")
    (tmp_repo / "a.txt").write_text("a\n", encoding="utf-8")
    (tmp_repo / "secret.txt").write_text("s\n", encoding="utf-8")
    git(tmp_repo, "add", "secret.txt")
    r = run_tool(tmp_repo, "tools/commit.py", ["a を足した", "a.txt"])
    assert r.returncode == 2 and "指定外" in r.stderr


# 9. commit.py: unborn と detached とルート指定
def test_commit_refuses_unborn_main(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    for d in ("tools",):
        subprocess.run(["cp", "-r", os.path.join(REPO, d), str(tmp_path)], check=True)
    (tmp_path / "a.txt").write_text("a\n", encoding="utf-8")
    env = {**os.environ, "YURECHECK_ROLE": "dev"}
    r = subprocess.run([sys.executable, str(tmp_path / "tools" / "commit.py"), "x", "a.txt"],
                       capture_output=True, text=True, env=env, cwd=tmp_path)
    assert r.returncode == 2 and "main" in r.stderr


def test_commit_refuses_detached_and_root_specs(tmp_repo):
    git(tmp_repo, "checkout", "-q", "-b", "feat/5-d")
    for spec in (":/", "./.", str(tmp_repo)):
        r = run_tool(tmp_repo, "tools/commit.py", ["x", spec])
        assert r.returncode == 2, spec
    head = git(tmp_repo, "rev-parse", "HEAD").stdout.strip()
    git(tmp_repo, "checkout", "-q", head)
    (tmp_repo / "a.txt").write_text("a\n", encoding="utf-8")
    r = run_tool(tmp_repo, "tools/commit.py", ["x", "a.txt"])
    assert r.returncode == 2 and "detached" in r.stderr


def _scan(repo):
    return guardlib.scan(str(repo), guardlib.changed_files(str(repo), "status"))


# 7. 日本語ファイル名
def test_scan_sees_non_ascii_filenames(tmp_repo):
    (tmp_repo / "資料.json").write_text('{"token": "ghp_abcdefghijklmnopqrstuvwxyz012345"}', encoding="utf-8")
    hard, _, _ = _scan(tmp_repo)
    assert any("資料.json" in h for h in hard)


# 8. 秘密ファイル名と JSON のパスワード
def test_scan_blocks_env_and_pem_and_json_password(tmp_repo):
    (tmp_repo / ".env").write_text("X=1\n", encoding="utf-8")
    (tmp_repo / "c.json").write_text('{"password": "abcdefghijk"}', encoding="utf-8")
    (tmp_repo / "k.pem").write_text("x\n", encoding="utf-8")
    hard, _, _ = _scan(tmp_repo)
    joined = "\n".join(hard)
    assert ".env" in joined and "c.json" in joined and "k.pem" in joined


def test_scan_reports_unscanned_big_text(tmp_repo):
    with open(tmp_repo / "big.txt", "w", encoding="utf-8") as f:
        f.write("a" * (3 * 1024 * 1024))
    hard, _, unscanned = _scan(tmp_repo)
    assert not hard and any("big.txt" in u for u in unscanned)


def test_commit_gate_blocks_unscanned(tmp_repo):
    git(tmp_repo, "checkout", "-q", "-b", "feat/9-u")
    with open(tmp_repo / "big.txt", "w", encoding="utf-8") as f:
        f.write("a" * (3 * 1024 * 1024))
    git(tmp_repo, "add", "big.txt")
    r = run_hook(tmp_repo, GATE, {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "cwd": str(tmp_repo)}, "dev")
    assert r.returncode == 2 and "未検査" in r.stderr


# 10. settings と role_paths の整合
def test_settings_deny_covers_role_paths():
    rp = json.load(open(os.path.join(REPO, ".claude", "role_paths.json"), encoding="utf-8"))
    for name in ("settings.env.json", "settings.dev.json"):
        d = json.load(open(os.path.join(REPO, ".claude", name), encoding="utf-8"))
        deny = set(d["permissions"]["deny"])
        for g in rp["owner_written"]:
            assert f"Write(./{g})" in deny and f"Edit(./{g})" in deny, (name, g)
    d = json.load(open(os.path.join(REPO, ".claude", "settings.dev.json"), encoding="utf-8"))
    deny = set(d["permissions"]["deny"])
    for g in ("AGENTS.md", ".claude/**", ".github/**", "tools/**", "docs/ops/**"):
        assert f"Write(./{g})" in deny, g


# 11. determinism: 0 組は失敗
def test_determinism_fails_on_empty_or_missing(tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "determinism.py"), str(d)], capture_output=True, text=True)
    assert r.returncode == 1 and "足りない" in r.stdout
    (d / "frames_a_r1.csv").write_text("1\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "determinism.py"), str(d)], capture_output=True, text=True)
    assert r.returncode == 1 and "r2 が無い" in r.stdout
    (d / "frames_a_r2.csv").write_text("1\n", encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "determinism.py"), str(d)], capture_output=True, text=True)
    assert r.returncode == 0


# 12. allow に破壊的な引数を通す項目が無い
def test_shared_allow_has_no_mutating_commands():
    d = json.load(open(os.path.join(REPO, ".claude", "settings.json"), encoding="utf-8"))
    allow = d["permissions"]["allow"]
    assert "Bash(git branch:*)" not in allow and "Bash(uv run ruff check:*)" not in allow
    assert "Bash(uv run ruff check --fix:*)" in d["permissions"]["deny"]
    assert "PostToolUse" not in d["hooks"]
