# Lenovo oemowninfo ツール（配布用）

Windows用。Python 3.10以降をインストールしてください。python.orgのPythonを使う場合はPython LauncherまたはPATH設定が必要です。
ZIPを展開し、install-dependencies.cmdを実行してください。インターネット接続が必要です。依存ライブラリをこのフォルダーのdependenciesへインストールします。
Python本体・USBドライバー・依存ライブラリはZIPに含めていません。依存ライブラリにはそれぞれのライセンスが適用されます。

端末をbootloader fastbootモードで接続し、このフォルダーでコマンドを実行してください。

```cmd
oemowninfo-get.cmd sn
oemowninfo-get.cmd countrycode
oemowninfo-get.cmd usbdebugflag
oemowninfo-get.cmd --list
```

get対応項目: sn, psn, skuid, fingerprint, countrycode, btmac, wifimac, usbdebugflag, vibcalil, vibcalir, displayid。
Lenovo TB320FCの解析対象ABL向けです。他機種・別ABLへの対応は保証しません。通常fastbootで接続できても、このツールでアクセスできるかはUSBドライバーによります。ドライバーの自動変更はしません。

## ブートローダーのロック状態

対象のLenovo Y700 Gen 2（TB320FC）では、ブートローダーがlocked（ロック）状態でもunlocked（アンロック）状態でも、oemowninfoコマンドを実行できます。このコマンドを使用するためのブートローダーアンロックは不要です。locked状態での動作も実機で確認しています。

この確認はテストした端末・ABLについてのものです。別のファームウェアでの動作を保証するものではありません。ロック状態にかかわらず、setでの書き込みには --write の指定が必要です。

## 書き込み

setはsnとcountrycodeのみ対応しています。次はプレビューのみで、USBへアクセスしません。

```cmd
oemowninfo-set.cmd countrycode VALUE
oemowninfo-set.cmd sn VALUE
```

実際に書き込む場合は、VALUEを正しい値に置き換え、末尾に `--write` を付けてください。

```cmd
oemowninfo-set.cmd countrycode VALUE --write
oemowninfo-set.cmd sn VALUE --write
```

`--write`を付けない場合はプレビューのみです。
変更前・要求値をbackupsへ保存し、書き込み後に読み戻して照合します。バックアップは対象項目の文字列で、パーティション全体ではありません。自動復元・再試行は行いません。結果不明の場合はgetで確認してください。
入力は1～31文字のASCII（空白・カンマ不可）。countrycode clearは拒否します。nullや00000000を書いてもゼロ埋めにはなりません。
書き込みは端末の識別情報や動作に影響します。読み取り確認だけならgetを使用してください。

## 再配布

このZIPには個人のバックアップ、端末SN、ファームウェア、キャッシュ、個人用絶対パスを含めていません。
使用後はbackupsにSN等が入るため、再配布時に除外してください。依存ライブラリを追加して再配布する場合は、そのライセンスと再配布条件を保持・確認してください。
