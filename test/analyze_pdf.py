#!/usr/bin/env python3
"""
PDFファイルの構成要素（画像、フォント、その他）のサイズ内訳を解析するスクリプト
"""
import sys
import argparse
from pathlib import Path
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTImage, LTTextBox, LTFigure

def analyze_pdf_structure(pdf_path):
    print(f"Analyzing: {pdf_path}")
    
    # 簡易的なストリーム解析（厳密なバイト数ではないが目安になる）
    font_size = 0
    image_size = 0
    text_content_length = 0
    other_size = 0
    
    try:
        with open(pdf_path, 'rb') as fp:
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            
            # オブジェクトレベルでの探索
            # xrefテーブルからオブジェクトを取得してタイプごとにサイズを集計
            
            for xref in doc.xrefs:
                for objid in xref.get_objids():
                    try:
                        obj = doc.getobj(objid)
                        
                        # ストリームオブジェクトの場合、その長さを取得
                        if hasattr(obj, 'attrs') and 'Length' in obj.attrs:
                            stream_len = obj.attrs['Length']
                            # 参照の場合は解決が必要だが、ここでは簡易的に扱う
                            if hasattr(stream_len, 'resolve'):
                                stream_len = stream_len.resolve()
                            
                            # タイプ判定
                            subtype = obj.attrs.get('Subtype', {}).name if 'Subtype' in obj.attrs else None
                            type_ = obj.attrs.get('Type', {}).name if 'Type' in obj.attrs else None
                            
                            if subtype == 'Image':
                                image_size += stream_len
                            elif subtype == 'Type1C' or subtype == 'CIDFontType0C' or type_ == 'Font':
                                font_size += stream_len
                            elif subtype == 'OpenType':  # OTF fonts
                                font_size += stream_len
                            elif type_ == 'FontDescriptor':
                                font_size += stream_len
                            else:
                                other_size += stream_len
                    except Exception:
                        pass

            total_estimated = font_size + image_size + other_size
            file_size = pdf_path.stat().st_size
            
            print("-" * 40)
            print(f"File Size (Actual):   {file_size / 1024:.2f} KB")
            print("-" * 40)
            print("Estimated Stream Content Breakdown:")
            print(f"  Images: {image_size / 1024:.2f} KB")
            print(f"  Fonts:  {font_size / 1024:.2f} KB (Approx. embedded font data)")
            print(f"  Other:  {other_size / 1024:.2f} KB (Text content, vector graphics, metadata)")
            print("-" * 40)
            
            if image_size > font_size and image_size > (file_size * 0.5):
                print(">> Main Report: This PDF is IMAGE-HEAVY.")
            elif font_size > image_size and font_size > (file_size * 0.3):
                print(">> Main Report: This PDF has significant FONT embedding overhead.")
            else:
                print(">> Main Report: Balanced or Text-heavy structure.")

    except Exception as e:
        print(f"Error analyzing PDF: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()
    
    path = Path(args.pdf_path)
    if path.exists():
        analyze_pdf_structure(path)
    else:
        print("File not found.")
