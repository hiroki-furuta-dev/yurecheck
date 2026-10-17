#!/usr/bin/env python3
"""済・未の一覧と残り。両方の役割が同じものを使う。
  uv run tools/status.py          Issue のブランチでの一覧(作業 → 未コミット → テスト → push → PR → 説明 → CI → レビュー)と次にやること
  uv run tools/status.py --all    全体の俯瞰(Milestone ごとの進み、open の PR、直近の nightly)
  uv run tools/status.py --hook   SessionStart から呼ばれる形(JSON の additionalContext で返す)
ルートは cwd から git のルート(worktree を含む)を解く。gh があれば Issue/PR/CI も読む(無ければ「gh 無し」)。
一覧(checklist)と次にやること(next_action)は引数だけで決まる純粋な関数で、テストから直接呼ぶ。
役割の違いはテストの行だけ(env は pytest、dev は Unity の EditMode と PlayMode)。
呼び出し元: SessionStart hook、/next。設計: docs/ops/WORKFLOW.md、docs/ops/registry.md。
"""
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guardlib  # noqa: E402

ROLE = os.environ.get("YURECHECK_ROLE", "")


def sh(args, cwd, timeout=20):
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception as e:
        return 1, str(e)


def gh_json(args, cwd):
    code, out = sh(["gh"] + args, cwd, timeout=30)
    if code != 0:
        return None
    try:
        return json.loads(out)
    except Exception:
        return None


def git_state(root):
    s = {}
    code, br = sh(["git", "symbolic-ref", "--short", "-q", "HEAD"], root)
    s["branch"] = br if code == 0 else "HEAD(detached)"
    _, porcelain = sh(["git", "status", "--porcelain"], root)
    s["dirty"] = len([line for line in porcelain.splitlines() if line.strip()])
    code, ab = sh(["git", "rev-list", "--left-right", "--count", "@{upstream}...HEAD"], root)
    parts = ab.split() if code == 0 else []
    s["ahead"] = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else None
    s["has_upstream"] = code == 0
    _, s["head"] = sh(["git", "rev-parse", "--short", "HEAD"], root)
    s["issue"] = issue_number(s["branch"])
    base = "origin/main" if sh(["git", "rev-parse", "-q", "--verify", "origin/main"], root)[0] == 0 else "main"
    code, n = sh(["git", "rev-list", "--count", f"{base}..HEAD"], root)
    s["commits"] = int(n) if code == 0 and n.isdigit() else 0
    return s


def issue_number(branch):
    """feat/<番号>-… と worktree-<番号>-… から Issue の番号を読む。"""
    m = re.match(r"(?:feat/|worktree-)(\d+)-", branch or "")
    return int(m.group(1)) if m else None


def test_state(root, head):
    try:
        with open(os.path.join(root, "results", "last_test.json"), encoding="utf-8") as f:
            t = json.load(f)
        t["fresh"] = t.get("commit") == head
        return t
    except Exception:
        return None


def proposals(root):
    todo = []
    for p in sorted(glob.glob(os.path.join(root, "docs", "proposals", "*.md"))):
        name = os.path.basename(p)
        if name.startswith("_") or os.path.exists(os.path.join(root, "docs", "proposals", "done", name)):
            continue
        todo.append(name)
    return todo


def gh_state(root, branch):
    g = {"available": sh(["gh", "--version"], root)[0] == 0}
    if not g["available"]:
        return g
    g["issues"] = gh_json(["issue", "list", "--state", "open", "--limit", "50", "--json", "number,title,milestone"], root) or []
    g["prs"] = gh_json(["pr", "list", "--state", "open", "--limit", "20", "--json",
                        "number,title,headRefName,isDraft,reviewDecision,statusCheckRollup,headRefOid,body,comments"], root) or []
    g["runs"] = gh_json(["run", "list", "--limit", "10", "--json", "name,status,conclusion,headBranch,createdAt"], root) or []
    g["my_pr"] = next((p for p in g["prs"] if p.get("headRefName") == branch), None)
    return g


