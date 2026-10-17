#!/usr/bin/env python3
"""このセッションで使ったモデルを transcript から数え、1行で出す。PR の「AI と人の分担」に写す。
  uv run tools/models.py
transcript のパスは results/.session_meta.json(SessionStart の session_mark.py が書く)から読む。
呼び出し元: /pr の手順 3。設計: docs/AI_USAGE.md。
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guardlib  # noqa: E402

MODEL_RE = re.compile(r'"model"\s*:\s*"([^"]+)"')


def transcript_path(root):
    try:
        with open(os.path.join(root, "results", ".session_meta.json"), encoding="utf-8") as f:
            return json.load(f).get("transcript_path")
    except Exception:
        return None


def models_used(path):
    """transcript の JSONL に出る model の値を数える。assistant の各発話に model が付く。"""
    c = Counter()
    if not path or not os.path.exists(path):
        return c
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                if '"role":"assistant"' in line or '"type":"assistant"' in line or '"role": "assistant"' in line:
                    for m in MODEL_RE.findall(line):
                        if m != "<synthetic>":
                            c[m] += 1
    except Exception:
        pass
    return c


def model_line(c):
    if not c:
        return "使ったモデル: 不明(transcript が無い)"
    return "使ったモデル: " + ", ".join(f"{m} ({n} 発話)" for m, n in c.most_common())


def main():
    root = guardlib.find_repo_root(os.getcwd())
    print(model_line(models_used(transcript_path(root))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
