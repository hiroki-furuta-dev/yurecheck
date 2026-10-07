#!/usr/bin/env python3
"""EditMode と PlayMode のテストを回し、results/last_test.json に {commit, passed, when} を書く(status.py が読む)。
  python tools/test.py            両方
  python tools/test.py --edit     EditMode だけ
依存: 環境変数 UNITY_PATH(Unity.exe のパス)。
"""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
UNITY = os.environ.get("UNITY_PATH", "")


def run(platform):
    """毎回新しい XML に書く。古い XML は先に消し、終了コード・XML の存在・件数をすべて見る。"""
    out = os.path.join(ROOT, "results", f"{platform.lower()}.xml")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    args = [UNITY, "-batchmode", "-projectPath", ROOT, "-runTests", "-testPlatform", platform,
            "-testResults", out, "-logFile", os.path.join(ROOT, "results", f"{platform.lower()}.log")]
    if platform == "EditMode":
        args.insert(2, "-nographics")
    rc = subprocess.run(args, cwd=ROOT).returncode
    if not os.path.exists(out):
        return False, 0, -1, f"XML が出なかった(終了コード {rc})"
    try:
        root = ET.parse(out).getroot()
        total, failed = int(root.attrib["total"]), int(root.attrib["failed"])
    except Exception:
        return False, 0, -1, "XML を読めない"
    if total == 0:
        return False, 0, 0, "テストが0件"
    return rc == 0 and failed == 0, total, failed, ""


def main():
    if not UNITY:
        print("UNITY_PATH が未設定", file=sys.stderr)
        return 2
    plats = ["EditMode"] if "--edit" in sys.argv else ["EditMode", "PlayMode"]
    ok_all = True
    summary = {}
    for p in plats:
        ok, total, failed, why = run(p)
        summary[p] = {"total": total, "failed": failed, "why": why}
        ok_all = ok_all and ok
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    with open(os.path.join(ROOT, "results", "last_test.json"), "w", encoding="utf-8") as f:
        json.dump({"commit": commit, "passed": ok_all, "platforms": plats,
                   "when": datetime.now().isoformat(timespec="seconds"), "summary": summary}, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False))
    if not ok_all:
        # 失敗したときだけ教訓を出す(docs/lessons/)
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "lessons.py"), "--match", json.dumps(summary, ensure_ascii=False),
                        "--failure", "test"], cwd=ROOT)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
