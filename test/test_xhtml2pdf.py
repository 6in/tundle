#!/usr/bin/env python3
"""
xhtml2pdf でA1サイズのPDF生成テスト（システム依存なし）
"""
from pathlib import Path
import sys

try:
    from xhtml2pdf import pisa
except ImportError:
    print("xhtml2pdfがインストールされていません")
    print("インストール: uv pip install xhtml2pdf")
    sys.exit(1)


def test_xhtml2pdf_a1(html_path: Path, output_path: Path):
    """
    xhtml2pdfでA1サイズのPDFを生成
    """
    # HTMLを読み込み
    html_content = html_path.read_text(encoding='utf-8', errors='ignore')
    
    # A1サイズのスタイル追加（595pt × 842pt が A1）
    # A1 = 1684pt × 2384pt
    styled_html = f'''
    <html>
    <head>
        <style>
            @page {{
                size: 1684pt 2384pt;
                margin: 25mm;
            }}
            body {{
                font-family: sans-serif;
                font-size: 10pt;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 10px 0;
            }}
            table, th, td {{
                border: 1px solid black;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    '''
    
    # PDFに変換
    with open(output_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(styled_html, dest=pdf_file)
    
    if pisa_status.err:
        print(f"❌ エラー: PDF生成に失敗しました")
        return False
    
    print(f"✅ 変換完了: {output_path}")
    
    # ファイルサイズ確認
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"📊 ファイルサイズ: {size_mb:.2f} MB")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python test_xhtml2pdf.py <htmlファイル> [出力PDF]")
        print("例: python test_xhtml2pdf.py capture/tik-tok/html/001.html test_xhtml2pdf_a1.pdf")
        sys.exit(1)
    
    html_path = Path(sys.argv[1])
    if not html_path.exists():
        print(f"エラー: {html_path} が見つかりません")
        sys.exit(1)
    
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("test_xhtml2pdf_a1.pdf")
    
    test_xhtml2pdf_a1(html_path, output_path)
