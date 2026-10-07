# Yurecheck

VRM アバターの揺れもの(髪、スカート、リボン、尻尾)の設定を、モーション集に対して無人で回し、貫通・発散・ジッタ・処理時間を数字で出して合否を決める Unity の道具。設計は docs/DESIGN.md、決定の理由は docs/adr/、用語は docs/CONTEXT.md、運用は docs/ops/WORKFLOW.md。場所ごとの決まりは .claude/rules/ にあり、該当ファイルを触るときに読み込まれる。hooks と tools は Python で、`uv run` で呼ぶ(製品は Unity/C# と core/ の .NET ライブラリ。Python は開発環境の保守だけ)。初めてなら `/onboarding`。

## 役割

このリポジトリの Claude Code は2つの役割のどちらかで起動する。環境変数 YURECHECK_ROLE が役割(env か dev)。セッションの最初に役割を1行で宣言する。未設定のまま読む・調べる・答えるのはよい。ファイルを書く前には、`claude --settings .claude/settings.env.json` か `.claude/settings.dev.json` で起動し直すよう案内する(hook も止める)。

| 役割 | 目的 | 書けるもの |
|---|---|---|
| env(環境) | 開発環境を作り保守する | AGENTS.md、.claude/、.github/、tools/、Packages/manifest.json、docs/ |
| dev(開発) | 道具の機能を作る | Assets/、Tests/、docs/(ops を除く)、scenarios/、presets/、motions/ATTRIBUTION.md |

- 役割はファイルを管理する。もう一方の役割に指示は出さない。
- 開発の役割が環境を変えたいときは docs/proposals/YYYY-MM-DD-内容.md に要件だけ書く。環境の役割が次の起動で読む。
- メンテナが書くファイル(docs/OWNER_WRITTEN.md)は AI が書かない。読んで提案だけする。理由は、指標の式と判定をメンテナが自分の言葉で説明できる状態に保つため。settings の deny と Write/Edit の PreToolUse hook の両方が止める(worktree に移っても対象ファイルからルートを解く)。

## 作業の流れ

1 Issue = 1 ブランチ = 1 PR。各手順の理由は docs/ops/WORKFLOW.md。

1. Issue を選ぶ。`git worktree add ../yurecheck-<番号> -b feat/<番号>-<内容>`。main では作業しない。
2. 作業し、区切りで `uv run tools/commit.py "件名" <パス>...` でコミットする。渡したパスだけがステージされる。`git add -A` は使わない。件名は「何をしたか」。
3. `uv run tools/test.py` でテストを回す。
4. `/pr` で PR を出す。「何を変えたか、なぜ」はメンテナが書く(AI は書かない)。残り2つは差分から下書きし、食い違いを見てから gh で送る。
5. smoke が通ったら `/review-pr`。食い違いの指摘に PR のコメントで答える。
6. 食い違いに答えたら、メンテナが merge する。終わりに `/handoff`。

`/next` で「段階と残り」が出る。`/next all` は全体の俯瞰。

## 仕事の仕方

- 頼まれた範囲だけを変える。作業中に見つけた別のバグ、整理したくなるコード、将来のための抽象化は、直さずに PR の要約に「続き」として書く。要らないエラー処理や互換のための分岐は足さない。
- 小さな変更はファイルを丸ごと書き直さず、該当箇所だけを編集する。
- 進捗を報告するときは、このセッションのツールの結果で裏付けられることだけを書く。テストが失敗したら出力ごと書く。飛ばした手順はそう書く。
- テストは、作業が求める振る舞いに1つずつ、隣のテストと同じ大きさで書く。確認のための使い捨てのスクリプトはコミットしない。
- サブエージェントは「読む」「確かめる」用途が基本(探索、別の文脈での検証、レビュー)。独立した下調べは並列に投げてよい。書かせるときは、指示をそれだけで完結させ(会話を見ていない前提)、戻すのは要約と差分にし、本体が必ず読んでから採用する(自己承認しない)。
- 失敗から得た教訓(こう失敗した、こう直した)は AGENTS.md、rules、自動メモリには書かない。docs/lessons/ に1件1ファイルで置き、失敗が起きたときだけ tools/lessons.py が該当するものを出す(常に文脈に居座る失敗の教訓は性能を下げる、という 2026-10 の研究に従う)。自動メモリには好みと環境の癖だけを残し、規則の出どころにしない。
- 返事は結論から。何が起きたか、何を見つけたかを最初の1文で言い、根拠は後ろに置く。

## 公開物としての規則

- ライセンス不明の素材、10MB 超のファイル、鍵の形をした文字列、.env や鍵のファイルは入れない。止めるのは commit と push の前のゲート(Bash の PreToolUse hook と .githooks/pre-commit)。アバターは自作の VRM、モーションは CC0 と motions/ATTRIBUTION.md。
- AI が書いた部分は docs/AI_USAGE.md に PR ごとに残す。
- main は PR の merge でだけ進む。履歴は書き換えない(force push と reset --hard は deny)。
