import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))


@pytest.fixture
def tmp_repo(tmp_path):
    """小さな git リポジトリに tools/ と .claude/ を写し、本番に触れずに試す(雛形 5)。"""
    for d in ("tools", ".claude", "docs", ".githooks"):
        shutil.copytree(os.path.join(REPO, d), tmp_path / d, ignore=shutil.ignore_patterns("tests", "__pycache__", "handoff", "lessons"))
    (tmp_path / "docs" / "handoff").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "proposals" / "done").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "motions").mkdir(exist_ok=True)
    (tmp_path / "motions" / "ATTRIBUTION.md").write_text("# x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md", "motions/ATTRIBUTION.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    return tmp_path


def run_hook(tmp_repo, script, payload, role):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_repo), "YURECHECK_ROLE": role}
    return subprocess.run([sys.executable, str(tmp_repo / script)], input=json.dumps(payload), capture_output=True,
                          text=True, env=env, cwd=tmp_repo)


def run_tool(tmp_repo, script, args, role="dev", extra_env=None):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_repo), "YURECHECK_ROLE": role, **(extra_env or {})}
    return subprocess.run([sys.executable, str(tmp_repo / script), *args], capture_output=True, text=True, env=env, cwd=tmp_repo)


def git(tmp_repo, *args):
    return subprocess.run(["git", *args], cwd=tmp_repo, capture_output=True, text=True)


def commit_file(tmp_repo, name, content="x\n", msg="add"):
    (tmp_repo / name).parent.mkdir(parents=True, exist_ok=True)
    (tmp_repo / name).write_text(content, encoding="utf-8")
    git(tmp_repo, "add", name)
    git(tmp_repo, "commit", "-q", "-m", msg)
