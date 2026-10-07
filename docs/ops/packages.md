# 依存(Packages/manifest.json に入れるもの)

PC 側で Unity 6 LTS(URP)のプロジェクトを作ってから足す。manifest.json は環境の範囲。

| パッケージ | 用途 | 入れ方 | ライセンス |
|---|---|---|---|
| com.vrmc.vrm (UniVRM 1.0 系) | VRM 1.0 の読み込み、SpringBone(手動更新) | UniVRM の README の git URL を manifest に | MIT |
| com.unity.visualeffectgraph | MeshToSDFBaker(SDF Bake Tool API) | Package Manager | Unity Companion |
| com.unity.test-framework | EditMode / PlayMode テスト | Package Manager | Unity Companion |
| com.unity.burst, com.unity.collections | CPU の参照実装の高速化(M1) | Package Manager | Unity Companion |
| MagicaCloth 2 | 第2の被検体(任意) | Asset Store。Assets/MagicaCloth2 は .gitignore で除外。MAGICACLOTH2 の記号で #if | 有料。ソースは入れない |

注意: UniVRM の手動更新は `Vrm10Instance.UpdateType = None` と `FastSpringBoneService.Instance.UpdateType = Manual`、毎フレーム `Runtime.Process()` のあと `ManualUpdate(dt)`。
