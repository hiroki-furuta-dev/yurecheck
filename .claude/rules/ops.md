---
paths:
  - ".github/**"
  - ".claude/**"
  - "tools/**"
  - "docs/ops/**"
---

# 環境の決まり

- workflow の trigger は push、schedule、workflow_dispatch だけ。pull_request と pull_request_target は書かない(公開リポジトリで self-hosted runner を fork から守るため。docs/ops/runner.md)。
- hooks と tools は Python の標準ライブラリだけで書き、Windows と Linux の両方で動くようにする。`uv run` で呼ぶ(pyproject.toml、.python-version)。lint は ruff、テストは pytest(tools/tests/。一時の git リポジトリで完結し、本番に触れない)。tools を変えたら `uv run pytest` を通す。
- docstring に使い方、呼び出し元、設計の参照先を書く。
- 環境の資産を足したり変えたりしたら docs/ops/registry.md に1行足す(何を、なぜ)。
- settings の deny は .claude/role_paths.json と同じ内容を保つ。片方だけ変えない。
- 止める役は PreToolUse の2つ(ファイルの guard、commit/push のゲート)と git の pre-commit。Claude Code は起動できない hook を「非ブロック」として通す仕様なので、閉じ方を自分で決める。ファイルの guard は `… || exit 2` で、起動できなければ Write を止める(uv が無ければ最初の Write で気づく)。commit/push のゲートは commit_gate.sh が包み、検査が起動できないときは commit/push/pr だけ止めて他の Bash(doctor、git status、導入の手順)は通す(uv の導入前でも入口に届くように)。判定できたときは exit 2 と理由、通すときは exit 0。知らせるだけの hook(SessionStart、SessionEnd、PostToolUseFailure)は失敗しても開いてよい。事後に知らせるだけの hook は増やさない(取り消せない)。
- 検査の本体は tools/guardlib.py に1つ。hooks、tools/commit.py、tools/precommit.py(.githooks/pre-commit)が同じものを呼ぶ。ルートは対象ファイルか stdin の cwd から解く(公式の仕様: CLAUDE_PROJECT_DIR はセッションの開始地点のまま、cwd が worktree を追う。command の `${CLAUDE_PROJECT_DIR:-.}` は未設定のときの保険)。
- Bash 経由の変更(ruff --fix、git branch -D)はファイルツールの保護を通らないので deny に明示する。allow は読み取り専用の命令だけ。Bash の commit/push のゲートに hook の `if` は使わない(`cd x && git push` のような複合コマンドが素通りするため。1回 0.03 秒なので全 Bash で回してよい)。
- Read の deny(.env、.ssh)は Bash の cat を確実には止めない(公式も「組み込みツールだけ」と記述。変数経由で抜ける報告あり)。本線は「秘密をリポジトリの中に置かない」と commit/push 前の走査で、deny は補助。
- 環境の変更も 1 Issue = 1 PR。smoke が通ることを確かめてから merge する。
- 同じ問題が繰り返されるなら、プロンプトを足さず hook(作業後のセンサー)か型(作業前のガイド)を足す。
- permission mode は既定の auto でよい。deny と PreToolUse hook は auto でも効き、リポジトリへの push は classifier が既定で止める(メンテナが承認する)。
