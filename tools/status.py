#!/usr/bin/env python3
"""段階と残り。両方の役割が同じものを使う。
  uv run tools/status.py          現在の段階と、その段階で終えること
  uv run tools/status.py --all    全体の俯瞰(Milestone ごとの進み、open の PR、直近の nightly)
  uv run tools/status.py --hook   SessionStart から呼ばれる形(JSON の additionalContext で返す)
ルートは cwd から git のルート(worktree を含む)を解く。gh があれば Issue/PR/CI も読む(無ければ「gh 無し」)。
段階の判定(stage_dev / stage_env)は引数だけで決まる純粋な関数で、テストから直接呼ぶ。
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
    m = re.search(r"(\d+)", s["branch"] or "")
    s["issue"] = int(m.group(1)) if m and s["branch"] not in ("main", "HEAD(detached)") else None
    return s


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


def latest_handoff(root):
    """docs/handoff/ の直近1枚から「やったこと」「次にやること」の行を返す(3節固定。雛形 2)。"""
    files = [f for f in sorted(glob.glob(os.path.join(root, "docs", "handoff", "*.md")))
             if not os.path.basename(f).startswith("README")]
    if not files:
        return None, []
    lines, keep = [], False
    try:
        with open(files[-1], encoding="utf-8") as f:
            for line in f:
                line = line.rstrip()
                if line.startswith("## "):
                    keep = line in ("## やったこと", "## 次にやること")
                    continue
                if keep and line.startswith("- ") and line.strip() != "-":
                    lines.append(line)
    except Exception:
        pass
    return os.path.basename(files[-1]), lines[:6]


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


def tests_ok(t):
    return bool(t) and t.get("fresh") and t.get("passed") and set(t.get("platforms") or []) >= {"EditMode", "PlayMode"}


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


def stage_dev(s, t, g):
    """開発の役割の段階。s=git_state, t=test_state, g=gh_state。純粋な関数。"""
    on_main = s["branch"] in ("main", "HEAD(detached)")
    pr = (g or {}).get("my_pr")
    if on_main and s["dirty"] == 0:
        return "0 着手前", ["Issue を1つ選ぶ(無ければ切る)", "git worktree add ../yurecheck-<番号> -b feat/<番号>-<内容>"]
    if on_main:
        return "0 着手前(main に未コミットの変更あり)", [
            "main では作業しない。変更を Issue のブランチへ移す(git stash → worktree → stash pop)"]
    if s["dirty"] > 0:
        return "1 作業中", ["区切りで uv run tools/commit.py でコミット",
                          "メンテナが書くファイルに AI が触っていないか(docs/OWNER_WRITTEN.md)"]
    if not tests_ok(t):
        why = "未実行" if not t else ("古い" if not t.get("fresh") else ("失敗" if not t.get("passed") else "片方だけ"))
        return f"2 テスト({why})", ["uv run tools/test.py で EditMode と PlayMode を最新コミットに対して回す"]
    if pr is None:
        return "3 PR 前", ["/pr で出す(確かめ方と分担は差分から下書き。『何を変えたか、なぜ』はメンテナが書く)"]
    if s.get("ahead"):
        return "3 PR 前(未 push のコミットあり)", ["push して PR を最新にする"]
    if pr.get("headRefOid") and s.get("head") and not pr["headRefOid"].startswith(s["head"]):
        return "3 PR 前(PR の head とローカルが違う)", ["push するか、ローカルを PR に合わせる"]
    if pr.get("isDraft"):
        return "3 PR 前(draft)", ["draft を外す(gh pr ready)"]
    cs = check_status(pr)
    if cs == "失敗":
        return "4 CI(失敗)", ["gh run view で原因を見る。環境の問題なら docs/proposals へ"]
    if cs == "未完":
        return "4 CI(待ち)", ["smoke の完了を待つ"]
    rd = pr.get("reviewDecision") or ""
    if rd == "CHANGES_REQUESTED":
        return "5 レビュー(変更要求)", ["指摘に答えて直す。PR のコメントに返事を書く"]
    if not explanation_written(pr):
        return "5 レビュー(説明が空)", ["PR の『何を変えたか、なぜ』をメンテナが書く(AI は書かない。docs/OWNER_WRITTEN.md)"]
    if not reviewed_by_tool(pr):
        return "5 レビュー", ["/review-pr を回す(Codex)。『説明と差分の突き合わせ』の指摘に答える"]
    return "6 merge 可", [
        "食い違いに答えたら、メンテナが merge する(gh pr merge --squash)",
        "merge 後に worktree を消し、uv run tools/handoff.py"]


def stage_env(todo, runs):
    nightly = next((r for r in (runs or []) if (r.get("name") or "").lower().startswith("nightly")), None)
    if todo:
        return "proposals 未対応", [f"docs/proposals/{n} を読んで受けるか断るか決める" for n in todo[:5]]
    if nightly and nightly.get("conclusion") == "failure":
        return "nightly 失敗", ["原因が環境か開発かを切り分ける。開発なら Issue を切る"]
    return "無し", ["環境の作業は無い。cc-dev へ"]


def render(root, all_view=False):
    s = git_state(root)
    t = test_state(root, s["head"])
    g = gh_state(root, s["branch"])
    role = ROLE or "未指定(--settings で起動すること)"
    stage, todo = stage_env(proposals(root), g.get("runs")) if ROLE == "env" else stage_dev(s, t, g)
    issue = f" (Issue #{s['issue']})" if s.get("issue") else ""
    lines = [f"役割: {role} / ブランチ: {s['branch']}{issue} / 段階: {stage}", "残り:"] + [f"- {x}" for x in todo]
    ho, ho_lines = latest_handoff(root)
    extra = []
    if s["dirty"]:
        extra.append(f"未コミット {s['dirty']} 件")
    if s.get("ahead"):
        extra.append(f"未 push {s['ahead']} コミット")
    if ho:
        extra.append(f"直近の HANDOFF: {ho}")
    if not g.get("available"):
        extra.append("gh 無し(Issue/PR/CI は読めない)")
    if extra:
        lines.append("状態: " + " / ".join(extra))
    if ho_lines:
        lines.append("前回:")
        lines += ho_lines
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
