#!/usr/bin/env python3
"""コミットの規律(雛形 4)。渡したパスだけをステージしてコミットする。
  uv run tools/commit.py "件名" <パス> [<パス> ...]
拒む条件: -A/./ルート指定、main か detached HEAD か unborn のブランチが読めないとき、指定外の変更が既にステージされているとき、
公開前の検査(tools/precommit.py と同じ)に当たるとき。件名の bot: は自動側の接頭辞で人は使わない。
呼び出し元: 両方の役割。設計: docs/ops/WORKFLOW.md 3。
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guardlib  # noqa: E402

ROOT_SPECS = ("-A", "--all", ".", "./", ":/", ":", "./.", "/")


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def current_branch():
    r = run(["git", "symbolic-ref", "--short", "-q", "HEAD"])
    if r.returncode != 0:
        return None  # detached HEAD
    return r.stdout.strip()


def main() -> int:
    if len(sys.argv) < 3:
        print('使い方: uv run tools/commit.py "件名" <パス> [<パス> ...]', file=sys.stderr)
        return 2
    msg, paths = sys.argv[1], sys.argv[2:]
    root = guardlib.find_repo_root(os.getcwd())
    for p in paths:
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
    staged = [s for s in run(["git", "diff", "--cached", "--name-only", "-z"]).stdout.split("\0") if s]
    wanted = {guardlib.rel(p, root) for p in paths}
    other = [s for s in staged if s not in wanted]
    if other:
        print("指定外の変更が既にステージされている。先に git restore --staged で外すこと: " + ", ".join(other[:5]), file=sys.stderr)
        return 2
    r = run(["git", "add", "--", *paths])
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return r.returncode
    if run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print("ステージされた変更なし")
        return 0
    hard, _soft, unscanned = guardlib.scan(root, guardlib.changed_files(root, "staged"))
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
