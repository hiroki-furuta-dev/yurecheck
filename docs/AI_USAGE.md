# AI の利用範囲

このリポジトリは Claude Code(運用と開発の2つの役割)と Codex(レビュー)を使って作っている。どの部分を AI が書き、メンテナが何を直したかを PR ごとに残す。

## 方針

- 指標の式、閾値、正規化、符号、更新順はメンテナが書く(docs/OWNER_WRITTEN.md)。
- AI が書くのは CLI、JSON、CSV、report、ビルド、CI、テストの雛形。
- 説明と差分の突き合わせ(/review-pr)で見つかった食い違いの数を残す。減っていけば内在化が進んでいる。

## モデル

役割と作業の形でモデルを使い分ける(既定は .claude/settings.*.json の model と effortLevel。メンテナが決める)。長い自律実行、設計、レビューは最上位のモデル。対話で小さく直す作業と運用の定型作業は一段下のモデル。使ったモデルは手で思い出さない。/pr が `uv run tools/models.py` で transcript から数え、PR の分担欄に写す。

## 記録

| PR | AI が書いた | メンテナが書いた・直した | 使ったモデル | 食い違い |
|---|---|---|---|---|
| #0 下書き | 環境一式(AGENTS.md、settings、hooks、skills、workflows、docs の骨) | 設計の決定、役割の分け方、名前 | 設計ノート(リポジトリの外) | - |
| #1 runner 待ちの回避 | smoke/nightly の RUNNER_READY 条件、runner.md、lessons と重複キーのテスト、PR テンプレートの最小化 | 方針(main へ直接 push しない、テンプレートを3つに)。if の重複は AI が見落とし AI が直した | claude-fable-5-1 | - |
| #4 hooks と deny の確認 | docs/proposals/ の5件(確認の結果、要件、受け入れのテストの本文)、確認の手順と使い捨てのスクリプト(コミットしていない) | 何を確かめるか、一時設定での hook の確認と /permissions の目視、提案に残すもの、PR の「何を変えたか、なぜ」 | claude-opus-5-5(27c37c5 の分は不明) | /pr の突き合わせで 0。/review-pr(Codex)の候補 6、うち 5 を直した(本文 3、提案 2)。1 は直していない(確認作業の証跡が差分に無い) |
| #8 開発環境の整備 | commit.py の git mv/git rm 対応とテスト、Issue forms とテスト、役割の改名(env→ops)と AGENTS.md・WORKFLOW.md・rules・skills・CONTEXT.md・README.md・registry の文言、docs/proposals/ から Issue #5〜#7 の本文 | 残りの作業の一覧と方針(役割の名前、push は AI、proposals の退役、Read の deny の範囲)、label と Issue を作る判断、#5 と #7 の一部の保留、PR の「何を変えたか、なぜ」 | claude-opus-5-5(18232f4〜e2a1081 は別のセッションで数えていない) | /pr の突き合わせで 3(役割の改名、要望の Issue 化、push を AI に)。説明は「など」に含めてそのまま出した |
