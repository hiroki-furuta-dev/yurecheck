---
failure: ci
keywords: [workflow, if, duplicate, "読めなかった", yaml, "actions/runs", ".github/workflows"]
---
# workflow の job に `if:` を足したら既存の `if:` と重複し、GitHub が workflow を読めなかった
Actions の run 名がファイル名(.github/workflows/smoke.yml)になり jobs が 0 件なら、YAML の構文エラー。原因は同じ job に `if:` が2行あったこと。手元の PyYAML は重複キーを黙って通すので検出できない。直し方は条件を `&&` で1つの `if:` にまとめる。再発は tools/tests/test_workflows.py(同じ親の下の重複キー)が止める。
