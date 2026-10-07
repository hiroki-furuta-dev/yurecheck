---
paths:
  - "core/**/*.cs"
  - "core/**/*.csproj"
---

# 中核(core/)のコードの決まり

core/Yurecheck.Core は Unity の外でビルドする .NET のライブラリ(docs/adr/0018)。TargetFramework は netstandard2.1、LangVersion は latest、PolySharp で record・init・required・nullable の属性を補う。

- 置くもの: 単位の型(Millimeters、PermilleOfHeight)、境界の parse(ScenarioFile → Scenario、ThresholdsFile → Thresholds)、FrameMetrics、Judge、指標の CPU 参照実装。Unity に依存するもの(SkinnedMeshRenderer、SDF の焼き込み、Burst、被検体)は置かない。UnityEngine を参照しない。
- 型で縛る。record と required と init で「作れる形」を限定し、閉じた階層は private コンストラクタと静的ファクトリで表す。Verdict は Judge の中からしか作れない(internal コンストラクタ + InternalsVisibleTo はテストにだけ)。
- 実行時の支えが要る機能は使わない: static abstract メンバー、既定インターフェイス実装、Span の ref struct の一部(Unity の Mono で動かない)。PolySharp が生成できる属性と型だけ。
- Unity 側(C# 9)から使う型は、必ずコンストラクタか静的メソッドで作れるようにする(init と required の構文は Unity 側では書けない)。
- nullable はエラー(TreatWarningsAsErrors)。BannedApiAnalyzers で DateTime.Now、Random の既定、Environment への依存を禁止する(同じ入力から同じ数字、のため)。
- テストは core/Yurecheck.Core.Tests(NUnit。Unity Test Framework と同じ書き方で揃える)。`dotnet test` が GitHub-hosted の runner で回る(.github/workflows/tools.yml)。参照実装のテストの期待値はメンテナが書く(docs/OWNER_WRITTEN.md)。
- DLL と pdb は csproj の post-build target が Assets/Yurecheck/Plugins/ に写す。手で写さない。CI も同じ target を使う。
- メンテナが書くファイル(Measure/*Reference*.cs、Judge/*.cs)は AI が書かない。提案は PR のコメントか docs/proposals/ に。
- 前身の実装(docs/adr/0014)のコードと素材は写さない。知識だけを使う。
