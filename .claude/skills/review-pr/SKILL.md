---
name: review-pr
description: 現在のブランチの PR をレビューする。Codex の adversarial review を回し、「説明と差分の突き合わせ」(説明にあるが diff に無い、diff にあるが説明に無い、主張を裏付けるテストの有無)を含めて PR のコメントに投稿する。段階 5 で使う。
---

# /review-pr

前提: 現在のブランチに open の PR があり、smoke が成功している(`python tools/status.py` で段階 5)。

1. `gh pr view --json number,title,body,baseRefName` で PR の本文を取り、「何を変えたか、なぜ」の欄を抜き出す。空なら止めて、メンテナに書いてもらう。
2. `git diff origin/main...HEAD` を取る。
3. レビュー役を起動する。既定は Codex CLI。焦点文は次の形:
   「対象は PR #N の差分のみ。(a) PR 本文の説明にあるが差分に無いこと、(b) 差分にあるが説明に無いこと、(c) 説明の各主張を裏付けるテストの有無、(d) 正しさの欠陥、の順に列挙する。候補として出し、確定は人が行う。」
   Codex が使えないときは、Claude のサブエージェント(読み取り専用)に同じ焦点文で回し、その旨を結果に書く。
4. 結果を PR のコメントとして投稿する: `gh pr comment N --body-file <結果>`。本文の先頭は `[review-pr]`(status.py がこの印で「レビュー済み」を見る)。末尾にレビュー役の種類とセッション ID(再開できるもの)を書く。
5. メンテナに、食い違いごとに「説明を直す」か「理解を直す」かを決めてもらう。メンテナの返事は PR のコメントに書く。次回の `/review-pr` は PR のコメント欄を先に読む。
6. 食い違いの件数を docs/AI_USAGE.md の当該 PR の行に残す(任意)。
