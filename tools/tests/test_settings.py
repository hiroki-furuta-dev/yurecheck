"""settings*.json が Claude Code の型どおりか(docs/lessons/2026-10-09-settings-attribution-type.md)。
型が違うとファイルごと読み飛ばされ、deny も hooks も効かなくなる。"""

import json
import os

from conftest import REPO

FILES = (".claude/settings.json", ".claude/settings.env.json", ".claude/settings.dev.json")


def _load(name):
    return json.load(open(os.path.join(REPO, name), encoding="utf-8"))


def test_attribution_commit_and_pr_are_strings():
    for name in FILES:
        attr = _load(name).get("attribution")
        if attr is None:
            continue
        for k in ("commit", "pr"):
            if k in attr:
                assert isinstance(attr[k], str), (name, k, attr[k])
        if "sessionUrl" in attr:
            assert isinstance(attr["sessionUrl"], bool), (name, attr["sessionUrl"])


def test_settings_json_is_valid_and_has_hooks():
    d = _load(".claude/settings.json")
    assert "hooks" in d and "permissions" in d
    for name in FILES:
        _load(name)  # JSON として読めること
