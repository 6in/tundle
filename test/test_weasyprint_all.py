#!/usr/bin/env python3
"""
weasyprintで全HTMLをA1サイズのPDFに変換（ファイルサイズ検証用）
"""
from pathlib import Path
import sys
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


def generate_pdf_weasyprint(input_dir: Path, output_path: Path):
    """weasyprintで全HTMLをA1サイズの1つのPDFに結合"""
    html_files = sorted([f for f in input_dir.glob("*.html") if "index.html" not in f.name and "temp" not in f.name])
    if not html_files:
        print(f"HTMLファイルが見つかりません: {input_dir}")
        return

    # A1サイズのCSS定義
    css = CSS(string='''
        @page {
            size: A1;
            margin: 25mm;
        }
        body {
            font-family: "HeiseiMin-W3", "Hiragino Mincho ProN", serif;
            font-size: 10pt;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }
        table, th, td {
            border: 1px solid black;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
    ''')
    
    font_config = FontConfiguration()
    
    print(f"処理対象: {len(html_files)}ファイル")
    print()
    
    # 全HTMLを連結したHTMLを作成
    combined_html = "<html><body>"
    for i, html_path in enumerate(html_files, 1):
        print(f"[{i}/{len(html_files)}] 読み込み: {html_path.name}")
        content = html_path.read_text(encoding='utf-8', errors='ignore')
        combined_html += f'<div style="page-break-after: always;">{content}</div>'
    
    combined_html += "</body></html>"
    
    print("\nPDF生成中...")
    html = HTML(string=combined_html, base_url=str(input_dir))
    html.write_pdf(
        str(output_path),
        stylesheets=[css],
        font_config=font_config
    )
    
    print(f"✅ 変換完了: {output_path}")
    
    # ファイルサイズ確認
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"📊 ファイルサイズ: {size_mb:.2f} MB")
    print(f"📊 1ページあたり: {size_mb / len(html_files):.3f} MB ({size_mb * 1024 / len(html_files):.1f} KB)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python test_weasyprint_all.py <htmlフォルダ> [出力PDF]")
        print("例: python test_weasyprint_all.py capture/tik-tok/html test/weasyprint_all.pdf")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    if not input_dir.exists():
        print(f"エラー: {input_dir} が見つかりません")
        sys.exit(1)
    
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("test_weasyprint_all.pdf")
    
    generate_pdf_weasyprint(input_dir, output_path)
