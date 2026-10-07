# CI は自 PC の self-hosted runner。pull_request では走らせない

GPU と Unity のライセンスが PC にある。公開リポジトリでは fork からの PR が self-hosted runner の上で任意のコードを走らせられるので、workflow の trigger は push(自分のブランチ)、schedule、workflow_dispatch だけにし、pull_request と pull_request_target は使わない。runner は専用の Windows ユーザーで、対話セッションのプロセスとして起動する(サービスだと D3D12 の描画が取れない)。

Considered Options: クラウドの runner(GPU が無い)、CI を持たない(「保守できる」を示せない)。

見直す条件: 外からの PR を受けるとき。PR の検証はクラウドの runner(ビルドとテストだけ)に分ける。
