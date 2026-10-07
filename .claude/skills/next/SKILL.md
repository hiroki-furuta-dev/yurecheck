---
name: next
description: 今どの段階にいて、その段階で終えることは何かを出す。引数 all で全体の俯瞰(Milestone ごとの進み、open の PR、直近の nightly)。「次は何をすればいい」「今どこ」「全体どう」で発動する。
---

# /next

1. 引数に `all` があれば `uv run tools/status.py --all`、無ければ `uv run tools/status.py` を実行する。
2. 出力をそのまま見せる。編集しない。
3. 出力の「残り」のうち最初の1つについて、具体的なコマンドか作業を1〜2行で添える。
4. 利用者が規則の解釈を聞いたら(「これは Issue にすべきか」「環境か開発か」「メンテナが書くファイルか」)、docs/ops/WORKFLOW.md と docs/OWNER_WRITTEN.md を根拠に答える。根拠が無い問いは「WORKFLOW.md に無い。メンテナが決めること」と言う。
