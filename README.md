# MicroKeyboard

自作マイクロキーボードの設計リポジトリです。回路図・PCB、筐体CAD、ZMKのシールド定義とキーマップをここで管理します。

## 構成

- `hardware/kicad/`: KiCad回路図、PCB、独自ライブラリ、製造データ
- `mechanical/case/`: 筐体CADの編集元と出力データ
- `boards/shields/micro_keyboard/`: XIAO nRF52840用ZMKシールド定義
- `config/`: ZMK依存関係と利用者設定
- `docs/`: 設計・部品・組立資料

## 現在の状態

AE-XCL103-3V3昇圧モジュールと[XIAO nRF52840（ピンなし表面実装）](docs/components/xiao_nrf52840.md)のシンボル・フットプリント・STEPモデルを登録しています。寸法・端子対応・再生成方法は[部品資料](docs/components/ae_xcl103_3v3.md)を参照してください。キー配列、GPIO割当、電源回路、基板形状、筐体寸法は設計作業で確定します。

## ファームウェア

ZMK本体は`config/west.yml`で取得し、このリポジトリではキーボード固有の設定を管理します。`build.yaml`にボードとシールドのビルド対象を設定すると、GitHub ActionsからUF2を取得できます。
