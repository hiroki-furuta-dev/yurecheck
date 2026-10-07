# Unity 6 は C# 9 なので、型の縛りは readonly struct と interface で作り、層は asmdef で縛る

Unity 6(6000.x)の C# は 9.0 で、record の完全対応、init、required は使えない(公式が「Init only setters は非対応」と明記)。単位の型は readonly struct と private コンストラクタ、必須項目はコンストラクタ引数、手順の縛りは interface の型状態(Attach の戻り値にしか Step が無い)で作る。層の向きは asmdef の参照で Metrics ← Judge ← Output の一方向に固定し、計測の中に閾値比較を書くコードがコンパイルできない形にする。MagicaCloth 2 の条件コンパイルは Subjects.MC2 の asmdef に閉じ、本体に #if を書く場所を作らない。

Considered Options: IsExternalInit を自前で定義して record と init を使う(広く行われているが公式は非対応と明記。採らない)、C# 15 の closed と union(.NET 11 preview。Unity では使えない)、層を名前空間の約束だけで守る(破れる)。

Consequences: Burst のジョブ内は生の float でよく、集計値を CPU に戻した時点で型に包む。ScriptableObject は生の値を持ち、読み込み時に Thresholds へ parse する。詳細と出典は docs/DESIGN.md 6b と、この ADR の下の Considered Options。
