# 失敗の教訓(失敗したときだけ読む)

1件1ファイル。常に読み込まれる場所(AGENTS.md、rules、自動メモリ)には置かない。失敗が起きたとき、tools/lessons.py が失敗の種類と文言に合う教訓だけを出す。根拠: 失敗の教訓が常に文脈に居座ると、何も起きていないときの性能まで下がる(Stanford ACE チームの Sentry、2026-10)。

書く条件: 直したあとに同じ失敗が再発しないことを確かめてから(テストが通った、CI が通った)。直せていない教訓は書かない。

形式(frontmatter と本文 5 行以内):

```
---
failure: test | hook | ci | build | runtime | tool
keywords: [NullReference, ScenarioFile, uv run]
---
# 一行の要約
何が起きたか。何が原因だったか。どう直したか。再発を止めた型・Lint・テストがあればその名前。
```