def check_status(pr):
    rolls = pr.get("statusCheckRollup") or []
    if not rolls:
        return "未完"
    concl = {r.get("conclusion") or r.get("state") for r in rolls}
    if any(c in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT") for c in concl):
        return "失敗"
    if all(c in ("SUCCESS", "NEUTRAL", "SKIPPED") for c in concl):
        return "成功"
    return "未完"


def explanation_written(pr):
    """PR 本文の「何を変えたか、なぜ」をメンテナが書いたか(テンプレートの例と closes 行だけなら未記入)。"""
    body = pr.get("body") or ""
    sec, on = [], False
    for line in body.splitlines():
        if line.startswith("## "):
            on = line.startswith("## 何を変えたか")
            continue
        if on:
            sec.append(line)
    text = re.sub(r"<!--.*?-->", "", "\n".join(sec), flags=re.S)
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith(("例:", "closes #", "("))]
    return len("".join(lines)) >= 20


def reviewed_by_tool(pr):
    """/review-pr が PR のコメントを付けたか(先頭の [review-pr] で見る)。"""
    return any("[review-pr]" in (c.get("body") or "") for c in pr.get("comments") or [])


ITEMS = ("作業", "未コミット", "テスト", "push", "PR", "説明", "CI", "レビュー")
NEEDS_PR = ("説明", "CI", "レビュー")
MERGE = "食い違いに答えたら、メンテナが merge する。worktree を消す"


def test_row(t, role):
    """テストの行。env は pytest の記録、dev(と未設定)は EditMode と PlayMode か「飛ばした」の記録を求める。"""
    want = {"pytest"} if role == "env" else {"EditMode", "PlayMode"}
    plats = set((t or {}).get("platforms") or [])
    if not t or not plats & want:
        return "未実行", False
    if not t.get("fresh"):
        return "古い", False
    if t.get("skipped"):
        return f"飛ばした({t['skipped']})", True
    if not plats >= want:
        return "片方だけ", False
    if not t.get("passed"):
        whys = [v.get("why") for v in (t.get("summary") or {}).values() if isinstance(v, dict)]
        return ("0件" if "テストが0件" in whys else "失敗"), False
    xfailed = sum(v.get("xfailed", 0) for v in (t.get("summary") or {}).values() if isinstance(v, dict))
    return (f"通った(既知の失敗 {xfailed} 件)" if xfailed else "通った"), True


def checklist(s, t, g, role):
    """済・未の一覧。[(項目, 状態, 済)] を ITEMS の順で返す。済は True / False / None(まだ見ない)。純粋な関数。"""
    if not s.get("commits") and not s.get("dirty"):
        return [("作業", "未着手", False)] + [(n, "―", None) for n in ITEMS[1:]]
    g = g or {}
    pr = g.get("my_pr")
    rows = [("作業", f"コミット {s.get('commits') or 0} 件", bool(s.get("commits")))]
    rows.append(("未コミット", f"変更 {s['dirty']} 件", False) if s.get("dirty") else ("未コミット", "無し", True))
    rows.append(("テスト",) + test_row(t, role))
    if not s.get("has_upstream"):
        push = ("upstream 無し", False)
    elif s.get("ahead"):
        push = (f"未 push {s['ahead']} 件", False)
    elif pr and pr.get("headRefOid") and s.get("head") and not pr["headRefOid"].startswith(s["head"]):
        push = ("PR の head と違う", False)
    else:
        push = ("最新", True)
    rows.append(("push",) + push)
    if not g.get("available"):
        rows.append(("PR", "不明(gh 無し)", False))
    elif pr is None:
        rows.append(("PR", "無し", False))
    elif pr.get("isDraft"):
        rows.append(("PR", "draft", False))
    else:
        rows.append(("PR", f"#{pr.get('number')}", True))
    if not pr:
        return rows + [(n, "―", None) for n in NEEDS_PR]
    rows.append(("説明", "書いた", True) if explanation_written(pr) else ("説明", "空", False))
    cs = check_status(pr)
    rows.append(("CI", {"成功": "通った", "失敗": "失敗", "未完": "待ち"}[cs], cs == "成功"))
    if (pr.get("reviewDecision") or "") == "CHANGES_REQUESTED":
        rows.append(("レビュー", "変更要求", False))
    else:
        rows.append(("レビュー", "済", True) if reviewed_by_tool(pr) else ("レビュー", "無し", False))
    return rows


