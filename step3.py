#!/usr/bin/env python3
"""
POC: HTMLからテキストと画像を抽出し、1HTML=1ページのPDFを生成
- ページサイズ: A1
- テキストは上から流し込み
- 画像は上から順番に縦積み（重なりなし）
"""
import argparse
import base64
import io
import re
from pathlib import Path
from typing import List, Tuple

from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import ImageReader
from PIL import Image


def extract_text_and_images(html_path: Path) -> Tuple[str, List[Tuple[str, bytes]]]:
    """
    HTMLからテキストと画像データを抽出
    Returns:
        text: 抽出テキスト
        images: [(name, image_bytes)]
    """
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # script/styleは除去
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # 画像抽出
    images = []
    for idx, img in enumerate(soup.find_all("img"), 1):
        src = img.get("src")
        if not src:
            continue
        if src.startswith("data:"):
            # data URI
            match = re.match(r"data:(.*?);base64,(.*)", src, re.DOTALL)
            if not match:
                continue
            b64 = match.group(2)
            try:
                image_bytes = base64.b64decode(b64)
                images.append((f"data_{idx}", image_bytes))
            except Exception:
                continue
        else:
            # 相対パスの画像
            img_path = (html_path.parent / src).resolve()
            if img_path.exists():
                try:
                    images.append((img_path.name, img_path.read_bytes()))
                except Exception:
                    continue

    # テキスト抽出
    text = soup.get_text("\n")
    # 連続空白の整理
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    return text, images


def draw_wrapped_text(c, text: str, x: float, y: float, max_width: float, leading: float) -> float:
    """簡易的な折り返しでテキストを描画し、描画後のy座標を返す"""
    lines = []
    for raw_line in text.split("\n"):
        if not raw_line:
            lines.append("")
            continue
        line = ""
        for ch in raw_line:
            test = line + ch
            if pdfmetrics.stringWidth(test, "HeiseiMin-W3", 10) <= max_width:
                line = test
            else:
                lines.append(line)
                line = ch
        lines.append(line)

    for line in lines:
        if y < 20 * mm:
            break
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_images_stacked(c, images: List[Tuple[str, bytes]], x: float, y: float, max_width: float) -> float:
    """画像を上から順に縦積みで描画"""
    for name, data in images:
        if y < 30 * mm:
            break
        try:
            img = Image.open(io.BytesIO(data))
            w, h = img.size
            scale = min(1.0, max_width / w)
            draw_w = w * scale
            draw_h = h * scale
            
            if y - draw_h < 20 * mm:
                break

            c.drawImage(ImageReader(img), x, y - draw_h, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')
            y -= (draw_h + 8)
        except Exception:
            continue
    return y


def generate_pdf(input_dir: Path, output_path: Path, pages_per_file: int = None):
    html_files = sorted([f for f in input_dir.glob("*.html") if "index.html" not in f.name and "temp" not in f.name])
    if not html_files:
        print(f"HTMLファイルが見つかりません: {input_dir}")
        return

    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
    
    print("=" * 60)
    if pages_per_file:
        print(f"📄 HTML → PDF変換（{pages_per_file}ページごとに分割）")
    else:
        print(f"📄 HTML → PDF変換")
    print("=" * 60)
    print(f"処理対象ファイル数: {len(html_files)}ファイル")
    print()
    
    width, height = A1
    margin_x = 25 * mm
    margin_y = 25 * mm
    max_width = width - 2 * margin_x
    leading = 16
    
    output_files = []
    
    if pages_per_file is None:
        # 分割なし：1つのPDFに全て
        c = canvas.Canvas(str(output_path), pagesize=A1)
        for i, html_path in enumerate(html_files, 1):
            text, images = extract_text_and_images(html_path)
            c.setFont("HeiseiMin-W3", 10)

            y = height - margin_y
            if text:
                y = draw_wrapped_text(c, text, margin_x, y, max_width, leading)
                y -= 10
            if images:
                y = draw_images_stacked(c, images, margin_x, y, max_width)

            c.showPage()
            print(f"[{i}/{len(html_files)}] OK: {html_path.name}")

        c.save()
        print(f"\n✅ PDF作成完了: {output_path}")
        output_files.append(output_path)
    else:
        # 分割あり：pages_per_fileごとにPDFを分割
        base_name = output_path.stem
        output_dir = output_path.parent
        file_count = 0
        c = None
        page_count = 0
        
        for i, html_path in enumerate(html_files, 1):
            # 新しいファイルを開く
            if c is None:
                file_count += 1
                pdf_path = output_dir / f"{base_name}-{file_count:03d}.pdf"
                c = canvas.Canvas(str(pdf_path), pagesize=A1)
                page_count = 0
                print(f"\n📋 ファイル {file_count}: {pdf_path.name}")
            
            text, images = extract_text_and_images(html_path)
            c.setFont("HeiseiMin-W3", 10)

            y = height - margin_y
            if text:
                y = draw_wrapped_text(c, text, margin_x, y, max_width, leading)
                y -= 10
            if images:
                y = draw_images_stacked(c, images, margin_x, y, max_width)

            c.showPage()
            page_count += 1
            print(f"  [{i}/{len(html_files)}] ページ {page_count}: {html_path.name}")
            
            # pages_per_fileに達したら保存して次のファイルへ
            if page_count >= pages_per_file:
                c.save()
                print(f"  ✅ 保存: {pdf_path.name} ({page_count}ページ)")
                output_files.append(pdf_path)
                c = None
        
        # 残りのページを保存
        if c is not None:
            c.save()
            print(f"  ✅ 保存: {pdf_path.name} ({page_count}ページ)")
            output_files.append(pdf_path)
        
        print("\n" + "=" * 60)
        print(f"✅ PDF作成完了: {file_count}ファイル")
        for f in output_files:
            print(f"📁 {f.name}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="HTMLからテキスト/画像を抽出してPDFを生成")
    parser.add_argument("input_dir", help="HTMLフォルダ (例: capture/tik-tok/html)")
    parser.add_argument("--output", default=None, help="出力PDF (省略時: input_dir/../output.pdf)")
    parser.add_argument("--pages-per-file", type=int, default=None, help="ページ分割数（例: 50）")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"入力フォルダが存在しません: {input_dir}")
        return

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_dir.parent / "output.pdf"

    generate_pdf(input_dir, output_path, args.pages_per_file)


if __name__ == "__main__":
    main()
