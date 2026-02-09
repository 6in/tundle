# Kindle Capture to PDF

Kindle for Macのスクリーンキャプチャから、OCR処理を経てPDFを生成するツール。

## 特徴

- 📸 **自動キャプチャ**: Kindle for Macのページを自動でキャプチャ
- 🔍 **高精度OCR**: YomiToku（日本語特化OCR）でテキスト抽出
- 📄 **PDF生成**: HTML経由で高品質なPDFを生成
- 🎨 **Tailwind CSS**: 美しいHTMLスタイリング
- 🔎 **検索可能**: HTML/PDF内でテキスト検索が可能
- 🖼️ **プレビュー**: index.htmlで変換結果をブラウザで確認
- 📦 **分割出力**: NotebookLM用に大容量PDFを分割可能

## 必要環境

- macOS (Apple Silicon / Intel)
- Python 3.12以上
- [uv](https://github.com/astral-sh/uv) (Pythonパッケージマネージャ)
- Kindle for Mac

## インストール

### 1. uvのインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. リポジトリのクローン

```bash
git clone <このリポジトリのURL>
cd tundle
```

### 3. 依存関係のインストール

```bash
uv sync
```

これで以下のパッケージが自動インストールされます：
- yomitoku (OCRエンジン)
- weasyprint (HTML→PDF生成)
- pillow (画像処理)
- その他の依存関係

### 4. WeasyPrint用システムライブラリのインストール（macOS）

```bash
brew install pango gdk-pixbuf libffi gobject-introspection
```

### 5. WeasyPrint用環境変数の設定（macOS）

一時的に設定する場合：

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

恒久的に設定する場合（zshの例）：

```bash
echo 'export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"' >> ~/.zshrc
source ~/.zshrc
```

## 使い方

### 基本的な使用方法

```bash
./kindle-to-pdf.sh
```

Kindle for Macで本を開いた状態で実行すると、自動でキャプチャ→OCR→PDF変換を行います。

### オプション

| オプション | 説明 | デフォルト |
|---|---|---|
| `--title TITLE` | 出力フォルダ名 | 現在日時 (例: 20260208000229) |
| `--base-dir DIR` | 保存先ベースディレクトリ | `capture` |
| `--max-pages N` | 最大キャプチャページ数 | 無制限 |
| `--wait SECONDS` | ページめくり待機時間（秒） | 1.0 |
| `--crop-top PIXELS` | 上部トリミング（ピクセル） | 0 |
| `--crop-bottom PIXELS` | 下部トリミング（ピクセル） | 0 |
| `--crop-left PIXELS` | 左部トリミング（ピクセル） | 0 |
| `--crop-right PIXELS` | 右部トリミング（ピクセル） | 0 |
| `--pdf-filename NAME` | 出力PDFファイル名 | `book.pdf` |
| `--pages-per-file N` | PDF分割単位（ページ数） | 分割なし |

### 使用例

#### 1. テスト実行（10ページのみ）

```bash
./kindle-to-pdf.sh --max-pages 10 --title test-book
```

#### 2. トリミング付きキャプチャ

Kindleのヘッダー/フッターを削除する場合：

```bash
./kindle-to-pdf.sh --crop-top 70 --crop-bottom 40 --title my-book
```

#### 3. PDF分割（NotebookLM用）

50ページごとに分割してPDFを生成：

```bash
./kindle-to-pdf.sh --pages-per-file 50 --pdf-filename book.pdf --title large-book
```

分割すると以下の2種類が生成されます：
- `book-001.pdf`, `book-002.pdf`, ... (AI用: 高品質)
- `book_light.pdf` (人間用: 16階調グレースケール、軽量)

#### 4. フルカスタマイズ

```bash
./kindle-to-pdf.sh \
  --title "完全な本" \
  --max-pages 100 \
  --crop-top 80 \
  --crop-bottom 50 \
  --wait 1.5 \
  --pdf-filename complete.pdf \
  --pages-per-file 50
```

## 出力ファイル

実行後、以下のファイルが生成されます：

```
capture/
└── 20260208000229/          # タイトル名のフォルダ
    ├── images/              # キャプチャ画像
    │   ├── 001.png
    │   ├── 002.png
    │   └── ...
    ├── html/                # OCR結果のHTML
    │   ├── 001.html
    │   ├── 002.html
    │   ├── ...
    │   ├── index.html       # プレビュー用HTML
    │   ├── index.template.html
    │   └── server.py        # 検索用サーバー
    ├── book.pdf             # 結合PDF (AI用)
    └── book_light.pdf       # 軽量PDF (人間用) ※分割時のみ
```

### HTMLプレビューの使い方

OCR結果をブラウザで確認できます：

```bash
cd capture/20260208000229
python html/server.py
```

ブラウザで `http://localhost:8000/html/index.html` を開くと：
- HTML/画像の2ペイン表示
- 本文検索機能
- キーボード操作（←→でページ移動）

## 各ステップの詳細

### Step 1: 画像キャプチャ (step1.py)

Kindle for Macのウィンドウをキャプチャします。

```bash
uv run python step1.py --max-pages 10 --crop-top 70
```

### Step 2: OCR + HTML変換 (step2.py)

YomiTokuで日本語OCRを実行し、HTMLを生成します。

```bash
uv run python step2.py capture/20260208000229 --output-dir capture/20260208000229/html
```

### Step 3: PDF生成 (step3.py)

HTMLをWeasyPrintでPDFに変換します（A1サイズ、HTMLレイアウト再現）。

```bash
uv run python step3.py capture/20260208000229/html --output capture/20260208000229/book.pdf
```

### Step 4: 軽量PDF生成 (step4.py)

16階調グレースケール化で軽量PDFを作成します。

```bash
uv run python step4.py capture/20260208000229 --output-filename book_light.pdf
```

## トラブルシューティング

### Kindleウィンドウが見つからない

- Kindle for Macが起動しているか確認
- ウィンドウが最小化されていないか確認

### OCRが遅い

- Apple Silicon Macの場合、Metal (GPU)が自動で使われます
- Intel Macの場合、CPUモードで動作します（少し遅いです）

### PDFが大きすぎる

`--pages-per-file 50` で分割してください。NotebookLMの200MB制限を回避できます。

### 検索が動かない

HTMLプレビューの検索機能は`server.py`が必要です：

```bash
cd capture/<タイトル>
python html/server.py
```

## ライセンス

MIT

## 参考

- [YomiToku](https://github.com/kotaro-kinoshita/yomitoku) - 日本語OCRエンジン
- [Playwright](https://playwright.dev/) - ブラウザ自動化ツール
