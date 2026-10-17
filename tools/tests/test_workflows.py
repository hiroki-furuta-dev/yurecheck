"""workflow の YAML に、同じ親の下で重複するキーが無いこと(docs/lessons/2026-10-07-workflow-duplicate-if.md)。
PyYAML は重複キーを黙って通すので、字下げを見て自前で数える。"""

import glob
import os
import re

from conftest import REPO

KEY = re.compile(r"^(\s*)(- )?([A-Za-z_][\w.-]*):(\s|$)")


def duplicate_keys(text):
    """同じ親(字下げ + 直前の '- ' の区切り)の中で2回出るキーを返す。"""
    seen = {}  # (indent, seq_id) -> set(keys)
    seq_id = {}  # indent -> 連番('- ' ごとに増える)
    dups = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = KEY.match(line)
        if not m:
            continue
        indent = len(m.group(1)) + (2 if m.group(2) else 0)
        if m.group(2):
            seq_id[indent] = seq_id.get(indent, 0) + 1
        for k in [i for i in seq_id if i > indent]:
            seq_id.pop(k)
        for k in [i for i in seen if i[0] > indent]:
            seen.pop(k)
        scope = (indent, seq_id.get(indent, 0))
        keys = seen.setdefault(scope, set())
        if m.group(3) in keys:
            dups.append((indent, m.group(3)))
        keys.add(m.group(3))
    return dups


def test_workflows_have_no_duplicate_keys():
    files = glob.glob(os.path.join(REPO, ".github", "workflows", "*.yml"))
    assert files
    for f in files:
        assert duplicate_keys(open(f, encoding="utf-8").read()) == [], f


def test_duplicate_detector_catches_double_if_and_allows_steps():
    bad = "jobs:\n  a:\n    if: x\n    runs-on: y\n    if: z\n"
    assert duplicate_keys(bad) == [(4, "if")]
    ok = "jobs:\n  a:\n    steps:\n      - name: one\n        if: x\n      - name: two\n        if: y\n"
    assert duplicate_keys(ok) == []


TRIGGER_PR = re.compile(r"^\s*(-\s*)?pull_request(_target)?\s*:?\s*$|^on:.*\bpull_request", re.M)


def test_self_hosted_workflows_have_no_pull_request_trigger():
    """self-hosted の runner を使う workflow は pull_request で走らせない(.claude/rules/ops.md、docs/ops/runner.md)。"""
    self_hosted = []
    for f in glob.glob(os.path.join(REPO, ".github", "workflows", "*.yml")):
        text = open(f, encoding="utf-8").read()
        if re.search(r"^\s*runs-on:.*self-hosted", text, re.M):
            self_hosted.append(f)
            assert not TRIGGER_PR.search(text), f
    assert self_hosted


def test_pull_request_detector():
    assert TRIGGER_PR.search("on:\n  push:\n  pull_request:\n")
    assert TRIGGER_PR.search("on: [push, pull_request]\n")
    assert not TRIGGER_PR.search("on:\n  push:\n# pull_request では走らせない\n    if: github.event_name != 'pull_request'\n")


def test_issue_forms_are_task_and_request_only():
    """Issue は作業(task.yml)と要望(request.yml)のフォームだけ。白紙は切る(docs/ops/WORKFLOW.md「Issue になる前」)。"""
    d = os.path.join(REPO, ".github", "ISSUE_TEMPLATE")
    read = lambda n: open(os.path.join(d, n), encoding="utf-8").read()  # noqa: E731
    assert sorted(os.listdir(d)) == ["config.yml", "request.yml", "task.yml"]
    assert re.search(r"^blank_issues_enabled:\s*false\s*$", read("config.yml"), re.M)
    for name in ("task.yml", "request.yml"):
        assert duplicate_keys(read(name)) == [], name
    assert re.findall(r"^\s+label: (\S+)", read("task.yml"), re.M) == ["結果", "完了の条件", "含まないもの", "役割", "Milestone"]
    assert re.findall(r"^\s+label: (\S+)", read("request.yml"), re.M) == ["要件", "なぜ", "再現"]
    assert re.search(r'^labels: \["要望"\]$', read("request.yml"), re.M)
