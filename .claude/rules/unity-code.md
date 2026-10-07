---
paths:
  - "Assets/**/*.cs"
  - "Assets/**/*.compute"
  - "Assets/**/*.hlsl"
---

# Unity のコードの決まり

- 規則は型と構造に持たせる。深さの mm と身長の千分率は別の型(readonly struct と private コンストラクタ、変換は PermilleOfHeight.From だけ)。閾値は正規化した型だけを受け取り、thresholds.json は境界で1回だけ parse する。FrameMetrics(事実)は生成後に変更できず、Verdict(方針)は Judge だけが作る。段階は interface の型状態で表す(IConfiguredRun → IWarmedRun → IMeasuredRun → IReport)。
- Unity 6 は C# 9。record、init、required は使えない。readonly struct、private コンストラクタ、interface で代替する(docs/adr/0017)。中核は Yurecheck.Core のライブラリ(core/、最新の C#、docs/adr/0018)に置き、Unity 側に書くのは適合層だけ。中核の型は DLL から使う(構文ではなくコンストラクタで作る)。中核の規則は .claude/rules/core-code.md。
- アセンブリは Metrics ← Judge ← Output の一方向(asmdef の参照)。MagicaCloth 2 の `#if MAGICACLOTH2` は Subjects.MC2 の asmdef(defineConstraints)の中だけに置く。
- 固定ステップ。Time.captureDeltaTime を使い、deltaTime を自分で計算しない。処理時間は Stopwatch と FrameTimingManager で別に測る。
- 更新順は Animator → ISubject.Step → Measure。この順を変える変更は Stepper.cs(メンテナが書く)に限る。
- 継承で振る舞いを分けない。合成と注入(ISubject の差し替え、計測器の差し替え)で分ける。
- 被検体は ISubject を実装する。MagicaCloth 2 に触るコードは `#if MAGICACLOTH2` の中に置き、無くてもビルドが通る。
- 判定対象の頂点は SpringBone の関節のウェイトで決める。材質名やボーン名の決め打ちを書かない。
- 計測の式は CPU の参照実装が正解。compute 版を書くときは参照実装との一致(誤差 1e-4)をテストにする。
- 他者のライブラリ(UniVRM、VFX Graph)は別アセンブリから参照し、自作コードと混ぜない。
- 用語は docs/CONTEXT.md の語を使う。設計の指示は具体の制約で書き、「責務」「DDD」「DRY」のような語で指示しない(語が先に出ると判断が語に引きずられる)。
- テストは Unity Test Framework。EditMode は合成データ、PlayMode は最小シナリオ。
- 前身の実装(docs/adr/0014)のコードと素材は写さない。知識だけを使う。
