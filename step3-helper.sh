#!/bin/bash
# step3.pyだけを実行するヘルパースクリプト
# 既にキャプチャ済みのHTMLに対してPDF生成を行う

set -e

if [ $# -lt 1 ]; then
    echo "使用方法: ./step3-helper.sh <title> [pages-per-file]"
    echo ""
    echo "例:"
    echo "  ./step3-helper.sh tik-tok          # output.pdfを生成"
    echo "  ./step3-helper.sh tik-tok 50       # 50ページごとに分割"
    exit 1
fi

TITLE="$1"
PAGES_PER_FILE="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="$SCRIPT_DIR/capture/$TITLE/html"
OUTPUT_DIR="$SCRIPT_DIR/capture/$TITLE"

# 入力ディレクトリの確認
if [ ! -d "$INPUT_DIR" ]; then
    echo "エラー: HTMLディレクトリが見つかりません: $INPUT_DIR"
    exit 1
fi

echo "============================================================"
echo "📄 PDF生成処理を開始します"
echo "============================================================"
echo "タイトル: $TITLE"
echo "入力ディレクトリ: $INPUT_DIR"
echo "出力ディレクトリ: $OUTPUT_DIR"
if [ -n "$PAGES_PER_FILE" ]; then
    echo "ページ分割: ${PAGES_PER_FILE}ページごと"
else
    echo "ページ分割: なし (1ファイルに結合)"
fi
echo ""

# step3.pyを実行
cd "$SCRIPT_DIR"

if [ -n "$PAGES_PER_FILE" ]; then
    uv run python step3.py "$INPUT_DIR" --output "$OUTPUT_DIR/$TITLE.pdf" --pages-per-file "$PAGES_PER_FILE"
else
    uv run python step3.py "$INPUT_DIR" --output "$OUTPUT_DIR/$TITLE.pdf"
fi

echo ""
echo "============================================================"
echo "✅ PDF生成完了"
echo "============================================================"
ls -lh "$OUTPUT_DIR/$TITLE"*.pdf 2>/dev/null || ls -lh "$OUTPUT_DIR/$TITLE.pdf"
