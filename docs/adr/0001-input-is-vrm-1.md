# 入力は VRM 1.0

アバターの入力形式は VRM 1.0 にする。Humanoid の骨、SpringBone の定義、コライダー、利用条件のメタを1ファイルで持ち、VRoid からそのまま出せるため。

Considered Options: FBX と手動の設定(揺れものの定義が無く入口を別に作る必要がある)、Unity の prefab(エンジンに閉じる)、VRM 0.x(書き出しの主流が 1.0 に移った)、素の glTF(SpringBone が無い)。

見直す条件: スタジオ向けに FBX の受け口が要ると分かったとき(VRM への変換を前処理として足す)。
