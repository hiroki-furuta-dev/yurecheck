---
status: accepted (2026-10-07 メンテナの了解)
---
# 揺れにくい中核は .NET Standard 2.1 のクラスライブラリとして別にビルドする

Unity 6 の C# は 9.0 だが、Unity は .NET Standard 2.1 を既定の API 互換レベルとし、.NET Standard を対象にしたマネージドプラグイン(DLL)を両方の互換レベルで受け付ける。そこで、処理が揺れにくい中核(単位の型、境界の parse、FrameMetrics、Judge、指標の CPU 参照実装)を Yurecheck.Core として .NET SDK で別にビルドし(LangVersion は最新、PolySharp で record・init・required・nullable 属性を下位互換で生成)、Unity 側は DLL を参照して薄い適合層(SkinnedMeshRenderer の頂点の読み出し、SDF の焼き込み、Burst のジョブ、被検体)だけを C# 9 で書く。

理由は3つ。中核を現代の C# で書け、型で縛る手段(record、required、閉じた階層)がそのまま使える。中核のテストを dotnet test で GitHub-hosted の runner で回せる(Unity も GPU も要らない)。Roslyn アナライザ(BannedApiAnalyzers、nullable のエラー化)が NuGet で素直に入る。

Considered Options: Unity 内で polyfill を入れて -langversion を上げる(xpTURN/Polyfill 等。動くが公式は非対応と明記)、Unity の C# 9 に合わせて readonly struct と interface だけで書く(docs/adr/0017。適合層はこれで書く)、中核も Unity に置いて Unity Test Framework だけで試す(GPU の無い CI で中核のテストが回らない)。

Consequences: ビルドが2系統になる(dotnet と Unity)。DLL は post-build で Assets/Plugins/Yurecheck.Core.dll に写し、CI が同じことをする(写し忘れを防ぐ)。実行時の支えが要る機能(static abstract メンバー、既定インターフェイス実装)は中核で使わない。Unity 側の C# 9 からは init や required の構文は書けないので、中核の型はコンストラクタで作れるようにしておく。Burst とジョブは中核に置けないので、高速版は Unity 側に書き、中核の参照実装との一致をテストにする(設計 6b の「CPU 参照実装が正解」と同じ)。デバッグは portable pdb を一緒に置く。IL2CPP で動くかは M1 で1回確かめる。

出典: Unity Manual「.NET profile support」(互換レベルと DLL の対応表)、「Managed plug-ins」(「コンパイラは試してから使う」)、PolySharp README(runtime 非依存の機能だけを生成。static abstract は不可)。メンテナが読んだ事例の出典は未特定。
