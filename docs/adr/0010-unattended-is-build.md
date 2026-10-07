# 無人実行は Windows のビルドに引数を渡す

エディタに依存しない。小さな窓で描画は残す(-nographics は使わない。SDF と頂点バッファに GPU が要る)。エディタ依存が前身の実装の無人化を止めた。

Considered Options: エディタの batchmode(-nographics と組むと GPU が無い)、エディタ Play の自動化(Unity の再起動ごとに設定が要る)、クラウド(GPU と Unity のライセンスの壁)。

見直す条件: ビルドの時間が反復の足かせになったとき。開発中はエディタの Play で同じランナーを呼ぶ口を残す。
