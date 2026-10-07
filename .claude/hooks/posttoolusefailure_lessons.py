#!/usr/bin/env python3
"""PostToolUseFailure hook: ツールが失敗したときだけ、docs/lessons/ の合う教訓を additionalContext で出す。
呼び出し元: .claude/settings.json。本体は tools/lessons.py。
"""
import os
import runpy
import sys

sys.argv = [sys.argv[0]]
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools", "lessons.py"), run_name="__main__")
