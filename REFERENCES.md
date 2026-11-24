# 参照元と帰属 / References and attribution

このリポジトリは ILCE-7CM2（A7C II）について**新規に**書いたもので、
どのリポジトリの fork でもありません。上流のコードは移植していません。
記録しているのはハッシュ・オフセット・手順だけです。

This repository was written from scratch for the ILCE-7CM2 (A7C II). It is not a
fork of anything, and no upstream code has been copied into it. It records only
hashes, offsets and procedures.

## 雛形 / Template

- [ArcaneLantern/a7iv-open-gate-test](https://github.com/ArcaneLantern/a7iv-open-gate-test)
  — A7 IV（6.02）のオープンゲート・フィールドテストキット。
  リポジトリ構成、デザイン（バイトパッチ集合）という考え方、
  「一時設定のみ・コールドブートで復帰」という運用方針を参考にした。
  **A7 IV の成果はすべて原著者のもの。** ライセンスは GPLv3。
  本リポジトリはそのコード・バイナリ（`libJit_*.so`、APK、ホストスクリプト）を
  一切含まない。

## 直接の前提 / Direct prerequisites

- [soralis0912/sony-a7cii-feature-research](https://github.com/soralis0912/sony-a7cii-feature-research)
  — ILCE-7CM2 2.01 の展開、製品クラス `PRODUCT_MODEL_PP`、BKID 6,450件、
  実機のサービスモード接続とバックアップ取得。
- [soralis0912/sony-a7cii-shell-access](https://github.com/soralis0912/sony-a7cii-shell-access)
  — サービス権限レベル（A/B/C）とネイティブ実行経路の判定。本リポジトリの
  最大の前提条件がここにある。
- [soralis0912/fwtool.py](https://github.com/soralis0912/fwtool.py/tree/a7cII)
  （`a7cII` ブランチ）— CXD90057 / ILCE-7CM2 対応の展開ツール。上流は
  [DavidBuchanan314/fwtool.py](https://github.com/DavidBuchanan314/fwtool.py)、
  さらに上流は [ma1co/fwtool.py](https://github.com/ma1co/fwtool.py)。

## 技術的参照 / Technical references

- [ma1co/Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)
  — サービスモードへの切り替えと Senser プロトコルの実装。
- [Erlla/sony-a7m4-custom-firmware](https://github.com/Erlla/sony-a7m4-custom-firmware)
  — サービスプロトコル経由のネイティブコード実行、更新系の原理。GPLv3。
- [DavidBuchanan314/ILCE-7M4-RE](https://github.com/DavidBuchanan314/ILCE-7M4-RE)
  — BootROM / Fastboot の参考。
- [leogenot/sony-a7iv-feature-research](https://github.com/leogenot/sony-a7iv-feature-research)
  — A7 IV のサービスモード手順。

## ライセンス / License

未設定。雛形にした A7 IV キットは GPLv3 なので、そのコードや文章を取り込む場合は
GPLv3 の条件に従う必要がある。本リポジトリでは**考え方と数値の引用、出典明記に
留め、コードは移植していない**。公開する場合はライセンスを決めてから。

Not set yet. The A7 IV kit used as a template is GPLv3, so taking its code or
prose would carry those terms. This repository keeps to the approach and cited
numbers, with no code copied. Decide a license before publishing.
