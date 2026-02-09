#!/bin/bash
# capture/配下の全フォルダに対してstep3-helper.shを実行

set -e

# dry-runオプションのチェック
DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAPTURE_DIR="$SCRIPT_DIR/capture"

if [ ! -d "$CAPTURE_DIR" ]; then
    echo "エラー: captureディレクトリが見つかりません: $CAPTURE_DIR"
    exit 1
fi

echo "============================================================"
if [ "$DRY_RUN" = true ]; then
    echo "📋 全キャプチャの処理対象確認（Dry Run）"
else
    echo "📚 全キャプチャのPDF再生成を開始します"
fi
echo "============================================================"
echo ""

# capture/配下のフォルダ名を取得（ディレクトリのみ）
FOLDERS=$(find "$CAPTURE_DIR" -maxdepth 1 -type d ! -path "$CAPTURE_DIR" -exec basename {} \; | sort)

if [ -z "$FOLDERS" ]; then
    echo "処理対象のフォルダが見つかりませんでした。"
    exit 0
fi

# フォルダ数をカウント
TOTAL=$(echo "$FOLDERS" | wc -l | tr -d ' ')
CURRENT=0

echo "処理対象フォルダ: $TOTAL 個"
echo ""

# 各フォルダに対してstep3-helper.shを実行
for folder in $FOLDERS; do
    CURRENT=$((CURRENT + 1))
    
    # htmlフォルダが存在するかチェック
    if [ ! -d "$CAPTURE_DIR/$folder/html" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "[$CURRENT/$TOTAL] ⏭️  スキップ: $folder (htmlフォルダなし)"
        else
            echo "[$CURRENT/$TOTAL] ⏭️  スキップ: $folder (htmlフォルダなし)"
            echo ""
        fi
        continue
    fi
    
    # HTMLファイル数を取得
    HTML_COUNT=$(find "$CAPTURE_DIR/$folder/html" -maxdepth 1 -name "*.html" ! -name "index.html" ! -name "*temp*" | wc -l | tr -d ' ')
    
    if [ "$DRY_RUN" = true ]; then
        # Dry Runモード: 情報だけ表示
        echo "[$CURRENT/$TOTAL] ✅ $folder"
        echo "    HTMLファイル数: ${HTML_COUNT}ファイル"
        echo "    入力: capture/$folder/html/"
        echo "    出力: capture/$folder/$folder.pdf"
        
        # 既存のPDFファイルがあれば表示
        if [ -f "$CAPTURE_DIR/$folder/$folder.pdf" ]; then
            EXISTING_SIZE=$(ls -lh "$CAPTURE_DIR/$folder/$folder.pdf" | awk '{print $5}')
            echo "    既存PDF: $EXISTING_SIZE"
        fi
        echo ""
    else
        # 通常モード: 実際に実行
        echo "[$CURRENT/$TOTAL] 🔄 処理中: $folder"
        echo "------------------------------------------------------------"
        
        # step3-helper.shを実行
        "$SCRIPT_DIR/step3-helper.sh" "$folder"
        
        echo ""
    fi
done

echo "============================================================"
if [ "$DRY_RUN" = true ]; then
    echo "✅ 処理対象確認完了: $TOTAL フォルダ中 処理対象を確認しました"
    echo ""
    echo "実際に実行するには:"
    echo "  ./all-for-step3.sh"
else
    echo "✅ 全キャプチャのPDF再生成が完了しました"
fi
echo "============================================================"
