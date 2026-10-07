# 固定ステップで回す

Time.captureDeltaTime を 1/60 に固定し、VSync を切り、乱数の種を固定する。実時間に依存せず、機械の速さが変わっても同じ軌道になり、CSV の md5 で決定性を確かめられる。処理時間は固定ステップの影響を受けない別の時計(Stopwatch、FrameTimingManager)で測る。

Considered Options: 可変 dt(機械の速さで軌道が変わり決定性が取れない。前身の実装の反省)、FixedUpdate の物理(Animator と被検体の更新順を自分で握れない)。

見直す条件: 被検体が独自の時計を持つとき(MagicaCloth 2 の既定 90Hz は設定で合わせる)。
