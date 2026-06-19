#!/usr/bin/env python3
"""
Extract clean plain-text content from all fetched raw files (JSON or HTML).
Saves cleaned text to /home/z/my-project/resources/synthesized/<slug>.txt
"""
import json
import re
from pathlib import Path
from html.parser import HTMLParser

RAW_DIR = Path("/home/z/my-project/resources/raw")
OUT_DIR = Path("/home/z/my-project/resources/synthesized")
OUT_DIR.mkdir(parents=True, exist_ok=True)


class TextExtractor(HTMLParser):
    """Convert HTML to text, preserving paragraph and line structure."""
    SKIP = {"script", "style", "noscript", "svg", "head", "nav", "footer", "header", "aside", "form"}
    BLOCK = {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "table", "section", "article"}

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1
        elif tag in self.BLOCK and self.parts:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip_depth > 0:
            self.skip_depth -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.skip_depth == 0:
            self.parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.parts)
        # Collapse whitespace but preserve paragraph breaks
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_text(html: str) -> str:
    p = TextExtractor()
    p.feed(html)
    return p.get_text()


def main():
    files = sorted([f for f in RAW_DIR.iterdir() if f.suffix in (".json", ".html") and f.name != "_manifest.json"])
    print(f"Processing {len(files)} raw files...")
    summary = []
    for f in files:
        out_name = f.stem + ".txt"
        out_path = OUT_DIR / out_name
        try:
            if f.suffix == ".json":
                data = json.load(open(f))
                # The web-reader returns {"data": {"title":..., "html":..., "text":..., "url":...}}
                d = data.get("data", data) if isinstance(data, dict) else {}
                title = d.get("title", "")
                url = d.get("url", "")
                html = d.get("html", "") or d.get("text", "")
                text = html_to_text(html) if html else ""
                content = f"URL: {url}\nTITLE: {title}\n\n{text}"
            else:
                # raw HTML from curl
                html = f.read_text(errors="ignore")
                # Try to extract title
                m = re.search(r"<title[^>]*>([^<]*)</title>", html, re.I)
                title = m.group(1).strip() if m else ""
                text = html_to_text(html)
                content = f"URL: (curl fetched)\nTITLE: {title}\n\n{text}"
            out_path.write_text(content, encoding="utf-8")
            summary.append((f.name, len(content)))
        except Exception as e:
            print(f"  ERROR {f.name}: {e}")
            summary.append((f.name, -1))

    print(f"\nExtracted {len(summary)} files:")
    for n, sz in summary:
        print(f"  {sz:>7} chars  {n}")


if __name__ == "__main__":
    main()
