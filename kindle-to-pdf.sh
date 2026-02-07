#!/bin/bash

# Kindleキャプチャから PDF 生成までの一連処理
# step1: 画像キャプチャ
# step2: HTML変換 (YomiToku)
# step3: PDF結合

set -e  # エラーで停止

# 色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}📚 Kindle → PDF 変換パイプライン${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# デフォルト値
TITLE=$(date +"%Y%m%d%H%M%S")
BASE_DIR="capture"
MAX_PAGES=""
WAIT_TIME="1.0"
CROP_TOP="0"
CROP_BOTTOM="0"
CROP_LEFT="0"
CROP_RIGHT="0"
PDF_FILENAME="book.pdf"
PAGES_PER_FILE=""

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --title)
            TITLE="$2"
            shift 2
            ;;
        --base-dir)
            BASE_DIR="$2"
            shift 2
            ;;
        --max-pages)
            MAX_PAGES="$2"
            shift 2
            ;;
        --wait)
            WAIT_TIME="$2"
            shift 2
            ;;
        --crop-top)
            CROP_TOP="$2"
            shift 2
            ;;
        --crop-bottom)
            CROP_BOTTOM="$2"
            shift 2
            ;;
        --crop-left)
            CROP_LEFT="$2"
            shift 2
            ;;
        --crop-right)
            CROP_RIGHT="$2"
            shift 2
            ;;
        --pdf-filename)
            PDF_FILENAME="$2"
            shift 2
            ;;
        --pages-per-file)
            PAGES_PER_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "使用法: $0 [オプション]"
            echo ""
            echo "オプション:"
            echo "  --title TITLE              フォルダ名 (デフォルト: 日時)"
            echo "  --base-dir DIR             保存先ベースディレクトリ (デフォルト: capture)"
            echo "  --max-pages N              最大ページ数"
            echo "  --wait SECONDS             ページ待機時間 (デフォルト: 1.0)"
            echo "  --crop-top PIXELS          上部トリミング"
            echo "  --crop-bottom PIXELS       下部トリミング"
            echo "  --crop-left PIXELS         左部トリミング"
            echo "  --crop-right PIXELS        右部トリミング"
            echo "  --pdf-filename FILENAME    PDF出力ファイル名 (デフォルト: book.pdf)"
            echo "  --pages-per-file N         PDF分割ページ数 (省略時は分割しない)"
            echo "  -h, --help                 このヘルプを表示"
            echo ""
            echo "使用例:"
            echo "  $0"
            echo "  $0 --max-pages 10 --crop-top 70 --crop-bottom 40"
            echo "  $0 --title my-book --pdf-filename output.pdf"
            echo "  $0 --pages-per-file 50 --pdf-filename book.pdf"
            exit 0
            ;;
        *)
            echo "不明なオプション: $1"
            exit 1
            ;;
    esac
done

# パス設定
CAPTURE_DIR="${BASE_DIR}/${TITLE}"
HTML_DIR="${CAPTURE_DIR}/html"

echo -e "${YELLOW}設定:${NC}"
echo "  タイトル: ${TITLE}"
echo "  保存先: ${CAPTURE_DIR}"
echo "  PDFファイル名: ${PDF_FILENAME}"
if [ -n "$MAX_PAGES" ]; then
    echo "  最大ページ数: ${MAX_PAGES}"
fi
echo ""

# Step 1: 画像キャプチャ
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 1: 画像キャプチャ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

STEP1_CMD="uv run python step1.py --output-dir ${BASE_DIR} --title ${TITLE} --wait ${WAIT_TIME}"
STEP1_CMD="${STEP1_CMD} --crop-top ${CROP_TOP} --crop-bottom ${CROP_BOTTOM}"
STEP1_CMD="${STEP1_CMD} --crop-left ${CROP_LEFT} --crop-right ${CROP_RIGHT}"

if [ -n "$MAX_PAGES" ]; then
    STEP1_CMD="${STEP1_CMD} --max-pages ${MAX_PAGES}"
fi

echo "実行: ${STEP1_CMD}"
eval ${STEP1_CMD}

echo ""

# Step 2: HTML変換
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 2: HTML変換 (YomiToku)${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

STEP2_CMD="uv run python step2.py ${CAPTURE_DIR} --output-dir ${HTML_DIR}"

echo "実行: ${STEP2_CMD}"
eval ${STEP2_CMD}

echo ""

# Step 3: PDF結合
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 3: PDF結合${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

STEP3_CMD="uv run python step3.py ${HTML_DIR} --output-filename ${PDF_FILENAME}"

if [ -n "$PAGES_PER_FILE" ]; then
    STEP3_CMD="${STEP3_CMD} --pages-per-file ${PAGES_PER_FILE}"
fi

echo "実行: ${STEP3_CMD}"
eval ${STEP3_CMD}

echo ""

# Step 4: 人間用軽量PDFの作成
# (PAGES_PER_FILEの有無に関わらず、アーカイブ用として作成推奨ですが、
#  ここでは元のロジックに合わせて分割オプションがある場合に追加処理として記述するか、
#  あるいは常に実行するように変更するか。要望は「機能の置き換え」なので、
#  分割オプションに関係なく実行しても良いが、文脈的にStep4は「アーカイブ用」なので
#  常に実行する形にするのが自然かもしれません。
#  ただし、ユーザーは「置き換えて」と言っているので、条件分岐の中身を書き換えます)

if [ -n "$PAGES_PER_FILE" ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Step 4: 人間用軽量PDF作成（16階調グレー圧縮）${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # ファイル名を設定（book.pdf → book_light.pdf）
    LIGHT_PDF_FILENAME="${PDF_FILENAME%.*}_light.pdf"
    
    # 入力はCAPTURE_DIR（画像がある場所）を指定
    STEP4_CMD="uv run python step4.py ${CAPTURE_DIR} --output-filename ${LIGHT_PDF_FILENAME}"
    
    echo "実行: ${STEP4_CMD}"
    eval ${STEP4_CMD}
    echo ""
fi

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}✅ すべての処理が完了しました！${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
if [ -n "$PAGES_PER_FILE" ]; then
    echo -e "📁 分割PDF (AI用): ${GREEN}${CAPTURE_DIR}/${PDF_FILENAME%.*}-*.pdf${NC}"
    echo -e "📁 軽量PDF (人間用): ${GREEN}${CAPTURE_DIR}/${LIGHT_PDF_FILENAME}${NC}"
else
    echo -e "📁 出力先: ${GREEN}${CAPTURE_DIR}/${PDF_FILENAME}${NC}"
fi
echo ""

