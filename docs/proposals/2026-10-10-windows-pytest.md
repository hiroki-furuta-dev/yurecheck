# tools のテストを Windows でも通す

## 要件

`uv run pytest` を Windows のメンテナの環境で回したとき、すべてのテストが通るか、理由を出して飛ばされるようにする。今は失敗が2件あり、その2件が確かめるはずの振る舞いが、この環境では確かめられていない。

- `test_guard.py::test_commit_gate_sh_without_uv_blocks_only_commit_push` が、Windows でも commit_gate.sh の振る舞いを確かめられること。確かめるのは、uv が無いときに commit/push/pr だけを止め、他の Bash を通すことである。確かめられない環境では、失敗ではなく理由つきの skip にする。
- `test_codex_findings.py::test_test_py_does_not_reuse_old_xml` が、Windows でも「古い XML を使い回さない」ことを確かめられること。`test_test_py_zero_tests_is_not_success` も同じく偽の Unity を使っており、今は通っている。ただ、Windows で本当に偽の Unity が起動しているかは確かめていない。

## なぜ

ops.md は「hooks と tools は Windows と Linux の両方で動くようにする」と決めている。メンテナの手元は Windows だが、テストの一部は POSIX の環境を前提にしている。このため、手元で2件が失敗するのが普通の状態になっている。失敗が普通になると、本物の失敗に気づけない。

commit_gate.sh の閉じ方は、uv の導入前でも入口に届くようにするための設計である。その設計を確かめるテストが、手元では一度も通っていない。

## 再現(2026-10-10、feat/2-verify-hooks の 27c37c5、dev の役割、Windows 11、Git Bash)

`uv run pytest -q` の結果は「2 failed, 53 passed」だった。

1. `test_commit_gate_sh_without_uv_blocks_only_commit_push` は、`subprocess.run(["/bin/sh", ...])` のところで `FileNotFoundError: [WinError 2]` が出て失敗した。Windows ネイティブの Python からは `/bin/sh` というパスが見えない。テストは PATH にも `/usr/bin:/bin` を使っている。
2. `test_test_py_does_not_reuse_old_xml` では、`tools/test.py --edit` の終了コード 1 の確認は通った。その次の `results/last_test.json` を読むところで `FileNotFoundError` が出て失敗した。偽の Unity は `#!/bin/sh` で始まる `unity.sh` で、Windows で直接起動できるかは確かめていない。test.py が last_test.json を書かずに終わった理由は追っていない。

## 受け入れの条件

- Windows(Git Bash があり、uv がある環境)で `uv run pytest -q` を回したとき、失敗が0件になる。
- skip が出るなら、その理由が出力に表示される。
- Linux の CI で、今と同じテストが同じように通る。
