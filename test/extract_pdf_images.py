#!/usr/bin/env python3
"""
指定したPDFファイルから画像を抽出して保存するスクリプト
（pypdfを使用）
"""
import argparse
from pathlib import Path
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTImage, LTContainer
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice

def save_image(lt_image, output_dir, page_num):
    """保存処理（pdfminerのLTImageから）"""
    try:
        # streamからデータを取得
        # pdfminer.sixのバージョンによっては stream.get_data() だったり rawdata だったり複雑
        # ここでは rawdata を期待
        if hasattr(lt_image, 'stream'):
            stream = lt_image.stream
            data = stream.get_data()
            
            # 拡張子の推測（簡易）
            filters = stream.get_filters()
            ext = ".jpg"
            if filters and len(filters) > 0:
                f = str(filters[0]).upper()
                if "DCTDECODE" in f:
                    ext = ".jpg"
                elif "JPXDECODE" in f:
                    ext = ".jp2"
                elif "LZWDECODE" in f or "FLATEDECODE" in f:
                    ext = ".png" # 本当はheaderチェックなどが必要だが簡易的に
            
            # 画像名
            name = lt_image.name or f"img_{id(lt_image)}"
            filename = f"p{page_num:03d}_{name}{ext}"
            
            out_path = output_dir / filename
            with open(out_path, "wb") as fp:
                fp.write(data)
            
            print(f"  [{page_num}ページ] 保存: {filename} ({len(data)/1024:.1f} KB)")
            return len(data)
    except Exception as e:
        print(f"  ⚠️ 保存エラー {lt_image.name}: {e}")
    return 0

def find_images(element, output_dir, page_num, count_ref, size_ref):
    """再帰的に要素を探索"""
    if isinstance(element, LTImage):
        s = save_image(element, output_dir, page_num)
        if s > 0:
            count_ref[0] += 1
            size_ref[0] += s
    elif isinstance(element, LTContainer):
        for child in element:
            find_images(child, output_dir, page_num, count_ref, size_ref)

def extract_images_from_pdf(pdf_path):
    pdf_path = Path(pdf_path)
    output_dir = pdf_path.parent / f"{pdf_path.stem}_extracted_images_miner"
    output_dir.mkdir(exist_ok=True)
    
    print(f"🔍 PDFから画像を抽出します (via pdfminer): {pdf_path}")
    print(f"📂 出力先: {output_dir}")
    print("-" * 50)

    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    count = [0]
    total_size = [0]

    try:
        with open(pdf_path, 'rb') as fp:
            for i, page in enumerate(PDFPage.get_pages(fp), 1):
                interpreter.process_page(page)
                layout = device.get_result()
                find_images(layout, output_dir, i, count, total_size)
        
        print("-" * 50)
        print(f"✅ 抽出完了: {count[0]} 枚")
        print(f"📊 画像合計サイズ: {total_size[0] / 1024 / 1024:.2f} MB")

    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDFから画像を抽出します (pdfminer版)")
    parser.add_argument("pdf_path", help="PDFファイルのパス")
    args = parser.parse_args()
    
    # 存在チェック
    path = Path(args.pdf_path)
    if not path.exists():
        print(f"File not found: {path}")
        exit(1)
        
    extract_images_from_pdf(path)
