# AI の利用範囲

このリポジトリは Claude Code(2つの役割)と Codex(レビュー)を使って作っている。どの部分を AI が書き、メンテナが何を直したかを PR ごとに残す。

## 方針

- 指標の式、閾値、正規化、符号、更新順はメンテナが書く(docs/OWNER_WRITTEN.md)。
- AI が書くのは CLI、JSON、CSV、report、ビルド、CI、テストの雛形。
- 説明と差分の突き合わせ(/review-pr)で見つかった食い違いの数を残す。減っていけば内在化が進んでいる。

## モデル

役割と作業の形でモデルを使い分ける(既定は .claude/settings.*.json の model と effortLevel。メンテナが決める)。長い自律実行、設計、レビューは最上位のモデル。対話で小さく直す作業と環境の定型作業は一段下のモデル。使ったモデルは手で思い出さず、SessionEnd の hook が transcript から数えて HANDOFF に書き、PR の分担欄に写す。

## 記録

| PR | AI が書いた | メンテナが書いた・直した | 使ったモデル | 食い違い |
|---|---|---|---|---|
| #0 下書き | 環境一式(AGENTS.md、settings、hooks、skills、workflows、docs の骨) | 設計の決定、役割の分け方、名前 | 設計ノート(リポジトリの外) | - |
| #1 runner 待ちの回避 | smoke/nightly の RUNNER_READY 条件、runner.md、lessons と重複キーのテスト、PR テンプレートの最小化 | 方針(main へ直接 push しない、テンプレートを3つに)。if の重複は AI が見落とし AI が直した | claude-fable-5-1 | - |
| #4 hooks と deny の確認 | docs/proposals/ の5件(確認の結果、要件、受け入れのテストの本文)、確認の手順と使い捨てのスクリプト(コミットしていない) | 何を確かめるか、一時設定での hook の確認と /permissions の目視、提案に残すもの、PR の「何を変えたか、なぜ」 | claude-opus-5-5(27c37c5 の分は不明) | 0(/pr の突き合わせ) |
