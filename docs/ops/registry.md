# 環境の資産の台帳

環境の役割が足したり変えたりしたら1行足す(何を、なぜ)。生成できる一覧は作らず、方針と履歴だけを手で書く。

| 資産 | 用途 | 更新 |
|---|---|---|
| AGENTS.md | 役割、流れ、仕事の仕方、公開の規則 | 2026-10-07 初版。Claude 5 世代の指針で「仕事の仕方」を追加 |
| .claude/rules/*.md | 場所ごとの決まり(メンテナが書くファイル、Unity、環境、ADR) | 2026-10-07 初版 |
| .claude/settings*.json | 共通の allow/deny と hooks、役割ごとの env と deny | 2026-10-07 初版。allow は読み取り専用だけに絞った(雛形 1) |
| .claude/role_paths.json | hook が参照する環境の範囲とメンテナが書くファイル | 2026-10-07 初版 |
| .claude/hooks/pretooluse_guard.py | deny の保険。役割とメンテナファイルで Write/Edit を止める | 2026-10-07 初版 |
| tools/status.py | 段階と残り、全体の俯瞰、直近の HANDOFF | 2026-10-07 初版 |
| tools/commit.py | 渡したパスだけをステージしてコミット | 2026-10-07 初版(雛形 4) |
| tools/handoff.py | リポジトリ内の HANDOFF(3節)。環境変数があれば外の作業記録にも写す | 2026-10-07 初版(雛形 2) |
| tools/test.py | Unity のテストを回して results/last_test.json | 2026-10-07 初版 |
| tools/determinism.py | r1 と r2 の md5 一致 | 2026-10-07 初版 |
| tools/tests/ | hooks と tools の pytest(一時 git リポジトリ) | 2026-10-07 初版(雛形 5) |
| pyproject.toml / .python-version | uv の設定。ruff と pytest | 2026-10-07 初版 |
| .github/workflows/tools.yml | GitHub-hosted で ruff と pytest | 2026-10-07 初版 |
| .github/workflows/smoke.yml | self-hosted で Unity のテスト、ビルド、最小シナリオ | 2026-10-07 初版 |
| .github/workflows/nightly.yml | self-hosted で full | 2026-10-07 初版 |
| .github/PULL_REQUEST_TEMPLATE.md | 3つだけ(何を・なぜ、確かめ方、分担)と例文。任意の自問は置かない(任意の規則は効かない) | 2026-10-07 初版、2026-10-08 最小化(初回の PR で手が止まった) |
| docs/ops/WORKFLOW.md | 作業の流れと理由、効いているかの確認 | 2026-10-07 初版 |
| docs/ops/runner.md | self-hosted runner の安全と起動 | 2026-10-07 初版 |
| docs/adr/0016 | 計測と判定の分離 | 2026-10-07 追加(設計とアーキテクチャの概念設計の原則から) |
| tools/guardlib.py | 検査の共通部品(ルート解決、-z の解析、秘密と素材の走査、HANDOFF のフィルタ) | 2026-10-07 追加(Codex の指摘 1,2,3,7,8 から) |
| .claude/hooks/pretooluse_commit_gate.py | Bash の commit/push/pr の前に staged か push 範囲を検査して止める | 2026-10-07 追加(Codex の指摘 1) |
| .githooks/pre-commit, tools/precommit.py | 手でコミットするときの同じ検査。core.hooksPath で有効化 | 2026-10-07 追加 |
| tools/tests/test_codex_findings.py | Codex の指摘12件の回帰テスト | 2026-10-07 追加 |
| (削除) PostToolUse の pubguard、tools/lint.py | 2026-10-07 削除。止められない事後通知と、auto モードでは要らない固定口。検査は guardlib と commit/push のゲートに一本化 |
| docs/adr/0017 | C# 9 の制約と asmdef の層 | 2026-10-07 追加(型と構造の調査から) |
| docs/lessons/, tools/lessons.py, PostToolUseFailure hook | 失敗の教訓を文脈の外に置き、失敗時だけ出す | 2026-10-07 追加(Sentry の研究から) |
| docs/adr/0018, .claude/rules/core-code.md | 中核を .NET Standard 2.1 のライブラリに。メンテナが書く Judge と参照実装は core/ へ | 2026-10-07 追加、同日 メンテナが採用 |
| .claude/settings.json の PreToolUse | 2つのゲートの command を `|| exit 2` で閉じる側に | 2026-10-07 変更(公式の仕様: 起動できない hook は非ブロックで通る) |
| .claude/rules/docs-ja.md | 人が読む文書の文体(README、docs/)。AI 向けの簡潔文と分ける | 2026-10-07 追加(メンテナの指摘) |
| AGENTS.md(旧 CLAUDE.md) | Claude Code は v2.1.277 以降 AGENTS.md を直接読む。汎用の名前に変え、公開リポジトリに要らない節(外との接点、第三者の文字列)を外した | 2026-10-07 変更(メンテナの指示) |
| .claude/hooks/commit_gate.sh | Bash のゲートの包み。検査が起動できないとき commit/push/pr だけ止める | 2026-10-07 追加(Codex 2回目の指摘) |
| tools/doctor.py, .claude/skills/onboarding | 合流した人の環境の点検と案内。何も変更せず、直し方を提案する | 2026-10-07 追加(メンテナの指示) |
| .claude/skills/pr | PR の説明を差分から下書きし、言い直しを受け、食い違いを直してから gh で出す。AI_USAGE の行も足す | 2026-10-08 追加(メンテナの提案) |
| tools/status.py の段階 6 | APPROVED 待ちを廃止(作者は自分の PR を承認できず、1人では到達不能だった)。説明をメンテナが書いた + [review-pr] のコメント、に変更 | 2026-10-08 変更(メンテナの問い) |
