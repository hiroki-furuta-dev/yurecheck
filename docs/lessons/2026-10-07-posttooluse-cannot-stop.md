---
failure: hook
keywords: [PostToolUse, exit 2, commit, push, 止まらない]
---
# PostToolUse の exit 2 は済んだ操作を取り消せない

編集直後の PostToolUse hook で秘密を見つけても、同じ Bash で commit と push まで済んでいれば取り消せない。止めるのは PreToolUse(commit/push の前)と git の pre-commit。PostToolUse は削った。回帰テスト: tools/tests/test_codex_findings.py の commit gate。
