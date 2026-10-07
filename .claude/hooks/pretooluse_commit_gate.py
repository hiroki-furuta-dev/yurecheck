#!/usr/bin/env python3
"""PreToolUse hook(Bash): 公開前のゲート。
Bash の command に git commit / git push / gh pr create / gh pr merge が含まれるとき、
- commit: インデックス(staged)の内容を guardlib.scan で検査
- push / pr: upstream より先のコミットに含まれるファイルを検査
hard(秘密、秘密ファイル名、LFS 外の大きなファイル)か unscanned(走査できなかった)があれば exit 2 で止める。
PostToolUse の pubguard は事後の注意で、止めるのはこの hook と .githooks/pre-commit。
呼び出し元: .claude/settings.json。設計: .claude/rules/ops.md。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
try:
    import guardlib
except Exception:
    guardlib = None

COMMIT = re.compile(r"\bgit\s+(-C\s+\S+\s+)?commit\b")
PUSH = re.compile(r"\bgit\s+(-C\s+\S+\s+)?push\b|\bgh\s+pr\s+(create|merge)\b")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if guardlib is None or data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    mode = "push" if PUSH.search(cmd) else ("staged" if COMMIT.search(cmd) else None)
    if not mode:
        return 0
    root = guardlib.find_repo_root(data.get("cwd") or os.getcwd())
    files = guardlib.changed_files(root, mode)
    hard, _soft, unscanned = guardlib.scan(root, files)
    if hard or unscanned:
        msg = "[gate] 公開前の検査で止めた。直すまで commit/push しない:\n"
        msg += "".join(f"- {h}\n" for h in hard) + "".join(f"- 未検査: {u}\n" for u in unscanned)
        sys.stderr.write(msg)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
