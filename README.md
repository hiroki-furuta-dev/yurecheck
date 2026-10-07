# Yurecheck

Yurecheck は、3D アバターの揺れもの(髪、スカート、リボン、尻尾など)の設定が、動かしたときに壊れないかを自動で確かめる道具です。用意したモーションと体型の違うアバターに対して設定を回し、揺れものの挙動を数値にして、決めておいた基準で合否を出します。

形は Unity のプロジェクトと、そこからビルドしたコマンドライン用の実行ファイルです。CI のひとつのステップとして呼び、合格した設定だけを次の工程へ通す、という使い方を想定しています。

(English summary at the bottom)

## 何を解くか

揺れものの設定を自動で作る道具はすでにいくつもあります。けれども、できあがった設定が本当に大丈夫かを確かめる作業は、今も人が動画を見て判断しています。髪が体にめり込む、スカートが暴れて発散する、静止しているのに細かく震える、処理が重い。こうした問題は見れば分かりますが、モーションとアバターの組み合わせが増えるほど、見る時間が足りなくなります。

Yurecheck はこの確認を次の形に置き換えます。

1. 揺れものの頂点の動きを毎フレーム記録します。
2. 記録から、問題の種類ごとに指標を計算します(v1 は貫通の深さ、発散、ジッタ、処理時間の4つ)。
3. 指標を、利用者が決めた閾値と比べて合否にします。合否の理由と、問題が起きたフレームの画像を一緒に残します。

人の目は、閾値を決めるときと、不合格の理由を確かめるときにだけ使います。

## 入力と出力

| 入力 | 出力 |
|---|---|
| アバター(v1 は VRM 1.0) | summary.csv(シナリオごとの指標と合否) |
| モーションのクリップ(Humanoid) | frames.csv(フレームごとの値) |
| 被検体の設定(v1 は VRM SpringBone と、任意で MagicaCloth 2) | 不合格になったフレームの PNG |
| scenarios.json(どの組み合わせを回すか) | report.md(人が読む要約) |
| thresholds.json(合否の閾値) | 終了コード(0 合格、1 不合格あり、2 実行エラー) |

## 特徴

- 自動で回ります。ビルドした実行ファイルに引数を渡すだけで、エディタを開く必要はありません。
- 決定的です。固定ステップで動かすので、同じ入力からは同じ結果が出ます。結果の一致はテストで確かめています。
- 揺れもののソルバに依存しません。被検体は共通の口(ISubject)から差し替えられます。
- 指標と閾値は分かれています。何を測るかはコード、どこまで許すかは利用者の設定です。

## これから

v1 の対象は VRM と4つの指標ですが、そこに限る理由はありません。候補として考えているのは、VRM 以外の Humanoid アバター、自作のソルバ(XPBD)、指標の追加、DCC ツール側からの呼び出し、設定の自動探索、自分の Unity プロジェクトに組み込める形での配布です。順番は docs/ROADMAP.md にあります。

## 使い方

実行ファイルの使い方は M0 で書きます。

開発に参加するときは、次の順で始めてください。

1. 端末で uv を入れます(Windows は Git for Windows も)。`uv sync` で Python 側の依存が揃います。
2. `uv run tools/doctor.py` で環境を点検します。uv がまだ無ければ `python tools/doctor.py` でも動きます。
3. Claude Code を起動して `/onboarding` を実行すると、点検の結果から最初の作業までを案内します。

hooks は uv で動くので、1 を飛ばすと Claude Code の中でファイルの書き込みが止まります。これは意図した動きで、止まったら 1 に戻ってください。

## 文書

- docs/DESIGN.md 設計の全体
- docs/adr/ 決定の記録(採らなかった案と、その理由)
- docs/METRICS.md 指標の定義
- docs/ops/WORKFLOW.md 作業の流れと、各手順の理由
- docs/AI_USAGE.md どこを AI が書き、どこを人が書いたか
- docs/ops/runner.md 自分の PC を CI のランナーにする手順

## AI の利用について

このリポジトリのコードの大半は AI(Claude Code)が書いています。設計の判断、指標の式、閾値、検証の仕組みはメンテナが書き、AI が書かないファイルは docs/OWNER_WRITTEN.md に挙げてあります。PR ごとの分担は docs/AI_USAGE.md に残します。

## 限界

見た目を良くする道具ではありません。閾値は人の目で校正した値で、絶対の基準ではありません。v1 が測る貫通は体との貫通が中心で、布同士の貫通と層の間は測りません。

## License

MIT ライセンスです。アバターは自作の VRM、モーションは CC0 のものを使い、出どころは motions/ATTRIBUTION.md に書いてあります。MagicaCloth 2 は任意の依存で、そのソースは含みません。

---

## English

Yurecheck checks whether an avatar's secondary-motion setup (hair, skirts, ribbons, tails) holds up in motion. It runs the setup against a motion set and avatars of different proportions unattended, turns the behavior into metrics (v1: penetration depth, divergence, jitter, cost), and returns pass/fail against user-defined thresholds, with the failing frames rendered as images. It is a Unity project plus a command-line runner built from it, meant to be one step in CI. Fixed-step and deterministic; solver-agnostic through a common subject interface (VRM SpringBone, MagicaCloth 2 optional).
