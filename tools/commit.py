#!/usr/bin/env python3
"""コミットの規律(雛形 4)。渡したパスだけ、か手元の変更の全部をステージしてコミットする。
  uv run tools/commit.py "件名" <パス> [<パス> ...]   渡したパスだけ(削除と移動も。git add -A -- <パス>。
                                                      git mv/git rm で既にステージ済みの旧パスは add に渡さない)
  uv run tools/commit.py "件名" --all                 .gitignore に無い変更の全部
拒む条件: パスに -A/./ルート指定、main か detached HEAD か unborn のブランチが読めないとき、指定外の変更が既にステージされているとき、
--all でもう一方の役割の範囲かメンテナが書くファイル(.claude/role_paths.json)の変更が混ざるとき、
公開前の検査(tools/precommit.py と同じ)に当たるとき。件名の bot: は自動側の接頭辞で人は使わない。
呼び出し元: 両方の役割。設計: docs/ops/WORKFLOW.md 3。
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guardlib  # noqa: E402

ROOT_SPECS = ("-A", "--all", ".", "./", ":/", ":", "./.", "/")
ROLE = os.environ.get("YURECHECK_ROLE", "")


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def current_branch():
    r = run(["git", "symbolic-ref", "--short", "-q", "HEAD"])
    if r.returncode != 0:
        return None  # detached HEAD
    return r.stdout.strip()


def already_staged_away(p, root, staged):
    """git mv / git rm で既にステージ済みの旧パス。index にも作業ツリーにも無く、git add に渡すと pathspec で落ちる。"""
    r = guardlib.rel(p, root)
    if os.path.lexists(p) or run(["git", "ls-files", "--", p]).stdout:
        return False
    return any(s == r or s.startswith(r.rstrip("/") + "/") for s in staged)


def not_mine(root, files):
    """--all で混ざってはいけない変更。もう一方の役割の範囲と、メンテナが書くファイル。"""
    rp = guardlib.load_role_paths(root) or {}
    other = rp.get("dev_only") if ROLE == "ops" else rp.get("ops_only")
    return [f for f in files if guardlib.matches(f, rp.get("owner_written")) or guardlib.matches(f, other)]


def main() -> int:
    if len(sys.argv) < 3:
        print('使い方: uv run tools/commit.py "件名" <パス> [<パス> ...] か --all', file=sys.stderr)
        return 2
    msg, paths = sys.argv[1], sys.argv[2:]
    root = guardlib.find_repo_root(os.getcwd())
    every = paths == ["--all"]
    for p in [] if every else paths:
        norm = os.path.normpath(p).replace("\\", "/")
        if p in ROOT_SPECS or norm in (".", "/") or p.startswith(":"):
            print(f"全体のステージは受けない: {p}", file=sys.stderr)
            return 2
        if os.path.isabs(p) and os.path.abspath(p) == root:
            print(f"全体のステージは受けない: {p}", file=sys.stderr)
            return 2
    if msg.startswith("bot:"):
        print("bot: は自動側の接頭辞。人のコミットには使わない", file=sys.stderr)
        return 2
    branch = current_branch()
    if branch is None:
        print("detached HEAD ではコミットしない。Issue のブランチへ", file=sys.stderr)
        return 2
    if branch == "main":
        print("main には直接コミットしない。Issue のブランチ(worktree)で作業する", file=sys.stderr)
        return 2
    staged = [s for s in run(["git", "diff", "--cached", "--name-only", "--no-renames", "-z"]).stdout.split("\0") if s]
    wanted = {guardlib.rel(p, root) for p in paths}
    other = [] if every else [s for s in staged if s not in wanted]
    if other:
        print("指定外の変更が既にステージされている。先に git restore --staged で外すこと: " + ", ".join(other[:5]), file=sys.stderr)
        return 2
    to_add = [p for p in paths if not already_staged_away(p, root, staged)]
    r = run(["git", "add", "-A"] if every else ["git", "add", "-A", "--", *to_add]) if every or to_add else None
    if r and r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return r.returncode
    if run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print("ステージされた変更なし")
        return 0
    files = guardlib.changed_files(root, "staged")
    foreign = not_mine(root, files) if every else []
    if foreign:
        run(["git", "reset", "-q"])
        print("--all に、この役割では書かない変更が混ざっている。パスを渡してコミットすること: " + ", ".join(foreign[:5]),
              file=sys.stderr)
        return 2
    hard, _soft, unscanned = guardlib.scan(root, files)
    if hard or unscanned:
        print("公開前の検査で止めた:\n- " + "\n- ".join(hard + [f"未検査: {u}" for u in unscanned]), file=sys.stderr)
        return 2
    r = run(["git", "commit", "-q", "-m", msg])
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return r.returncode
    print(run(["git", "log", "--oneline", "-1"]).stdout.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
