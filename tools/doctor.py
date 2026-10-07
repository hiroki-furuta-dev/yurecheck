"""環境の点検(doctor)。合流した人と /onboarding が最初に走らせる。

使い方:
  uv run tools/doctor.py          表で出す
  uv run tools/doctor.py --json   JSON で出す(/onboarding が読む)
終了コード: 0 = 必須が全部 OK、1 = 必須に NG あり。
呼び出し元: .claude/skills/onboarding/SKILL.md、docs/ops/WORKFLOW.md。設計: docs/ops/WORKFLOW.md「初めてのとき」。
検査は標準ライブラリだけで行い、何も変更しない。直し方は提案するだけ。
"""

import json
import os
import re
import shutil
import subprocess
import sys

REQUIRED, RECOMMENDED, OPTIONAL = "必須", "推奨", "任意"


def _run(args, cwd=None):
    try:
        r = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=20)
        return r.returncode, (r.stdout or r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""


def _root():
    rc, out = _run(["git", "rev-parse", "--show-toplevel"])
    return out if rc == 0 else os.getcwd()


def find_git_bash(env, which):
    """Windows で hooks を動かす bash を特定する。WSL の System32\\bash.exe は使わない。戻り値は (path か None, 理由)。"""
    cand = env.get("CLAUDE_CODE_GIT_BASH_PATH", "")
    if cand:
        return (cand, "CLAUDE_CODE_GIT_BASH_PATH") if os.path.exists(cand) else (None, "CLAUDE_CODE_GIT_BASH_PATH の先が無い")
    git = which("git")
    if git:
        root = os.path.dirname(os.path.dirname(git))  # <Git>\cmd\git.exe → <Git>
        for rel in (("bin", "bash.exe"), ("usr", "bin", "bash.exe")):
            p = os.path.join(root, *rel)
            if os.path.exists(p):
                return p, "git と同じ場所"
    b = which("bash")
    if b and "system32" in b.lower():
        return None, "PATH の bash は WSL(System32)。Git for Windows の bash が要る"
    return (b, "PATH") if b else (None, "bash が無い")


def bash_sees_uv(bash):
    rc, _ = _run([bash, "-lc", "uv --version"])
    return rc == 0


def checks(root):
    """点検の一覧。各項目は dict(name, level, ok, detail, fix)。"""
    out = []

    def add(name, level, ok, detail, fix=""):
        out.append({"name": name, "level": level, "ok": bool(ok), "detail": detail, "fix": fix if not ok else ""})

    v = sys.version_info
    add("Python 3.12 以上", REQUIRED, v >= (3, 12), f"{v.major}.{v.minor}.{v.micro}", "uv が .python-version を見て入れる: uv sync")
    add("uv", REQUIRED, shutil.which("uv"), shutil.which("uv") or "無い",
        "https://docs.astral.sh/uv/ の手順で入れて uv sync(uv が無い間は python tools/doctor.py で点検できる)")
    rc, gv = _run(["git", "--version"])
    add("git", REQUIRED, rc == 0, gv or "無い", "https://git-scm.com/")
    rc, lv = _run(["git", "lfs", "version"])
    add("git lfs", REQUIRED, rc == 0, lv.split("(")[0].strip() if rc == 0 else "無い", "git lfs install(アバターと PNG は LFS)")
    rc, hp = _run(["git", "config", "--get", "core.hooksPath"], cwd=root)
    add("core.hooksPath = .githooks", REQUIRED, hp == ".githooks", hp or "未設定",
        "git config core.hooksPath .githooks(手でコミットするときの検査)")
    for f in (".claude/settings.env.json", ".claude/settings.dev.json", ".claude/role_paths.json"):
        exists = os.path.exists(os.path.join(root, f))
        add(f, REQUIRED, exists, "ある" if exists else "無い", "clone が欠けている。git status を見る")
    role = os.environ.get("YURECHECK_ROLE", "")
    add("YURECHECK_ROLE", RECOMMENDED, role in ("env", "dev"), role or "未設定",
        "claude --settings .claude/settings.env.json か .claude/settings.dev.json で起動する(settings が設定する)")
    rc, dv = _run(["dotnet", "--version"])
    add("dotnet SDK", RECOMMENDED, rc == 0, dv or "無い", "core/ を触るなら要る。https://dotnet.microsoft.com/download")
    pv = os.path.join(root, "ProjectSettings", "ProjectVersion.txt")
    if os.path.exists(pv):
        m = re.search(r"m_EditorVersion:\s*(\S+)", open(pv, encoding="utf-8").read())
        ver = m.group(1) if m else "読めない"
        add("Unity", RECOMMENDED, bool(m), ver, "Unity Hub で同じ版を入れる")
    else:
        add("Unity", OPTIONAL, True, "ProjectSettings が無い(M0 で版が決まる)")
    add("gh", OPTIONAL, shutil.which("gh"), shutil.which("gh") or "無い", "PR と Issue を端末から扱うなら https://cli.github.com/")
    if os.name == "nt":
        bash, why = find_git_bash(os.environ, shutil.which)
        ok = bool(bash) and bash_sees_uv(bash)
        add("Git Bash から uv が見える", REQUIRED, ok, (bash or "無い") + ("" if ok else f"({why})"),
            "hooks は Git Bash で動く。Git for Windows を入れ、uv を PATH に。別の bash を使わせるなら CLAUDE_CODE_GIT_BASH_PATH")
    rc, br = _run(["git", "branch", "--show-current"], cwd=root)
    add("作業ブランチ", OPTIONAL, br not in ("", "main"), br or "detached",
        "main では作業しない。git worktree add ../yurecheck-<番号> -b feat/<番号>-<内容>")
    return out


def main(argv):
    root = _root()
    res = checks(root)
    bad = [r for r in res if r["level"] == REQUIRED and not r["ok"]]
    if "--json" in argv:
        print(json.dumps({"root": root, "ok": not bad, "checks": res}, ensure_ascii=False, indent=1))
    else:
        print(f"doctor: {root}")
        for r in res:
            mark = "OK" if r["ok"] else ("NG" if r["level"] == REQUIRED else "--")
            line = f"{mark:2} [{r['level']}] {r['name']}: {r['detail']}"
            if r["fix"]:
                line += f"  → {r['fix']}"
            print(line)
        print("必須は全部 OK" if not bad else f"必須に NG が {len(bad)} 件")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
