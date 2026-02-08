#!/usr/bin/env python3
"""
YomiTokuを使用してKindleキャプチャ画像を1ページごとのHTMLファイルに変換
"""

import os
import glob
import argparse
import json
import re
import shutil
from pathlib import Path
from yomitoku import DocumentAnalyzer
from PIL import Image
import numpy as np
from html.parser import HTMLParser

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks = []

    def handle_data(self, data):
        if data:
            self._chunks.append(data)

    def get_text(self):
        return " ".join(self._chunks)

def extract_text_from_html_file(html_path, max_chars=None):
    try:
        content = html_path.read_text(encoding="utf-8")
        parser = _TextExtractor()
        parser.feed(content)
        text = parser.get_text()
        text = re.sub(r"\s+", " ", text).strip()
        if max_chars is not None and len(text) > max_chars:
            text = text[:max_chars]
        return text
    except Exception:
        return ""

def process_kindle_captures_to_html(input_dir, output_dir=None):
    """
    Kindleキャプチャ画像を1ページごとのHTMLファイルに変換
    
    Args:
        input_dir: 入力画像のディレクトリ
        output_dir: 出力ディレクトリ（指定なしの場合は input_dir/html を使用）
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"エラー: 入力ディレクトリが存在しません: {input_dir}")
        return
    
    # 出力ディレクトリの設定
    if output_dir is None:
        output_path = input_path / "html"
    else:
        output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 画像ファイルを取得（*.png, *.jpg, *.jpeg）
    # input_dir/images フォルダが存在する場合はそこから取得、なければ input_dir (後方互換)
    images_dir = input_path / "images"
    if not images_dir.exists():
        images_dir = input_path

    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        image_files.extend(sorted(images_dir.glob(ext)))
    
    if not image_files:
        print(f"エラー: 画像ファイルが見つかりません: {images_dir}")
        return
    
    print("=" * 60)
    print(f"📚 Kindleキャプチャ → HTML変換")
    print("=" * 60)
    print(f"入力ディレクトリ: {images_dir}")
    print(f"出力ディレクトリ: {output_path}")
    print(f"処理対象ファイル数: {len(image_files)}ファイル")
    print()
    
    # YomiTokuの初期化（Metal/MPS対応）
    print("YomiTokuを初期化しています...")
    try:
        # デバイスを自動選択（Metal が使えれば mps, なければ cpu）
        import torch
        if torch.backends.mps.is_available():
            device = "mps"
            print("  デバイス: Metal (GPU) 🚀")
        else:
            device = "cpu"
            print("  デバイス: CPU")
    except:
        device = "cpu"
        print("  デバイス: CPU")
    
    model = DocumentAnalyzer(device=device)
    print("✓ YomiToku準備完了\n")
    
    # リラン時処理：既存のHTMLから再開位置を特定
    # 最後に処理されたと思われるHTMLファイル（ファイル名順）を探す
    resume_target_stem = None
    existing_htmls = sorted([
        f for f in output_path.glob("*.html") 
        if "index.html" not in f.name and "temp" not in f.name
    ])
    
    if existing_htmls:
        last_html = existing_htmls[-1]
        resume_target_stem = last_html.stem
        print(f"🔄 既存の進行状況を検出: 最後のファイルは {last_html.name}")
        print(f"👉 {last_html.name} に対応する画像から処理を再開・再生成します。")
        print(f"   (それ以前のファイルはスキップされます)")
        print()

    # 各画像を処理
    for idx, image_file in enumerate(image_files, 1):
        # スキップ判定
        if resume_target_stem:
            # 現在の画像ファイル名(拡張子なし)が、最後に処理したファイルより辞書順で小さい場合はスキップ
            if image_file.stem < resume_target_stem:
                continue
        
        print(f"[{idx}/{len(image_files)}] 処理中: {image_file.name}")
        
        try:
            # 画像を読み込んでnumpy配列に変換
            image = Image.open(image_file)
            image_array = np.array(image)
            
            # 画像を解析（タプルの最初の要素がDocumentAnalyzerSchemaオブジェクト）
            result_tuple = model(image_array)
            result = result_tuple[0]
            
            # 一時ファイルにHTMLを出力
            temp_file = output_path / f"{image_file.stem}_temp.html"
            result.to_html(out_path=str(temp_file), img=image_array)
            
            # 一時ファイルを読み込んで、完全なHTMLとして再保存
            with open(temp_file, 'r', encoding='utf-8') as f:
                body_content = f.read()
            
            # 最終的なHTMLファイルを生成
            output_file = output_path / f"{image_file.stem}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('<!DOCTYPE html>\n')
                f.write('<html lang="ja">\n')
                f.write('<head>\n')
                f.write('  <meta charset="UTF-8">\n')
                f.write('  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
                f.write(f'  <title>Kindle - {image_file.stem}</title>\n')
                f.write('  <script src="https://cdn.tailwindcss.com"></script>\n')
                f.write('  <style>\n')
                f.write('    body { font-family: "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif; }\n')
                f.write('  </style>\n')
                f.write('</head>\n')
                f.write('<body class="bg-gradient-to-br from-slate-50 to-slate-100 min-h-screen py-8">\n')
                f.write('  <div class="max-w-4xl mx-auto px-4">\n')
                f.write('    <div class="bg-white rounded-xl shadow-lg p-8 mb-4">\n')
                f.write('      <div class="prose prose-slate max-w-none">\n')
                # body_contentのdivタグを処理してTailwindクラスを追加
                styled_content = body_content.replace('<div>', '', 1).replace('</div>', '', 1)
                styled_content = styled_content.replace('<h1>', '<h1 class="text-2xl font-bold text-slate-800 mt-8 mb-4 pb-2 border-b-2 border-blue-500">')
                styled_content = styled_content.replace('<p>', '<p class="text-slate-700 leading-relaxed mb-3">')
                styled_content = styled_content.replace('<table', '<div class="overflow-x-auto my-6"><table class="min-w-full border border-slate-300 rounded-lg overflow-hidden"')
                styled_content = styled_content.replace('</table>', '</table></div>')
                styled_content = styled_content.replace('<td', '<td class="border border-slate-300 px-4 py-3 text-sm"')
                styled_content = styled_content.replace('<th', '<th class="border border-slate-300 px-4 py-3 text-sm font-semibold bg-slate-100"')
                styled_content = styled_content.replace('<img ', '<img class="rounded-lg shadow-md my-4 mx-auto" ')
                f.write(styled_content)
                f.write('      </div>\n')
                f.write('    </div>\n')
                f.write('  </div>\n')
                f.write('</body>\n')
                f.write('</html>\n')
            
            # 一時ファイルを削除
            temp_file.unlink()
            
            print(f"  ✓ 保存完了: {output_file.name}")
            
        except Exception as e:
            print(f"  ✗ エラー: {e}")
            
    # index.htmlを生成
    html_files = sorted([f.name for f in output_path.glob("*.html") if "temp" not in f.name and f.name != "index.html"])

    if html_files:
        index_file = output_path / "index.html"
        template_src = Path(__file__).parent / "templates" / "index_template.html"
        template_dst = output_path / "index.template.html"
        server_src = Path(__file__).parent / "templates" / "server_template.py"
        server_dst = output_path / "server.py"
        print(f"\n📑 index.htmlを生成しています...")

        if not template_src.exists():
            print(f"  ✗ テンプレートが見つかりません: {template_src}")
        else:
            shutil.copyfile(template_src, template_dst)
            template = template_dst.read_text(encoding="utf-8")
            rendered = template.replace("__TOTAL_PAGES__", str(len(html_files)))
            index_file.write_text(rendered, encoding="utf-8")
            print(f"  ✓ index.html生成完了: {index_file}")
            print(f"  ✓ テンプレート配置: {template_dst}")

        if not server_src.exists():
            print(f"  ✗ サーバーテンプレートが見つかりません: {server_src}")
        else:
            shutil.copyfile(server_src, server_dst)
            print(f"  ✓ server.py配置: {server_dst}")
    
    print("\n" + "=" * 60)
    print(f"✅ 変換完了: {len(image_files)}ファイル")
    print(f"📁 出力先: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="YomiTokuを使用してKindleキャプチャ画像をHTMLに変換します"
    )
    parser.add_argument(
        "input_dir",
        help="入力ディレクトリ（例: capture/20260207181042）",
    )
    parser.add_argument(
        "--output-dir",
        help="出力ディレクトリ（省略時は input_dir/html）",
        default=None,
    )

    args = parser.parse_args()

    # 実行
    process_kindle_captures_to_html(args.input_dir, args.output_dir)
