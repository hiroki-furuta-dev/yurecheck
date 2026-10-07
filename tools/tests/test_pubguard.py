"""公開前の検査(guardlib.scan)のテスト。commit/push のゲートと git の pre-commit が同じ関数を使う。"""
import os
import sys

from conftest import REPO

sys.path.insert(0, os.path.join(REPO, "tools"))
import guardlib  # noqa: E402


def scan_status(repo):
    return guardlib.scan(str(repo), guardlib.changed_files(str(repo), "status"))


def test_secret_is_hard(tmp_repo):
    (tmp_repo / "Assets").mkdir()
    (tmp_repo / "Assets" / "cfg.json").write_text('{"token": "ghp_abcdefghijklmnopqrstuvwxyz012345"}', encoding="utf-8")
    hard, _, _ = scan_status(tmp_repo)
    assert any("秘密" in h for h in hard)


def test_big_non_lfs_file_is_hard(tmp_repo):
    with open(tmp_repo / "big.bin", "wb") as f:
        f.seek(11 * 1024 * 1024)
        f.write(b"0")
    hard, _, _ = scan_status(tmp_repo)
    assert any("LFS" in h for h in hard)


def test_motion_without_attribution_is_soft(tmp_repo):
    (tmp_repo / "motions" / "walk.fbx").write_bytes(b"0")
    hard, soft, _ = scan_status(tmp_repo)
    assert not hard and any("ATTRIBUTION" in s for s in soft)


def test_clean_tree_is_silent(tmp_repo):
    assert scan_status(tmp_repo) == ([], [], [])
