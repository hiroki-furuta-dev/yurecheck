#!/usr/bin/env python3
"""決定性の検査。ランナーは SpringBone のシナリオを2回回し、frames_<scenario>_r1.csv と _r2.csv を書く。
両方の md5 が一致すれば合格。不一致があれば exit 1。
  python tools/determinism.py results/smoke
"""
import glob
import hashlib
import os
import sys


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    """r1 が1つも無い、r2 が欠けている、空のファイル、md5 の不一致、のどれかで exit 1。"""
    d = sys.argv[1] if len(sys.argv) > 1 else "results/smoke"
    expect = int(sys.argv[sys.argv.index("--expect") + 1]) if "--expect" in sys.argv else 1
    bad, n = [], 0
    for r1 in sorted(glob.glob(os.path.join(d, "frames_*_r1.csv"))):
        name = os.path.basename(r1).replace("_r1.csv", "")
        r2 = r1.replace("_r1.csv", "_r2.csv")
        if not os.path.exists(r2):
            bad.append(f"{name}: r2 が無い")
            continue
        if os.path.getsize(r1) == 0 or os.path.getsize(r2) == 0:
            bad.append(f"{name}: 空のファイル")
            continue
        n += 1
        if md5(r1) != md5(r2):
            bad.append(f"{name}: md5 不一致")
    if n < expect:
        bad.append(f"組が足りない({n} < {expect})")
    print(f"determinism: {n} pairs, {len(bad)} problems")
    for b in bad:
        print(f"- {b}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
