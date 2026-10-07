#!/usr/bin/env python3
"""hooks と tools が共有する検査の部品。
- find_repo_root(path): 対象ファイルか cwd から git のルート(worktree を含む)を解く。
  CLAUDE_PROJECT_DIR は開始地点のまま動かないので検査対象のルートには使わない
- load_role_paths(root, fallbacks): .claude/role_paths.json。worktree に無ければ開始地点か hook 自身のリポジトリから
- changed_files(root, mode): "status"(作業ツリーの変更)、"staged"(インデックス)、"push"(upstream より先のコミット)。
  -z で NUL 区切りを読む(日本語名、rename に対応)
- scan(root, files): 秘密の形、秘密ファイル名、LFS 外の大きなファイル、素材の置き場。
  hard(止める)、soft(注意)、unscanned(走査できなかった) を返す
- clean_lines(lines): HANDOFF 用。秘密・パス・URL を含む行を落とす
呼び出し元: .claude/hooks/*.py、tools/commit.py、tools/handoff.py、tools/precommit.py。設計: docs/ops/WORKFLOW.md、.claude/rules/ops.md。
"""
import fnmatch
import json
import os
import re
import subprocess

SECRET = re.compile(
    r"(-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}"
    r"|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|[\"']?(password|passwd|secret|api[_-]?key|token)[\"']?\s*[:=]\s*[\"']?[^\s\"',;]{8,})",
    re.I,
)
SECRET_NAMES = re.compile(r"(^|/)(\.env(\..*)?|.*\.(pem|key|p12|pfx|jks)|id_(rsa|ed25519|ecdsa)(\.pub)?|.*\.secret)$", re.I)
PATHLIKE = re.compile(r"(https?://|[A-Za-z]:[\\/]|\\\\|~/|/(home|Users|mnt|tmp|var|etc|opt|root|srv)/|/[\w.-]+/[\w.-]+\.\w+)", re.I)
LFS_EXT = {".vrm", ".fbx", ".mp4", ".png", ".unitypackage"}
ASSET_EXT = {".vrm", ".fbx", ".mp4"}
ASSET_DIRS = ("avatars/", "motions/", "docs/", "results/")
SKIP_PREFIX = (".claude/hooks/", "tools/", "docs/handoff/")
MAX_FILES = 500
MAX_TEXT = 2 * 1024 * 1024
MAX_SIZE = 10 * 1024 * 1024


def sh(args, cwd, timeout=20):
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout
    except Exception:
        return 1, ""


def find_repo_root(start=None):
    """start(ファイルかディレクトリ)から上へ .git(ディレクトリか worktree の file)を探す。無ければ git に聞く。"""
    p = os.path.abspath(start or os.getcwd())
    if os.path.isfile(p):
        p = os.path.dirname(p)
    cur = p
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    code, out = sh(["git", "rev-parse", "--show-toplevel"], cwd=p)
    if code == 0 and out.strip():
        return out.strip()
    return os.environ.get("CLAUDE_PROJECT_DIR") or p


def rel(path, root):
    try:
        return os.path.relpath(os.path.abspath(path), root).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def load_role_paths(root, fallbacks=()):
    """設定の出どころ。検査対象のルート(worktree)に無ければ、開始地点(CLAUDE_PROJECT_DIR)や hook 自身のリポジトリから読む。"""
    for base in (root, *fallbacks, os.environ.get("CLAUDE_PROJECT_DIR") or ""):
        if not base:
            continue
        try:
            with open(os.path.join(base, ".claude", "role_paths.json"), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            continue
    return None


def matches(path, globs):
    return any(fnmatch.fnmatch(path, g) for g in globs or [])


def _parse_z(out):
    """git status --porcelain -z の解析。rename は "XY new\\0old" の順で来る。"""
    files, items, i = [], out.split("\0"), 0
    while i < len(items):
        line = items[i]
        if len(line) < 3:
            i += 1
            continue
        xy, path = line[:2], line[3:]
        files.append(path)
        if xy[0] in "RC":
            i += 1  # 次の要素は rename 元
        i += 1
    return files


def changed_files(root, mode="status"):
    if mode == "staged":
        code, out = sh(["git", "diff", "--cached", "--name-only", "-z"], cwd=root)
        return [p for p in out.split("\0") if p] if code == 0 else []
    if mode == "push":
        code, out = sh(["git", "diff", "--name-only", "-z", "@{upstream}...HEAD"], cwd=root)
        if code != 0:
            code, out = sh(["git", "ls-files", "-z"], cwd=root)
        return [p for p in out.split("\0") if p] if code == 0 else []
    code, out = sh(["git", "status", "--porcelain", "-z", "--untracked-files=all"], cwd=root)
    return _parse_z(out) if code == 0 else []


def looks_text(ap, size):
    if size > MAX_TEXT:
        return False
    try:
        with open(ap, "rb") as f:
            head = f.read(4096)
        return b"\0" not in head
    except OSError:
        return False


def scan(root, files, attribution=None):
    hard, soft, unscanned = [], [], []
    if attribution is None:
        try:
            with open(os.path.join(root, "motions", "ATTRIBUTION.md"), encoding="utf-8") as f:
                attribution = f.read()
        except Exception:
            attribution = ""
    if len(files) > MAX_FILES:
        unscanned.append(f"{len(files) - MAX_FILES} 件(上限 {MAX_FILES} を超えた分)")
        files = files[:MAX_FILES]
    for rp in files:
        ap = os.path.join(root, rp)
        if not os.path.isfile(ap) or rp.startswith(SKIP_PREFIX):
            continue
        ext = os.path.splitext(rp)[1].lower()
        try:
            size = os.path.getsize(ap)
        except OSError:
            unscanned.append(rp)
            continue
        if SECRET_NAMES.search(rp):
            hard.append(f"{rp}: 秘密ファイルの名前(.env、鍵、証明書)")
            continue
        if size > MAX_SIZE and ext not in LFS_EXT:
            hard.append(f"{rp}: {size // (1024 * 1024)}MB。LFS の対象外の大きなファイル")
        if ext in ASSET_EXT:
            if not rp.startswith(ASSET_DIRS):
                soft.append(f"{rp}: 素材は avatars/ か motions/ に置く")
            if rp.startswith("motions/") and os.path.basename(rp) not in attribution:
                soft.append(f"{rp}: motions/ATTRIBUTION.md に出どころとライセンスが無い")
            continue
        if ext in LFS_EXT:
            continue
        if not looks_text(ap, size):
            if size > MAX_TEXT:
                unscanned.append(f"{rp}(テキスト走査の上限 2MB 超)")
            continue
        try:
            with open(ap, encoding="utf-8", errors="ignore") as f:
                text = f.read()
            m = SECRET.search(text)
            if m:
                hard.append(f"{rp}: 秘密の形をした文字列({m.group(0)[:16]}...)")
        except Exception:
            unscanned.append(rp)
    return hard, soft, unscanned


def clean_lines(lines):
    kept, dropped = [], 0
    for line in lines:
        if SECRET.search(line) or PATHLIKE.search(line):
            dropped += 1
        else:
            kept.append(line)
    return kept, dropped
