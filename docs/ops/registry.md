# 運用の資産の台帳

運用の役割が足したり変えたりしたら1行足す(何を、なぜ)。生成できる一覧は作らず、方針と履歴だけを手で書く。

| 資産 | 用途 | 更新 |
|---|---|---|
| AGENTS.md | 役割、流れ、仕事の仕方、公開の規則 | 2026-10-07 初版。Claude 5 世代の指針で「仕事の仕方」を追加 |
| .claude/rules/*.md | 場所ごとの決まり(メンテナが書くファイル、Unity、環境、ADR) | 2026-10-07 初版 |
| .claude/settings*.json | 共通の allow/deny と hooks、役割ごとの env と deny | 2026-10-07 初版。allow は読み取り専用だけに絞った(雛形 1) |
| .claude/role_paths.json | hook が参照する役割の範囲(ops_only、dev_only)とメンテナが書くファイル | 2026-10-07 初版。2026-10-17 env_only を ops_only にし dev_only を足した(Issue #3) |
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
| tools/status.py | 段階の番号をやめ、済・未の一覧(作業、手元の変更、テスト、push、PR、説明、CI、レビュー)と次にやることを出す。ops と dev で同じ一覧 | 2026-10-17 変更(Issue #3。当時の env では Issue のブランチでも「作業は無い」と出ていた) |
| tools/test.py | ops は pytest、dev は Unity を回す。Unity プロジェクトが無ければ起動せずに飛ばす。既知の失敗は xfail(strict、raises、reason に Issue か提案) | 2026-10-17 変更(Issue #3) |
| (削除) tools/handoff.py、/handoff、SessionEnd の hook、docs/handoff/ | 2026-10-17 削除(Issue #3)。merge の後に書く HANDOFF を入れるブランチが無かった。中身は PR 本文と重なる。worktree に置いた分は worktree と一緒に消えた |
| tools/models.py | transcript から使ったモデルを数え、PR の分担欄に写す1行を出す | 2026-10-17 追加(Issue #3。handoff.py から移した) |
| .claude/rules/ops.md の pull_request | 禁止を self-hosted の workflow に限った。tools.yml(GitHub-hosted)と食い違っていた | 2026-10-17 変更(Issue #3) |
| 役割の名前 env → ops(運用) | settings.env.json を settings.ops.json に、role_paths.json の env_only を ops_only にし、dev_only を足した。文言も「環境の役割」から「運用の役割」へ。docs/adr/0015 は決めた時点の記録なので書き換えず、改名はここに残す | 2026-10-17 変更(Issue #3) |
| tools/commit.py | `--all`(もう一方の役割とメンテナのファイルが混ざれば止める)、削除と移動のパス、git mv/git rm で既にステージ済みの旧パスを git add に渡さない | 2026-10-17 変更(Issue #3。git mv/git rm の後は旧パスが pathspec で落ちていた) |
| (退役) docs/proposals/ | 2026-10-17 削除(Issue #3)。要望は「要望」の Issue にした。一覧と label で拾え、受けた作業の PR から参照できる。残っていた3件は Issue #5、#6、#7 に移し(#5 と #7 のメンテナが書くファイルの部分は保留)、windows-pytest は Issue #3 で解決した |
| .github/ISSUE_TEMPLATE/ | task.yml(結果、完了の条件、含まないもの、役割、Milestone)、request.yml(要望: 要件、なぜ、再現)、config.yml(白紙の Issue を切る)。label は ops、dev、要望 | 2026-10-17 変更(Issue #3。task.md を forms にし、proposals の受け皿を足した) |
| tools/tests/ の Windows 対応 | commit_gate.sh のテストは sh を PATH から探す(無ければ理由つきで skip)。偽の Unity は Windows では .cmd にした。2件の xfail を外し、`uv run pytest` が Windows で全部通る | 2026-10-17 変更(Issue #3。提案 windows-pytest。手元で2件の失敗が普通になっていた) |
| .claude/settings.json の Read の deny | `~/.claude/**` を `~/.claude/.credentials.json` と `~/.claude/settings.json` に絞った | 2026-10-17 変更(Issue #3。大きなツールの出力が ~/.claude/projects/ に退避され、Read で読めなかった) |
| push | AI が打つ。auto mode の判定が止めたらメンテナが承認する(/pr の手順 1 と 6、WORKFLOW.md) | 2026-10-17 変更(Issue #3。同日の 0787bd8 で「メンテナが打つ」にしたのを戻した) |
| (削除) tools/guardlib.py の clean_lines と PATHLIKE | 2026-10-17 削除(Issue #3)。HANDOFF の行のフィルタで、HANDOFF の撤去後は呼び出し元がテストだけになっていた |
