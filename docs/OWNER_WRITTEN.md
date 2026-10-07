# メンテナが書くファイル

ここに挙げたファイルはメンテナが書く。AI は読んで提案するだけで、書かない(.claude/role_paths.json の owner_written と hook が止める)。理由: 指標の式、閾値、正規化、符号、更新順は、自分の言葉で説明できる状態を保つ部分だから(理解の内在化7:AI活用3)。

| ファイル | 中身 |
|---|---|
| docs/METRICS.md | 4指標の定義、単位、閾値の根拠 |
| core/Yurecheck.Core/Measure/*Reference*.cs | 指標の CPU 参照実装(テストの正解)。core は .NET のライブラリ(docs/adr/0018) |
| core/Yurecheck.Core/Judge/*.cs | 閾値と合否、正規化 |
| Assets/Yurecheck/Runtime/Stepper.cs | 固定 dt の進行と更新順(Animator → Subject → Measure) |
| Assets/Yurecheck/Runtime/Sdf/Sign*.cs | 内外の符号の規則(コライダーの和) |
| scenarios/thresholds.json | 閾値の既定値 |
| PR 本文の「何を変えたか、なぜ」 | ファイルではないが同じ扱い。/pr は下書きせず、status は空なら 6 に進めない |

AI が書いてよいもの: CLI、JSON、CSV、report、BuildScript、CI、テストの雛形(期待値はメンテナ)。
