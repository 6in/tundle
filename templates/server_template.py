#!/usr/bin/env python3
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from html.parser import HTMLParser
import re

BASE_DIR = Path(__file__).parent.parent  # html/から親ディレクトリへ
HTML_DIR = BASE_DIR / "html"

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks = []

    def handle_data(self, data):
        if data:
            self._chunks.append(data)

    def get_text(self):
        return " ".join(self._chunks)

def extract_text_from_html_file(html_path):
    try:
        content = html_path.read_text(encoding="utf-8")
        parser = _TextExtractor()
        parser.feed(content)
        text = parser.get_text()
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception:
        return ""

def collect_pages(query=None):
    html_files = sorted([f for f in HTML_DIR.glob("*.html") if "temp" not in f.name and f.name != "index.html"])
    image_files = {img.stem: img for img in BASE_DIR.glob("*.png")} | {img.stem: img for img in BASE_DIR.glob("*.jpg")} | {img.stem: img for img in BASE_DIR.glob("*.jpeg")}

    pages = []
    q = (query or "").lower().strip()

    for html_path in html_files:
        stem = html_path.stem
        image_path = image_files.get(stem)
        image_rel = ""
        if image_path:
            image_rel = os.path.relpath(image_path, start=HTML_DIR).replace("\\", "/")

        label = stem
        try:
            label = f"Page {int(stem)}"
        except Exception:
            pass

        text = extract_text_from_html_file(html_path)
        if q and q not in text.lower() and q not in label.lower():
            continue

        pages.append({
            "html": os.path.relpath(html_path, start=HTML_DIR).replace("\\", "/"),
            "image": image_rel,
            "stem": stem,
            "label": label,
        })

    return pages

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/search":
            params = parse_qs(parsed.query)
            query = params.get("query", [""])[0]
            pages = collect_pages(query=query)
            payload = {"pages": pages}
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        return super().do_GET()

if __name__ == "__main__":
    os.chdir(BASE_DIR)
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("", port), Handler)
    print(f"Serving on http://localhost:{port}")
    print(f"Open: http://localhost:{port}/html/index.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
