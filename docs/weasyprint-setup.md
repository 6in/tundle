# WeasyPrint セットアップメモ

## 概要
step3.pyでHTMLレイアウトを保持したPDF生成を行うため、weasyprintを採用しました。

## システム要件（macOS）

### Homebrewでシステムライブラリをインストール

```bash
# 必要なシステムライブラリをインストール
brew install pango gdk-pixbuf libffi gobject-introspection
```

インストールされるパッケージ：
- `pango`: テキストレイアウトエンジン
- `gdk-pixbuf`: 画像処理ライブラリ
- `libffi`: 外部関数インターフェース
- `gobject-introspection`: GObject型システム

### Pythonパッケージのインストール

```bash
# weasyprintをインストール
uv pip install weasyprint
```

## 環境変数の設定

weasyprintを実行する際は、Homebrewでインストールしたライブラリへのパスを設定する必要があります。

### 一時的な設定（シェルで毎回実行）

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

### 恒久的な設定（推奨）

`~/.zshrc` または `~/.bash_profile` に以下を追加：

```bash
# WeasyPrint用のライブラリパス
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

設定後、シェルを再起動するか以下を実行：

```bash
source ~/.zshrc  # zshの場合
source ~/.bash_profile  # bashの場合
```

## 実行方法

### 環境変数を含めて実行

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH" && uv run python step3.py capture/tik-tok/html
```

### 環境変数が設定済みの場合

```bash
uv run python step3.py capture/tik-tok/html
```

## パフォーマンス比較

| 手法 | ファイルサイズ (157ページ) | 1ページあたり | 特徴 |
|------|--------------------------|--------------|------|
| **weasyprint** | **1.52 MB** | **9.9 KB** | HTMLレイアウト完全再現、テーブル対応 |
| ReportLab (旧版) | 3.3 MB | 21 KB | テキスト抽出のみ、軽量 |
| Playwright (最旧版) | 47 MB | 300 KB | 重すぎて廃止 |

## トラブルシューティング

### エラー: `cannot load library 'libgobject-2.0-0'`

**原因**: システムライブラリへのパスが通っていない

**解決方法**:
1. Homebrewでライブラリがインストールされているか確認:
   ```bash
   brew list | grep -E "pango|gdk-pixbuf|gobject"
   ```

2. 環境変数が設定されているか確認:
   ```bash
   echo $DYLD_LIBRARY_PATH
   ```

3. 上記の環境変数設定を実施

### エラー: `WeasyPrint could not import some external libraries`

**原因**: 必要なシステムライブラリがインストールされていない

**解決方法**:
```bash
brew install pango gdk-pixbuf libffi gobject-introspection
```

## 注意事項

- macOS Catalina (10.15) 以降では、`DYLD_LIBRARY_PATH` の設定が必要です
- Homebrewのインストール場所が `/opt/homebrew` でない場合（Intel Macなど）は、パスを適宜変更してください
  - Intel Mac: `/usr/local/lib`
  - Apple Silicon: `/opt/homebrew/lib`

## 参考リンク

- [WeasyPrint公式ドキュメント](https://doc.courtbouillon.org/weasyprint/)
- [WeasyPrintインストールガイド](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)
