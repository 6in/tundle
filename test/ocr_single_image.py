#!/usr/bin/env python3
"""
macOS Vision Frameworkを使用して画像からテキストを抽出するスクリプト
"""

import sys
import os
from Cocoa import NSURL
from Vision import (
    VNRecognizeTextRequest,
    VNImageRequestHandler,
    VNRequestTextRecognitionLevelAccurate
)

def ocr_image(image_path):
    if not os.path.exists(image_path):
        print(f"エラー: 画像ファイルが見つかりません: {image_path}")
        return

    # パスを絶対パスに変換
    abs_path = os.path.abspath(image_path)
    file_url = NSURL.fileURLWithPath_(abs_path)

    # テキスト認識リクエストの作成
    request = VNRecognizeTextRequest.alloc().init()
    # 認識レベルを高精度に設定
    request.setRecognitionLevel_(VNRequestTextRecognitionLevelAccurate)
    # 言語推定と補正を使用
    request.setUsesLanguageCorrection_(True)
    # 日本語と英語を認識対象にする
    request.setRecognitionLanguages_(["ja-JP", "en-US"])

    # リクエストハンドラの作成と実行
    handler = VNImageRequestHandler.alloc().initWithURL_options_(file_url, {})
    success, error = handler.performRequests_error_([request], None)

    if not success:
        print(f"OCR処理に失敗しました: {error}")
        return

    # 結果の取得
    results = request.results()
    if not results:
        print("テキストが検出されませんでした。")
        return

    print(f"--- OCR結果 ({image_path}) ---")
    for observation in results:
        # 最も信頼度の高い候補を取得
        candidate = observation.topCandidates_(1)[0]
        print(candidate.string())
    print("-----------------------------")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 引数がない場合はデフォルトでユーザー指定のファイルを使用
        target_image = "capture/20260207180313/005.png"
    else:
        target_image = sys.argv[1]
    
    ocr_image(target_image)
