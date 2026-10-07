#!/usr/bin/env python3
"""失敗したときだけ教訓を出す(Sentry の「失敗の知識は条件つきで露出する」を最小で)。
  uv run tools/lessons.py --match "<失敗の文言>" [--failure test|hook|ci|build|runtime|tool]
  PostToolUseFailure hook からは標準入力の JSON(ツール名、入力、エラー)を受けて同じ照合をする
docs/lessons/*.md の frontmatter(failure、keywords)と本文を失敗の文言と突き合わせ、合うものを最大 2 件返す。
無ければ何も出さない。
呼び出し元: .claude/hooks/posttoolusefailure_lessons.py、tools/test.py(失敗時)。設計: docs/lessons/README.md。
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guardlib  # noqa: E402


def load(root):
    out = []
    for p in sorted(glob.glob(os.path.join(root, "docs", "lessons", "*.md"))):
        if os.path.basename(p).startswith("README"):
            continue
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        fm, body = {}, text
        m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
        if m:
            body = m.group(2)
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    v = v.strip()
                    if v.startswith("[") and v.endswith("]"):
                        v = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
                    fm[k.strip()] = v
        out.append({"path": os.path.basename(p), "failure": fm.get("failure", ""),
                    "keywords": fm.get("keywords", []), "body": body.strip()})
    return out


def match(lessons, text, failure=None, limit=2):
    low = (text or "").lower()
    scored = []
    for les in lessons:
        if failure and les["failure"] and les["failure"] != failure:
            continue
        score = sum(1 for k in les["keywords"] if k and k.lower() in low)
        if score:
            scored.append((score, les))
    scored.sort(key=lambda x: -x[0])
    return [les for _, les in scored[:limit]]


def flatten(obj):
    if isinstance(obj, dict):
        return " ".join(flatten(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(flatten(v) for v in obj)
    return str(obj) if obj is not None else ""


def render(found):
    return "\n\n".join(f"[lesson] {les['path']}\n{les['body']}" for les in found)


def main():
    root = guardlib.find_repo_root(os.getcwd())
    args = sys.argv[1:]
    failure = args[args.index("--failure") + 1] if "--failure" in args else None
    if "--match" in args:
        text = args[args.index("--match") + 1]
        found = match(load(root), text, failure)
        if found:
            print(render(found))
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    found = match(load(root), flatten(data), failure or "tool")
    if found:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUseFailure",
                                                 "additionalContext": render(found)}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
