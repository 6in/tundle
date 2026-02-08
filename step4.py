#!/usr/bin/env python3
"""
Step 1でキャプチャされた画像を、人間が読みやすい軽量PDFとして結合するスクリプト
16階調グレースケールに減色してファイルサイズを抑制します。
"""

import argparse
import tempfile
import shutil
from pathlib import Path
from PIL import Image

def convert_images_to_pdf(input_dir, output_filename="merged_book.pdf", colors=16):
    """
    画像ファイルを読み込み、減色・圧縮してPDFにする
    """
    input_path = Path(input_dir)
    input_path = input_path.resolve()
    # 画像ディレクトリの決定（images/ フォルダがあればそこから、なければルートから）
    images_dir = input_path / "images"
    if not images_dir.exists():
        images_dir = input_path

    output_pdf_path = input_path / output_filename
    
    if not images_dir.exists():
        print(f"エラー: 画像ディレクトリが存在しません: {images_dir}")
        return

    # 画像ファイルの取得
    image_files = sorted([
        f for f in images_dir.glob("*") 
        if f.suffix.lower() in ['.png', '.jpg', '.jpeg']
        and not f.name.startswith(".")
    ])
    
    if not image_files:
        print(f"エラー: 画像ファイルが見つかりません: {images_dir}")
        return

    print("=" * 60)
    print(f"📚 軽量PDF作成ツール")
    print("=" * 60)
    print(f"入力ディレクトリ: {images_dir}")
    print(f"画像数: {len(image_files)}枚")
    print(f"画像処理: {colors}階調グレースケール")
    print("-" * 60)

    # 一時ディレクトリ
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 画像を処理してリストに保存
        processed_images = []
        
        print("変換処理を開始します...")
        
        for idx, img_path in enumerate(image_files, 1):
            try:
                with Image.open(img_path) as img:
                    # グレースケール & 減色
                    gray_img = img.convert('L')
                    quantized_img = gray_img.quantize(colors=colors, method=Image.Quantize.MAXCOVERAGE)
                    
                    # RGB変換（PDFはRGBが必要）
                    rgb_img = quantized_img.convert('RGB')
                    processed_images.append(rgb_img.copy())
                
                # 進捗表示
                if idx % 10 == 0 or idx == len(image_files):
                    print(f"  [{idx}/{len(image_files)}] 画像処理完了")

            except Exception as e:
                print(f"  ❌ エラー (Page {idx}): {e}")

        # PDFとして保存
        if processed_images:
            print("-" * 60)
            print(f"💾 PDF保存中...: {output_pdf_path.name}")
            processed_images[0].save(
                output_pdf_path,
                save_all=True,
                append_images=processed_images[1:],
                optimize=True
            )
            
            # サイズ確認
            if output_pdf_path.exists():
                size_mb = output_pdf_path.stat().st_size / (1024 * 1024)
                print(f"\n✅ 作成完了！")
                print(f"📁 出力ファイル: {output_pdf_path}")
                print(f"📊 ファイルサイズ: {size_mb:.1f} MB")
            else:
                print("❌ 保存に失敗しました。")
        else:
            print("❌ 処理可能な画像がありませんでした。")
            
    except Exception as e:
        print(f"\n❌ 重大なエラーが発生しました: {e}")
        if output_pdf_path.exists():
            output_pdf_path.unlink()
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="【Step 4】画像を16階調グレースケールに減色して軽量PDFを作成します"
    )
    parser.add_argument(
        "input_dir",
        help="画像ファイルが入っているディレクトリ",
    )
    parser.add_argument(
        "--output-filename",
        help="出力PDFファイル名（デフォルト: light_book.pdf）",
        default="light_book.pdf",
    )
    parser.add_argument(
        "--colors",
        help="減色数（デフォルト: 16）",
        type=int,
        default=16,
    )

    args = parser.parse_args()
    convert_images_to_pdf(args.input_dir, args.output_filename, args.colors)
