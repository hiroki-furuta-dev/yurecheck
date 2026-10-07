#!/bin/sh
# Bash の PreToolUse hook。stdin の JSON を pretooluse_commit_gate.py に渡す。
# ゲート本体が起動できないとき(uv が無い、落ちた)は、commit/push/pr の命令だけ止め(exit 2)、
# それ以外の Bash(doctor、git status、導入の手順)は通す。uv の導入前でも入口に届くようにするため。
# 呼び出し元: .claude/settings.json(PreToolUse Bash)。設計: .claude/rules/ops.md。
in=$(cat)
printf '%s' "$in" | uv run --quiet "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/pretooluse_commit_gate.py"
rc=$?
if [ "$rc" -eq 0 ] || [ "$rc" -eq 2 ]; then
  exit "$rc"
fi
case "$in" in
  *"git commit"*|*"git push"*|*"gh pr"*)
    echo "[gate] 検査が起動できない(uv が無いか落ちた。rc=$rc)。commit/push/pr は止める。uv を入れて uv sync(README「使い方」)" >&2
    exit 2 ;;
  *)
    exit 0 ;;
esac
