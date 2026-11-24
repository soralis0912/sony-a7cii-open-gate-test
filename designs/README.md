# designs/

1つの JSON が1つの「デザイン」＝カメラのメモリに当てるバイトパッチの集合。
形式は [../docs/DESIGN_FORMAT.md](../docs/DESIGN_FORMAT.md)。

**現在、ILCE-7CM2 向けに検証済みのデザインは1件もありません。**
`TEMPLATE.json` は形式の見本で、アドレスは全部ゼロのプレースホルダです。

デザインを1件作ったら、カメラに送る前に必ずオフラインで照合する：

```bash
python3 ../scripts/verify_design.py <name>.json \
  --image <p15>/lib/appFw.so
```

`old` が1つでも一致しなければ、そのデザインは別のファームウェア・別の機種・
または単純な間違いなので、カメラには送らない。
