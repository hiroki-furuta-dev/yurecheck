#!/usr/bin/env python3
"""SessionStart hook。セッション開始時刻と transcript のパスを results/ に残す(handoff.py が使う)。
標準入力に hook の JSON(session_id, transcript_path, cwd ...)が来る。無くても動く。
呼び出し元: .claude/settings.json の SessionStart。設計: docs/ops/WORKFLOW.md 8。
"""
import json
import os
import sys
from datetime import datetime

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
with open(os.path.join(ROOT, "results", ".session_start"), "w", encoding="utf-8") as f:
    f.write(datetime.now().isoformat(timespec="seconds"))
meta = {"started": datetime.now().isoformat(timespec="seconds")}
try:
    data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    if isinstance(data, dict) and data.get("transcript_path"):
        meta["transcript_path"] = data["transcript_path"]
except Exception:
    pass
with open(os.path.join(ROOT, "results", ".session_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False)
