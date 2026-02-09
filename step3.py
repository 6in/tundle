#!/usr/bin/env python3
"""
HTMLをWeasyPrintでPDF化（A1サイズ）
- HTMLレイアウト（テーブル等）を保持
- 1HTML=1ページとして連結
"""
import argparse
from pathlib import Path
from typing import Iterable, List

from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration


def iter_html_files(input_dir: Path) -> List[Path]:
    return sorted([f for f in input_dir.glob("*.html") if "index.html" not in f.name and "temp" not in f.name])


def build_combined_html(html_files: Iterable[Path]) -> str:
    parts = ["<html><body>"]
    for html_path in html_files:
        content = html_path.read_text(encoding="utf-8", errors="ignore")
        parts.append(f'<div style="page-break-after: always;">{content}</div>')
    parts.append("</body></html>")
    return "".join(parts)


def get_default_css() -> CSS:
    return CSS(
        string="""
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
        """
    )


def write_pdf(html_string: str, base_url: str, output_path: Path) -> None:
    css = get_default_css()
    font_config = FontConfiguration()
    html = HTML(string=html_string, base_url=base_url)
    html.write_pdf(str(output_path), stylesheets=[css], font_config=font_config)


def generate_pdf(input_dir: Path, output_path: Path, pages_per_file: int = None):
    html_files = iter_html_files(input_dir)
    if not html_files:
        print(f"HTMLファイルが見つかりません: {input_dir}")
        return

    print("=" * 60)
    if pages_per_file:
        print(f"📄 HTML → PDF変換（{pages_per_file}ページごとに分割）")
    else:
        print("📄 HTML → PDF変換")
    print("=" * 60)
    print(f"処理対象ファイル数: {len(html_files)}ファイル")
    print()

    output_files: List[Path] = []

    if pages_per_file is None:
        combined_html = build_combined_html(html_files)
        write_pdf(combined_html, str(input_dir), output_path)
        print(f"✅ PDF作成完了: {output_path}")
        output_files.append(output_path)
    else:
        base_name = output_path.stem
        output_dir = output_path.parent
        file_count = 0

        for start in range(0, len(html_files), pages_per_file):
            chunk = html_files[start : start + pages_per_file]
            file_count += 1
            pdf_path = output_dir / f"{base_name}-{file_count:03d}.pdf"
            print(f"\n📋 ファイル {file_count}: {pdf_path.name}")

            combined_html = build_combined_html(chunk)
            write_pdf(combined_html, str(input_dir), pdf_path)
            print(f"  ✅ 保存: {pdf_path.name} ({len(chunk)}ページ)")
            output_files.append(pdf_path)

        print("\n" + "=" * 60)
        print(f"✅ PDF作成完了: {file_count}ファイル")
        for f in output_files:
            print(f"📁 {f.name}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="HTMLをWeasyPrintでPDFに変換")
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
