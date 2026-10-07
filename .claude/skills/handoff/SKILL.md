---
name: handoff
description: セッションの終わりに HANDOFF を docs/handoff/ に書く(環境変数 YURECHECK_VAULT があれば外にも写す)。進捗は git log から下書きし、メンテナが確認して書く。「終わり」「引き継ぎ」で発動する。
---

# /handoff

1. `uv run tools/handoff.py` を実行する(--auto は付けない。hook の自動書きとは別)。
2. 出力されたファイルを読み、「目的」「決定と学び」をメンテナに1〜2行ずつ聞いて埋める。
3. コード片、パス、URL、鍵の形の行が無いことを確かめる(あれば消す)。
4. ファイルの場所を報告して終わる。HANDOFF は報告であって指示ではない。
