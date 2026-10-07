# self-hosted runner(自分の PC)

## なぜ self-hosted か

Unity、GPU(D3D12)、MagicaCloth 2 が PC にしか無い。クラウドの runner は GPU が無く、Unity のライセンスの扱いも重い。

## 公開リポジトリでの安全

公開リポジトリでは、fork からの PR が self-hosted runner の上で任意のコードを走らせられる。GitHub も公開リポジトリでの self-hosted を勧めていない。次を守る。

1. workflow の trigger は push(自分のブランチ)、schedule、workflow_dispatch だけ。pull_request と pull_request_target は使わない。
2. リポジトリの Settings → Actions → "Fork pull request workflows" を「すべての外部協力者に承認が必要」にする。
3. runner は専用の Windows ユーザーで動かす。そのユーザーの環境に鍵や他のリポジトリの資格情報を置かない。
4. 外からの PR を受ける段階になったら、PR の検証はクラウドの runner(ビルドと EditMode テストだけ、GPU 無し)に分ける。

任意の強化(後回しでよい): action を commit の SHA で固定する(`gh actions-lock`)。

## 起動の形

- サービス登録ではなく、ログオンした対話セッションでプロセスとして起動する(`run.cmd`)。サービスだと D3D12 の描画と GPU 時間が取れない。
- ラベル: self-hosted, windows, yurecheck。
- 環境変数 UNITY_PATH に Unity.exe のパスを置く。
- 自動ログオン + スタートアップで run.cmd を起動する構成にすると、再起動後も戻る(手順はメンテナが決める)。

## 手順(初回)

1. GitHub の Settings → Actions → Runners → New self-hosted runner(Windows x64)の手順どおりに展開する。
2. 専用ユーザーでログオンし、`config.cmd --labels yurecheck` で登録する。
3. `run.cmd` で起動し、workflow_dispatch で smoke を1回回す。
4. results/ に CSV が出れば完了。

## 登録したら

runner が Idle で見えたら、リポジトリの Settings → Secrets and variables → Actions → Variables に `RUNNER_READY` = `true` を置く。smoke と nightly はこの変数があるときだけ走る(無い間は skipped。runner の無い状態で queued のまま 24 時間後に失敗になるのを防ぐため)。runner を止めるときは変数を消す。
