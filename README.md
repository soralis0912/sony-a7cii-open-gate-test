# A7C II オープンゲート：フィールドテストキット（開発中）

[English version](README_EN.md)

> [!WARNING]
> 自己責任で利用してください。本リポジトリの利用による損害について、作者は責任を負いません。
> カメラのメモリやファームウェアに手を入れる操作は、起動不能・撮影データや調整値の
> 破壊・保証や修理への影響を招きえます。実機で試す前に設定バックアップを取り、
> 純正バッテリーを使い、USB を途中で抜かないでください。

Sony **ILCE-7CM2**（A7C II）ファームウェア **Ver. 2.01** で、センサーの 3:2 全面を
そのまま記録する「オープンゲート」を**一時設定（メモリのみ）**で有効にするための
キットを作る試みです。

> **状態：センサー側のアドレスは特定済み、実機での適用は1件も成立していません。**
> 候補デザインが2件ありますが、検証済みなのは「そのアドレスにその値が
> 確かにある」ところまでで、カメラには当てていません。

## これは何の移植か

[ArcaneLantern/a7iv-open-gate-test](https://github.com/ArcaneLantern/a7iv-open-gate-test)
は Sony A7 IV（6.02）向けに、USB のサービスプロトコル経由でネイティブヘルパー
（`libJit_level*.so`）をカメラに読み込ませ、センサー geometry・スケーラ・
エンコーダのテーブルを**その電源が入っている間だけ**書き換えて、
3840x2560 や 5760x3840 のオープンゲート記録を実現しています。
バッテリーを抜けば元に戻ります。

本リポジトリは **fork ではなく**、その設計思想を A7C II 向けに作り直す新規リポジトリです。
A7 IV の成果はすべて原著者のものです。詳細は [REFERENCES.md](REFERENCES.md)。

## A7C II で成立するのか（現時点の判定）

| 項目 | 状況 |
| --- | --- |
| センサー | A7 IV と同世代の 33MP（7008 x 4672）。オープンゲートの寸法設計は近い見込み |
| アスペクト／デスキーズのプロパティ | ILCE-7CM2 の `appFw.so` に存在（`0x02cf01fc ASPECT_RATIO`、`DE_SQUEEZE_DISP` 系） |
| ネイティブコード実行の経路 | **半分確認済み（2026-11-24 訂正）。** A7 IV キットは Jiritsu のファイル書き込みで一時 `libJit.so` を置いて読み込ませる。Jiritsu は `0x40` AdjustControl 経由（カテゴリ `0x1001`）で**権限レベルに依らず**、**読み取りは実機で確認済み**。未確認なのは**書き込み側**（`SET_FILE` `0x4007`） |
| センサー geometry のアドレス | **特定済み（2026-11-24）。** p8 の `cpapp-b.bin` 内、`0xdd81d8` の読み出しモードテーブル。全面 7008x4672 と現行 16:9 窓 7008x3942 の両方が入っている。[docs/SENSOR_TABLE.md](docs/SENSOR_TABLE.md) |
| 出力サイズ表 | **特定済み（2026-11-24）。** `cpapp-b.bin` の `0xbefe38` に 4K 幅の4変種（16:9 / 4:3 / **3:2 = 3840x2560** / 1:1）が並んでいる。**3:2 は Sony 自身の表に既にある** |
| スケーラ／エンコーダのアドレス | **未特定。** A7 IV のアドレスは流用できない |
| 実機適用 | **未実施** |

**訂正（2026-11-24）**：ここに「その経路は `0xff00` TestMode で、
サービス権限レベル A のテーブルにしか無い」と書いていましたが誤りでした。
Jiritsu は `0x40` AdjustControl 経由（カテゴリ `0x1001`、コマンド
`0x4001`〜`0x4012`）で、AdjustControl は全レベルのテーブルにあります。
実機でも読み取り（`GET_FILE2` `0x4011`）が通っています。

したがって関門は「レベル A が出るか」ではなく、**Jiritsu の書き込み
（`SET_FILE` `0x4007` / `SET_FILE2` `0x4010`）が通るか**です。
コマンド一覧と危険な隣人（`FORMAT` / `FIRMUP` / `FILE_DELETE`）は姉妹リポジトリ
[sony-a7cii-feature-research](https://github.com/soralis0912/sony-a7cii-feature-research)
の `evidence/jiritsu-commands-a7cii-201.json`、手順は
[sony-a7cii-shell-access](https://github.com/soralis0912/sony-a7cii-shell-access)
の `docs/FIELD_SESSION.md`。

**今すぐ実機で試せるものが1つだけあります**：デスキーズ表示系の
バックアッププロパティ。ネイティブ実行もデザインも要りません。手順は
[docs/PROPERTY_EXPERIMENTS.md](docs/PROPERTY_EXPERIMENTS.md)。

## 入っているもの

```
designs/     デザイン（バイトパッチ集合）。候補2件（old のみ検証済み）
scripts/     verify_design.py       デザインの old バイトを展開済み fw と照合
             locate_sensor_table.py センサー読み出しモードテーブルを見つけて全件デコード
             locate_geometry.py     fw 内で寸法が出てくる位置を探す汎用プローブ
docs/        SENSOR_TABLE.md     特定したテーブルの構造と候補デザインの根拠
             DERIVATION.md       A7 IV の各ステップに対して A7C II で何を特定すべきか
             DESIGN_FORMAT.md    デザイン JSON の形式
             PROPERTY_EXPERIMENTS.md
                                 ネイティブ実行なしで今すぐ試せる実験（実機）
evidence/    プローブの出力（再現可能な記録）
```

ホスト側の実行スクリプト（Windows の `.cmd`、macOS の `.command`、Android アプリ）は、
**当てるデザインが1件も無い段階では置きません**。当てるものが決まってから、
送信経路ごと追加します。

## 使い方（今できること）

公式アップデートは各自で入手し、[fwtool.py](https://github.com/soralis0912/fwtool.py)
の `a7cII` ブランチで展開してください。

```bash
# センサー読み出しモードテーブルを見つけて全53レコードをデコードする
python3 scripts/locate_sensor_table.py \
  <p8>/cpapp-b.bin --json evidence/sensor-table-a7cii-201.json

# 候補デザインの old バイトを照合する
python3 scripts/verify_design.py designs/og_window_fullheight_v0.json \
  --image "cpapp=<p8>/cpapp-b.bin"

# 汎用プローブ：寸法が出てくる候補位置を探す（appFw 側）
python3 scripts/locate_geometry.py \
  <p15>/lib/appFw.so --section .rodata --section .data --limit 6 \
  --json evidence/geometry-probe-a7cii-201.json

# ある位置の前後を見る
python3 scripts/locate_geometry.py <p15>/lib/appFw.so --context 3722680

# デザインを書いたら、カメラに触る前に必ず照合する
python3 scripts/verify_design.py designs/<name>.json --image <p15>/lib/appFw.so
```

`<p15>` は
`<fwtool.py>/unpacked/firmware.tar_unpacked/0700_part_image/dev/nflasha15_unpacked`、
`<p8>` は同じ階層の `nflasha8_unpacked`。

## 含めないもの

Sony のファームウェア、復号済みバイナリ、カメラのバックアップ、シリアル番号、
復号鍵、抽出したプロプライエタリファイル、他リポジトリのバイナリ（APK や
`libJit_*.so` を含む）は意図的に含めていません。記録するのはハッシュ・
オフセット・手順だけです。

ライセンスは未設定です。上流のコードは移植していません（[REFERENCES.md](REFERENCES.md)）。

## 謝辞

- **[ArcaneLantern/a7iv-open-gate-test](https://github.com/ArcaneLantern/a7iv-open-gate-test)**
  — 本リポジトリの雛形。A7 IV で「一時設定だけでオープンゲートが撮れる」ことを
  実証し、デザイン（バイトパッチ集合）という形でそれを公開した研究。
- **[Erlla/sony-a7m4-custom-firmware](https://github.com/Erlla/sony-a7m4-custom-firmware)**
  — 普通の USB ケーブルとサービスプロトコルでカメラ上でネイティブコードが
  走ることを示した研究。
- **[ma1co/Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)**
  — マスストレージからサービスモードへの切り替えと、サービスプロトコルの実装。
- **[DavidBuchanan314/fwtool.py](https://github.com/DavidBuchanan314/fwtool.py)**
  — 解析に必要なファームウェアの展開。上流の
  [ma1co/fwtool.py](https://github.com/ma1co/fwtool.py) にも謝意を。
- **[leogenot/sony-a7iv-feature-research](https://github.com/leogenot/sony-a7iv-feature-research)**
  — A7 IV のサービスモード手順を文書化した研究。
- **[soralis0912/sony-a7cii-feature-research](https://github.com/soralis0912/sony-a7cii-feature-research)**
  — 本リポジトリが前提にする ILCE-7CM2 側の事実（展開、製品クラス、
  プロパティ一覧、実機でのサービスモード接続）。
