# ROADMAP

Milestone は GitHub の Milestones と同じ名前で持つ。`/next --all` がここと Issue を突き合わせる。

| 段 | 出るもの | 完了の条件 |
|---|---|---|
| M0 基盤 | 空走するランナー | リポジトリ、LICENSE、Unity 6 LTS + URP + UniVRM + VFX Graph、VRoid の VRM 3体、CC0 クリップ 5本と ATTRIBUTION、core/Yurecheck.Core と dotnet test が tools.yml で回り DLL が Assets/Yurecheck/Plugins/ に写る、Scenario と Writer、BuildScript と CLI、hooks と skills が Windows で動く、空のシナリオが CSV を書く |
| M1 指標 | 合成ケースが全部通る。予算の実測 | 揺れもの頂点集合、SdfBaker、CPU の参照実装で4指標、EditMode テスト、固定ステップと決定性、1 時間の予算に収まるかの計測。収まらなければ compute 版 |
| M2 判定 | 最初の「覆した既定」の数字 | SpringBone 被検体、MC2 被検体、合成モーション、指標の妥当性の確認(目視の印)、閾値、report.md、PNG |
| M3 公開 | 提出できる形 | smoke と nightly、runner の手順、README 日英、AI_USAGE、METRICS、動画、実行ファイル |
| M4 判断 | v2 に入るか | 自作 XPBD、Maya 層、設定の自動探索、校正の補助コマンド |