ACTIONS = {
    ("作業", None): "作業する。区切りで uv run tools/commit.py \"件名\" <パス>... でコミットする",
    ("未コミット", None): "uv run tools/commit.py \"件名\" <パス>... でコミットする",
    ("テスト", None): "uv run tools/test.py を最新のコミットに対して回す",
    ("push", None): "push する(メンテナが打つ)",
    ("PR", "不明(gh 無し)"): "gh を PATH に通して起動し直す(PR と CI が読めない)",
    ("PR", "draft"): "draft を外す(gh pr ready)",
    ("PR", None): "/pr で出す(「何を変えたか、なぜ」はメンテナが書く)",
    ("説明", None): "PR の「何を変えたか、なぜ」をメンテナが書く(AI は書かない。docs/OWNER_WRITTEN.md)",
    ("CI", "失敗"): "gh run view で原因を見る。環境の問題なら docs/proposals へ",
    ("CI", None): "CI の完了を待つ",
    ("レビュー", "変更要求"): "指摘に答えて直す。PR のコメントに返事を書く",
    ("レビュー", None): "/review-pr を回す。「説明と差分の突き合わせ」の指摘に答える",
}


def next_action(rows):
    """一覧のうち、まだ終わっていない最初の項目で次にやること。全部済なら merge の案内。"""
    for name, state, done in rows:
        if done is False:
            return ACTIONS.get((name, state)) or ACTIONS[(name, None)]
    return MERGE


def render(root, all_view=False):
    s = git_state(root)
    t = test_state(root, s["head"])
    g = gh_state(root, s["branch"])
    role = ROLE or "未指定(--settings で起動すること)"
    issue = f" (Issue #{s['issue']})" if s.get("issue") else ""
    lines = [f"役割: {role} / ブランチ: {s['branch']}{issue}"]
    if s["branch"] in ("main", "HEAD(detached)"):
        dirty = f"(main に未コミットの変更 {s['dirty']} 件)" if s["dirty"] else ""
        lines.append(f"Issue のブランチへ{dirty}: git worktree add ../yurecheck-<番号> -b feat/<番号>-<内容>")
    else:
        rows = checklist(s, t, g, ROLE)
        mark = {True: "済", False: "未", None: "―"}
        lines += [f"- [{mark[done]}] {name}: {state}" for name, state, done in rows]
        lines.append(f"残り: {next_action(rows)}")
    todo = proposals(root)
    if todo:
        lines.append(f"proposals: {len(todo)} 件({', '.join(todo)})")
    if not g.get("available"):
        lines.append("状態: gh 無し(Issue/PR/CI は読めない)")
    lines.append("規則: 1 PR = 1 Issue。main は PR の merge でだけ進む。メンテナが書くファイルは AI が書かない(docs/ops/WORKFLOW.md)")
    if all_view and g.get("available"):
        lines += ["", "全体:"]
        for m in sorted(gh_json(["api", "repos/{owner}/{repo}/milestones?state=all"], root) or [], key=lambda x: x.get("title", "")):
            lines.append(f"- {m.get('title')}: 閉じた {m.get('closed_issues', 0)} / 残り {m.get('open_issues', 0)}")
        for p in g.get("prs") or []:
            lines.append(f"- PR #{p['number']} {p['title']} [{p['headRefName']}] "
                         f"CI:{check_status(p)} review:{p.get('reviewDecision') or '未'}")
        for r in (g.get("runs") or [])[:3]:
            lines.append(f"- run {r.get('name')} {r.get('status')} {r.get('conclusion') or ''} ({r.get('headBranch')})")
    return "\n".join(lines)


def main():
    root = guardlib.find_repo_root(os.getcwd())
    text = render(root, "--all" in sys.argv)
    if "--hook" in sys.argv:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}, ensure_ascii=False))
    else:
        print(text)


if __name__ == "__main__":
    main()
