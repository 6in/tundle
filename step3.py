#!/usr/bin/env python3
"""
KindleキャプチャのHTML変換結果を1つのPDFファイルとして出力
"""

import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter
import tempfile
import http.server
import socketserver
import threading
import time


def convert_html_to_pdf(input_dir, output_dir=None, output_filename="output.pdf", pages_per_file=None):
    """
    HTMLファイルを1つのPDFに結合して出力（オプションでページ分割）
    
    Args:
        input_dir: 入力HTMLディレクトリ
        output_dir: 出力PDFディレクトリ（省略時は input_dirの親ディレクトリ）
        output_filename: 出力PDFファイル名（デフォルト: output.pdf）
        pages_per_file: ページ分割数（Noneの場合は分割しない）
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"エラー: 入力ディレクトリが存在しません: {input_dir}")
        return
    
    # 出力ディレクトリの設定
    if output_dir is None:
        output_path = input_path.parent  # titleフォルダ直下に出力
    else:
        output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 絶対パスに変換
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    
    # HTMLファイルを取得
    html_files = sorted(input_path.glob("*.html"))
    
    if not html_files:
        print(f"エラー: HTMLファイルが見つかりません: {input_dir}")
        return
    
    print("=" * 60)
    print(f"📄 HTML → PDF変換（1ファイルに結合）")
    print("=" * 60)
    print(f"入力ディレクトリ: {input_path}")
    print(f"出力ディレクトリ: {output_path}")
    print(f"出力ファイル名: {output_filename}")
    print(f"処理対象ファイル数: {len(html_files)}ファイル")
    print()
    
    # HTTPサーバーを起動
    PORT = 0  # 0を指定すると自動的に空いているポートを使用
    server = None
    server_thread = None
    
    try:
        # サーバーハンドラーを作成（入力ディレクトリをルートとする）
        handler = http.server.SimpleHTTPRequestHandler
        
        # ディレクトリを変更してサーバー起動
        import os
        original_dir = os.getcwd()
        os.chdir(input_path)
        
        server = socketserver.TCPServer(("", PORT), handler)
        PORT = server.server_address[1]  # 実際に割り当てられたポート番号を取得
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        print(f"🌐 HTTPサーバー起動: http://localhost:{PORT}")
        time.sleep(1)  # サーバー起動を待機
        
        # 一時ディレクトリで個別PDFを作成
        temp_dir = Path(tempfile.mkdtemp())
        temp_pdfs = []
        
        # Playwrightでブラウザを起動
        with sync_playwright() as p:
            print("ブラウザを起動しています...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 2800, 'height': 4000})
            
            # ページ分割処理の初期化
            if pages_per_file is not None:
                print(f"\n{pages_per_file}ページごとに分割保存します")
                base_name = output_filename.rsplit('.', 1)[0]
                extension = output_filename.rsplit('.', 1)[1] if '.' in output_filename else 'pdf'
                file_count = 0
                merger = PdfWriter()
                output_files = []
            
            # 各HTMLをPDFに変換
            for idx, html_file in enumerate(html_files, 1):
                print(f"[{idx}/{len(html_files)}] 処理中: {html_file.name}")
                
                try:
                    # HTTPサーバー経由でアクセス
                    file_url = f"http://localhost:{PORT}/{html_file.name}"
                    page.goto(file_url, wait_until="networkidle")
                    
                    # 一時PDFファイルを生成
                    temp_pdf = temp_dir / f"{html_file.stem}.pdf"
                    temp_pdfs.append(temp_pdf)
                    
                    # PDFとして保存（A1サイズで1ページに収める）
                    page.pdf(
                        path=str(temp_pdf),
                        format="A1",
                        print_background=True,
                        margin={
                            "top": "10mm",
                            "bottom": "10mm",
                            "left": "10mm",
                            "right": "10mm"
                        }
                    )
                    
                    print(f"  ✓ 変換完了")
                    
                    # ページ分割処理：指定ページ数ごとにPDF保存
                    if pages_per_file is not None:
                        merger.append(str(temp_pdf))
                        current_pages = len(merger.pages)
                        
                        # 指定ページ数に達したら保存
                        if current_pages >= pages_per_file:
                            file_count += 1
                            output_pdf = output_path / f"{base_name}-{file_count:03d}.{extension}"
                            print(f"  💾 {current_pages}ページ分を保存中: {output_pdf.name}")
                            merger.write(str(output_pdf))
                            merger.close()
                            output_files.append(output_pdf)
                            print(f"  ✅ 保存完了: {output_pdf.name}")
                            
                            # 次のファイル用にリセット
                            merger = PdfWriter()
                    
                except Exception as e:
                    print(f"  ✗ エラー: {e}")
            
            # ページ分割処理：残りのページを保存
            if pages_per_file is not None and len(merger.pages) > 0:
                file_count += 1
                remaining_pages = len(merger.pages)
                output_pdf = output_path / f"{base_name}-{file_count:03d}.{extension}"
                print(f"\n💾 残り{remaining_pages}ページを保存中: {output_pdf.name}")
                merger.write(str(output_pdf))
                merger.close()
                output_files.append(output_pdf)
                print(f"✅ 保存完了: {output_pdf.name}")
            
            browser.close()
        
        # 分割なしの場合の結合処理
        if pages_per_file is None:
            print("\nPDFを結合しています...")
            merger = PdfWriter()
            
            for temp_pdf in temp_pdfs:
                if temp_pdf.exists():
                    merger.append(str(temp_pdf))
            
            # 結合したPDFを保存
            output_pdf = output_path / output_filename
            merger.write(str(output_pdf))
            merger.close()
            
            print("\n" + "=" * 60)
            print(f"✅ 変換完了: {len(html_files)}ファイルを結合")
            print(f"📁 出力先: {output_pdf}")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print(f"✅ 変換完了: {len(html_files)}ファイルを{file_count}個のPDFに分割")
            for output_pdf in output_files:
                print(f"📁 {output_pdf.name}")
            print("=" * 60)
        
        # 一時ファイルを削除
        for temp_pdf in temp_pdfs:
            if temp_pdf.exists():
                temp_pdf.unlink()
        temp_dir.rmdir()
        
    finally:
        # HTTPサーバーを停止
        if server:
            print("\n🛑 HTTPサーバーを停止しています...")
            server.shutdown()
            server.server_close()
        
        # 元のディレクトリに戻る
        os.chdir(original_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="KindleキャプチャのHTMLを1つのPDFに結合します",
        epilog="""
使用例:
  uv run python step3.py capture/test2/html
  uv run python step3.py capture/test2/html --output-dir /path/to/pdf --output-filename book.pdf
  uv run python step3.py capture/test2/html --pages-per-file 50 --output-filename book.pdf
        """
    )
    parser.add_argument(
        "input_dir",
        help="入力HTMLディレクトリ（例: capture/test2/html）",
    )
    parser.add_argument(
        "--output-dir",
        help="出力PDFディレクトリ（省略時は input_dirの親ディレクトリ）",
        default=None,
    )
    parser.add_argument(
        "--output-filename",
        help="出力PDFファイル名（デフォルト: output.pdf）",
        default="output.pdf",
    )
    parser.add_argument(
        "--pages-per-file",
        type=int,
        help="ページ分割数（省略時は分割しない）",
        default=None,
    )
    
    args = parser.parse_args()
    
    # 実行
    convert_html_to_pdf(args.input_dir, args.output_dir, args.output_filename, args.pages_per_file)
