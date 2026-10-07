---
name: onboarding
description: このリポジトリに合流した人を、環境の点検から最初の作業まで案内する。「初めて」「合流した」「セットアップ」「何から始めれば」で発動する。
---

# /onboarding

相手は、このリポジトリを clone したばかりの共同開発者。説明はですます調で、1回の返事に1つの段階だけを進め、相手の答えを待ってから次へ行く。全部を一度に出さない。

## 0 前提

uv が無いと hooks が動かず、ファイルの書き込みが止まる(意図した動き)。最初に `uv --version` を確かめ、無ければ README「使い方」の 1 を案内して、入るまで先へ進まない。点検だけは `python tools/doctor.py` でもできる。

## 1 点検

`uv run tools/doctor.py` を実行し、出力の表をそのまま見せる。NG があれば「→」の直し方を1つずつ提案する。実行してよいのは、設定だけで済むもの(`git config core.hooksPath .githooks`、`uv sync`)で、相手の了解を得てから。インストールが要るもの(uv、git lfs、dotnet、Unity、Git for Windows)は URL を示して相手に任せ、入ったら doctor をもう一度走らせる。

## 2 何をしたいかを聞く

質問は2つまで。

- 環境(hooks、CI、tools)を直したいのか、道具の機能を作りたいのか。前者は env、後者は dev の役割。
- OS は Windows か。

答えに合わせて、起動コマンドを1行で示す(`claude --settings .claude/settings.env.json` か `.claude/settings.dev.json`)。

## 3 知っておくこと

次の5つを、相手の役割に関わる順に、各2〜3文で話す。根拠の文書を読んでから話し、文書に無いことは言わない。

1. 何を作っているか(README の最初の2段落)。
2. 2つの役割と、役割ごとに書けるもの(AGENTS.md「役割」)。
3. 1 Issue = 1 ブランチ = 1 PR。コミットは `uv run tools/commit.py "件名" <パス>...`、テストは `uv run tools/test.py`(docs/ops/WORKFLOW.md。各手順の「なぜ」も一言添える)。
4. AI が書かないファイルと、その理由(docs/OWNER_WRITTEN.md)。
5. `/pr`(差分から説明を下書きし、言い直しを受けて出す)、`/next`(段階と残り)、`/review-pr`、`/handoff`。

## 4 最初の作業

open の Issue を出す(`gh issue list`。gh が無ければ GitHub の Issues の URL を示す)。相手が選んだ Issue で `git worktree add ../yurecheck-<番号> -b feat/<番号>-<内容>` を実行し、その worktree で `/next` を走らせて「段階と残り」を見せる。Issue が無ければ、docs/ROADMAP.md の現在の Milestone から1つ提案する。

## 5 終わり

相手専用のチェックリスト(済んだこと、残っていること、次に読む文書)を 10 行以内で出して終わる。

## 注意

- CLAUDE.local.md を作ると AGENTS.md が読まれなくなる(Claude Code の既定)。作るなら /config の Project instructions を claude-md-and-agents-md にするよう伝える。
- Windows の hooks は Git Bash で動く。doctor が bash の有無を見る。
- 分からないことは推測で答えず、「WORKFLOW.md に無いので、メンテナに聞いてください」と言い、Issue にその質問を書いてよい。
