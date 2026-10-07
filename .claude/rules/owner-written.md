---
paths:
  - "docs/METRICS.md"
  - "docs/OWNER_WRITTEN.md"
  - "Assets/Yurecheck/Runtime/Measure/*Reference*.cs"
  - "Assets/Yurecheck/Runtime/Judge/**"
  - "Assets/Yurecheck/Runtime/Stepper.cs"
  - "Assets/Yurecheck/Runtime/Sdf/Sign*.cs"
  - "scenarios/thresholds.json"
---

# メンテナが書くファイル

このファイルはメンテナが書く。AI は読んで、指摘と提案を PR のコメントか docs/proposals/ に書く。直接は書かない(hook が止める)。理由: 指標の式、閾値、正規化、符号の規則、更新順は、メンテナが自分の言葉で説明できる状態を保つ部分だから。メンテナが「ここを書いて」と明示したときだけ、その範囲を書き、PR の分担欄に AI が書いたと残す。
