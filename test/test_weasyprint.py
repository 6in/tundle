#!/usr/bin/env python3
"""
weasyprint でA1サイズのPDF生成テスト
"""
from pathlib import Path
import sys

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except ImportError:
    print("weasyprintがインストールされていません")
    print("インストール: uv pip install weasyprint")
    sys.exit(1)


def test_weasyprint_a1(html_path: Path, output_path: Path):
    """
    weasyprintでA1サイズのPDFを生成
    
    CSSで @page を使ってA1サイズを指定
    """
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
    
    # フォント設定
    font_config = FontConfiguration()
    
    # HTMLをPDFに変換
    html = HTML(filename=str(html_path))
    html.write_pdf(
        str(output_path),
        stylesheets=[css],
        font_config=font_config
    )
    
    print(f"✅ 変換完了: {output_path}")
    
    # ファイルサイズ確認
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"📊 ファイルサイズ: {size_mb:.2f} MB")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python test_weasyprint.py <htmlファイル> [出力PDF]")
        print("例: python test_weasyprint.py capture/tik-tok/html/001.html test_weasyprint_a1.pdf")
        sys.exit(1)
    
    html_path = Path(sys.argv[1])
    if not html_path.exists():
        print(f"エラー: {html_path} が見つかりません")
        sys.exit(1)
    
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("test_weasyprint_a1.pdf")
    
    test_weasyprint_a1(html_path, output_path)
