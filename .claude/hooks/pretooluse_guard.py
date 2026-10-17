#!/usr/bin/env python3
"""PreToolUse hook(Write/Edit/MultiEdit): settings の deny の保険。
役割(YURECHECK_ROLE=ops|dev)と .claude/role_paths.json を見て、
- メンテナが書くファイル(owner_written)への Write/Edit は、どちらの役割でも止める
- 運用の範囲(ops_only)への Write/Edit は、ops 以外の役割では止める
- 製品の範囲(dev_only)への Write/Edit は、ops の役割では止める(2つの役割を混ぜない)
ルートは対象ファイルから git のルート(worktree を含む)を解く。CLAUDE_PROJECT_DIR は開始地点のまま動かないので使わない。
止めるときは exit 2 で理由を stderr に出す。判断できないときは止めない。
スクリプト自体が起動できない・落ちたときは settings の `|| exit 2` が閉じる。
呼び出し元: .claude/settings.json。設計: .claude/rules/ops.md。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
try:
    import guardlib
except Exception:
    guardlib = None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if guardlib is None or data.get("tool_name", "") not in ("Write", "Edit", "MultiEdit"):
        return 0
    ti = data.get("tool_input", {}) or {}
    paths = [ti["file_path"]] if ti.get("file_path") else []
    paths += [e["file_path"] for e in (ti.get("edits") or []) if isinstance(e, dict) and e.get("file_path")]
    if not paths:
        return 0
    role = os.environ.get("YURECHECK_ROLE", "")
    for p in paths:
        root = guardlib.find_repo_root(p)
        here = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
        rp = guardlib.load_role_paths(root, fallbacks=(here,))
        if rp is None:
            continue
        r = guardlib.rel(p, root)
        if guardlib.matches(r, rp.get("owner_written")):
            sys.stderr.write(f"[guard] {r} はメンテナが書くファイル(docs/OWNER_WRITTEN.md)。AI は書かない。"
                             "提案は PR のコメントに書く。\n")
            return 2
        if role != "ops" and guardlib.matches(r, rp.get("ops_only")):
            sys.stderr.write(f"[guard] {r} は運用の範囲。役割 '{role or '未指定'}' では書けない。"
                             "変えたいときは「要望」の Issue を立てる(要件だけ。.github/ISSUE_TEMPLATE/request.yml)。"
                             "運用の役割で開くには: claude --settings .claude/settings.ops.json\n")
            return 2
        if role == "ops" and guardlib.matches(r, rp.get("dev_only")):
            sys.stderr.write(f"[guard] {r} は製品の範囲。役割 'ops' では書けない。"
                             "変えたいときは「要望」の Issue を立てる。開発の役割で開くには: claude --settings .claude/settings.dev.json\n")
            return 2
    if not role:
        sys.stderr.write("[guard] YURECHECK_ROLE が未設定。--settings .claude/settings.ops.json か settings.dev.json で起動すること。\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
