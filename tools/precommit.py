#!/usr/bin/env python3
"""git の pre-commit から呼ぶ。インデックス(staged)を guardlib.scan で検査し、hard か unscanned があれば exit 1。
呼び出し元: .githooks/pre-commit、tools/commit.py。設計: .claude/rules/ops.md。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guardlib  # noqa: E402


def main() -> int:
    root = guardlib.find_repo_root(os.getcwd())
    hard, _soft, unscanned = guardlib.scan(root, guardlib.changed_files(root, "staged"))
    if hard or unscanned:
        print("[precommit] 止めた:", file=sys.stderr)
        for h in hard:
            print(f"- {h}", file=sys.stderr)
        for u in unscanned:
            print(f"- 未検査: {u}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
