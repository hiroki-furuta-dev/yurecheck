#!/usr/bin/env python3
"""役割に合ったテストを回し、results/last_test.json に {commit, passed, suites, when, summary} を書く(status.py が読む)。
  uv run tools/test.py            ops の役割は pytest、dev の役割(と未設定)は EditMode と PlayMode
  uv run tools/test.py --edit     Unity は EditMode だけ
pytest の既知の失敗は xfail(strict、raises、reason に Issue 番号)で印を付け、件数を xfailed に数える。
Unity プロジェクト(ProjectSettings/ProjectVersion.txt)が無ければ Unity を起動せず、飛ばしたことを skipped に残す。
依存: Unity を回すときは環境変数 UNITY_PATH(Unity.exe のパス)。
呼び出し元: AGENTS.md の手順 3、/next。設計: docs/ops/WORKFLOW.md。
"""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
UNITY = os.environ.get("UNITY_PATH", "")
ROLE = os.environ.get("YURECHECK_ROLE", "")


def head():
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def write_last(record):
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    record = {"commit": head(), **record, "when": datetime.now().isoformat(timespec="seconds")}
    with open(os.path.join(ROOT, "results", "last_test.json"), "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def run_pytest():
    """pytest を回し、JUnit XML から件数、既知の失敗(xfail)、失敗したテストの名前を数える。"""
    out = os.path.join(ROOT, "results", "pytest.xml")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    rc = subprocess.run([sys.executable, "-m", "pytest", "-q", f"--junitxml={out}"], cwd=ROOT).returncode
    s = {"passed": 0, "failed": 0, "xfailed": 0, "skipped": 0, "failed_tests": [], "why": ""}
    try:
        cases = ET.parse(out).getroot().iter("testcase")
    except Exception:
        s["why"] = f"XML が出なかった(終了コード {rc})"
        return False, s
    for c in cases:
        name = c.attrib.get("classname", "").replace(".", "/") + ".py::" + c.attrib.get("name", "")
        skipped = c.find("skipped")
        if c.find("failure") is not None or c.find("error") is not None:
            s["failed"] += 1
            s["failed_tests"].append(name)
        elif skipped is not None:
            s["xfailed" if skipped.attrib.get("type") == "pytest.xfail" else "skipped"] += 1
        else:
            s["passed"] += 1
    if s["passed"] + s["failed"] + s["xfailed"] == 0:
        s["why"] = "テストが0件"
    return rc == 0 and not s["why"], s


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
    try:
        rc = subprocess.run(args, cwd=ROOT).returncode
    except OSError as e:
        return False, 0, -1, f"Unity を起動できない({e.__class__.__name__})"
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
    if ROLE == "ops":
        ok, summary = run_pytest()
        write_last({"passed": ok, "suites": ["pytest"], "summary": {"pytest": summary}})
        print(json.dumps(summary, ensure_ascii=False))
        return 0 if ok else fail({"pytest": summary})
    plats = ["EditMode"] if "--edit" in sys.argv else ["EditMode", "PlayMode"]
    if not os.path.exists(os.path.join(ROOT, "ProjectSettings", "ProjectVersion.txt")):
        print("ProjectSettings/ProjectVersion.txt が無いので、Unity を起動せずに止めた(Unity プロジェクトが無い)")
        write_last({"passed": False, "skipped": "Unity プロジェクトが無い", "suites": plats})
        return 0
    if not UNITY:
        print("UNITY_PATH が未設定", file=sys.stderr)
        return 2
    ok_all = True
    summary = {}
    for p in plats:
        ok, total, failed, why = run(p)
        summary[p] = {"total": total, "failed": failed, "why": why}
        ok_all = ok_all and ok
    write_last({"passed": ok_all, "suites": plats, "summary": summary})
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if ok_all else fail(summary)


def fail(summary):
    """失敗したときだけ教訓を出す(docs/lessons/)。"""
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "lessons.py"), "--match", json.dumps(summary, ensure_ascii=False),
                    "--failure", "test"], cwd=ROOT)
    return 1


if __name__ == "__main__":
    sys.exit(main())
