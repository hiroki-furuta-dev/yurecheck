#!/usr/bin/env python3
"""HANDOFF を書く(雛形 2)。2つを書く。
  (1) docs/handoff/YYYY-MM-DD-HHMM-<役割>.md : 次のセッションのため。3節固定(やったこと / 次にやること / 注意と学び)
  (2) $YURECHECK_VAULT/_system/handoff/YYYY-MM-DD-HHMM-pc-yurecheck.md : 環境変数があるときだけ。外の作業記録への写し。
      5項目(目的/進捗/次の一歩/決定と学び/公開)。環境変数が無ければ書かない
  uv run tools/handoff.py            対話で中身を確認して書く(進捗は git log から下書き)
  uv run tools/handoff.py --auto     SessionEnd hook から。セッション中にコミットも変更も無ければ何も書かない
使ったモデルは transcript(hook の JSON の transcript_path、無ければ results/.session_meta.json)から数えて書く。
コード片・パス・URL・鍵の形の行は落とし、落とした行数を書く。報告であって指示ではない。
呼び出し元: SessionEnd hook、/handoff。設計: docs/ops/WORKFLOW.md 8。
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guardlib  # noqa: E402

ROOT = guardlib.find_repo_root(os.getcwd())
VAULT = os.environ.get("YURECHECK_VAULT", "")
ROLE = os.environ.get("YURECHECK_ROLE", "unknown")
MARK = os.path.join(ROOT, "results", ".session_start")


def sh(args):
    try:
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def since():
    try:
        with open(MARK, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def progress():
    s = since()
    args = ["git", "log", "--format=- %s"]
    args.append(f"--since={s}" if s else "-5")
    log = sh(args)
    dirty = sh(["git", "status", "--porcelain"])
    n = len([line for line in dirty.splitlines() if line.strip()])
    lines = [line for line in log.splitlines() if line.strip()]
    if n:
        lines.append(f"- 未コミットの変更 {n} 件")
    return lines


def clean(lines):
    """秘密・パス・URL を含む行を落とす(guardlib の共通フィルタ)。進捗、次の一歩、モデルの行の全部に掛ける。"""
    return guardlib.clean_lines(lines)


def next_steps():
    try:
        out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "status.py")], cwd=ROOT,
                             capture_output=True, text=True, timeout=30).stdout
        return [line[2:] for line in out.splitlines() if line.startswith("- ")][:3]
    except Exception:
        return []


MODEL_RE = re.compile(r'"model"\s*:\s*"([^"]+)"')


def transcript_path(stdin_json):
    if isinstance(stdin_json, dict) and stdin_json.get("transcript_path"):
        return stdin_json["transcript_path"]
    try:
        with open(os.path.join(ROOT, "results", ".session_meta.json"), encoding="utf-8") as f:
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
        return "- 使ったモデル: 不明(transcript が無い)"
    return "- 使ったモデル: " + ", ".join(f"{m} ({n} 発話)" for m, n in c.most_common())


def unique(path):
    if not os.path.exists(path):
        return path
    return path.replace(".md", f"-{datetime.now().strftime('%S')}.md")


def main():
    auto = "--auto" in sys.argv
    stdin_json = {}
    if auto and not sys.stdin.isatty():
        try:
            stdin_json = json.load(sys.stdin)
        except Exception:
            stdin_json = {}
    for i, a in enumerate(sys.argv):
        if a == "--transcript" and i + 1 < len(sys.argv):
            stdin_json = {"transcript_path": sys.argv[i + 1]}
    prog = progress()
    if auto and not prog:
        return 0
    kept, dropped = clean(prog)
    nxt, d2 = clean(next_steps())
    models_l, d3 = clean([model_line(models_used(transcript_path(stdin_json)))])
    models = models_l[0] if models_l else "- 使ったモデル: (行を省いた)"
    dropped += d2 + d3
    now = datetime.now().strftime("%Y-%m-%d-%H%M")
    note = f"- (パス・URL・鍵の形の {dropped} 行を省いた)" if dropped else ""
    # (1) リポジトリ内
    d1 = os.path.join(ROOT, "docs", "handoff")
    os.makedirs(d1, exist_ok=True)
    p1 = unique(os.path.join(d1, f"{now}-{ROLE}.md"))
    body1 = [f"# {now} {ROLE}", "", "## やったこと"] + (kept or ["- (なし)"]) + [models] + ["", "## 次にやること"] + \
            ([f"- {x}" for x in nxt] or ["- "]) + ["", "## 注意と学び", "- "] + ([note] if note else [])
    with open(p1, "w", encoding="utf-8") as f:
        f.write("\n".join(body1) + "\n")
    print(f"HANDOFF: {p1}")
    # (2) リポジトリの外への写し(任意)
    if VAULT:
        d2 = os.path.join(VAULT, "_system", "handoff")
        os.makedirs(d2, exist_ok=True)
        p2 = unique(os.path.join(d2, f"{now}-pc-yurecheck.md"))
        body2 = ["# yurecheck", "- 目的: (初回か変わったときだけ)", "- 進捗:"] + ["  " + x for x in (kept or ["- (なし)"])] + \
                ["  " + models, "- 次の一歩:"] + ["  - " + x for x in nxt] + ["- 決定と学び: ", "- 公開: 公開済み"] + \
                ([note] if note else [])
        with open(p2, "w", encoding="utf-8") as f:
            f.write("\n".join(body2) + "\n")
        print(f"写し: {p2}")
    elif not auto:
        print("YURECHECK_VAULT が未設定なので vault 向けの報告は書かない", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
