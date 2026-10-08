---
failure: hook
keywords: [Settings Error, attribution, "Expected string", settings.json, "skipped entirely"]
---
# settings.json の attribution.commit / pr を false にしたら、ファイルごと読み飛ばされた
Claude Code は `attribution.commit` と `attribution.pr` を文字列として検証する(空文字で消す)。false を書くと「Expected string」で settings.json 全体が無効になり、deny も hooks も効かない。直し方は `"commit": "", "pr": "", "sessionUrl": false`(sessionUrl だけ真偽値。公式の settings-reference で確認)。再発は tools/tests/test_settings.py が止める。
