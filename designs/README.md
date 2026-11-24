# designs/

1つの JSON が1つの「デザイン」＝カメラのメモリに当てるバイトパッチの集合。
形式は [../docs/DESIGN_FORMAT.md](../docs/DESIGN_FORMAT.md)。

**実機に当てたデザインは1件もありません。** 候補が2件あり、
検証済みなのは「そのアドレスにその `old` が確かにある」ところまでです。

| デザイン | 対象 | 内容 |
| --- | --- | --- |
| `og_window_fullheight_v0.json` | p8 `cpapp-b.bin` | 16:9 窓（7008x3942）を全面（7008x4672）にする |
| `og_voffset_zero_v0.json` | p8 `cpapp-b.bin` | センタリングオフセット 366 → 0、対の 403 → 19 |

根拠は [../docs/SENSOR_TABLE.md](../docs/SENSOR_TABLE.md)。
`TEMPLATE.json` は形式の見本で、アドレスはゼロのプレースホルダです。

デザインを1件作ったら、カメラに送る前に必ずオフラインで照合する：

```bash
python3 ../scripts/verify_design.py <name>.json \
  --image "cpapp=<p8>/cpapp-b.bin"
```

`--image` は `where=パス` の形で、デザインの `where` と対応させる。

`old` が1つでも一致しなければ、そのデザインは別のファームウェア・別の機種・
または単純な間違いなので、カメラには送らない。
