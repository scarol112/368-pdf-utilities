#!/usr/bin/env python3
"""
Renders an article JSON file (as produced by wn-scrape.py) into a
newspaper-style, 3-column, 9pt, letter-size PDF using headless Chrome.

Usage:
  .venv/bin/python wn-build_pdf.py output/article.json --out output/article.pdf

With no --out, the PDF is written alongside the input JSON, named with the
current date and time (YYYYMMDD-HHMMSS.pdf) so repeated runs don't clobber
each other.

--from TEXT / --to TEXT trim miscellania (nav, ads, "related articles",
etc.) that got scraped along with the real article. Output starts at the
beginning of the --from text and stops just before the --to text; either
can be omitted to leave that end untrimmed. Both match as a plain substring
against the scraped block text (see output/article.json).
"""

import argparse
import html
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime


def esc(s):
    return html.escape(s or "", quote=False)


def render_html(article):
    title = article.get("title") or "Untitled"
    byline = article.get("byline") or ""
    dateline = article.get("dateline") or ""
    url = article.get("url") or ""

    body_parts = []
    for b in article["blocks"]:
        tag = b.get("tag", "p")
        text = esc(b.get("text", ""))
        if not text:
            continue
        if tag in ("h2", "h3"):
            body_parts.append(f'<p class="subhead">{text}</p>')
        elif tag == "blockquote":
            body_parts.append(f'<p class="quote">{text}</p>')
        else:
            body_parts.append(f"<p>{text}</p>")
    body_html = "\n".join(body_parts)

    byline_row = ""
    if byline or dateline:
        byline_row = f"""
  <div class="byline-row">
    <span>{esc(byline)}</span>
    <span>{esc(dateline)}</span>
  </div>"""

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<style>
  @page {{ size: letter; margin: 0.5in 0.45in 0.6in 0.45in; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: Georgia, 'Times New Roman', Times, serif;
    font-size: 9pt;
    line-height: 1.32;
    color: #111;
    margin: 0;
  }}
  .masthead {{
    text-align: center;
    border-bottom: 3px double #111;
    padding-bottom: 4pt;
    margin-bottom: 6pt;
  }}
  .masthead .kicker {{
    font-family: 'Franklin Gothic Medium', Arial, sans-serif;
    font-size: 7pt;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 3pt;
  }}
  .masthead h1 {{
    font-size: 20pt;
    line-height: 1.15;
    margin: 0;
    font-weight: 700;
  }}
  .byline-row {{
    display: flex;
    justify-content: space-between;
    font-family: Arial, sans-serif;
    font-size: 7.5pt;
    color: #444;
    border-top: 1px solid #999;
    border-bottom: 1px solid #999;
    padding: 2pt 0;
    margin-bottom: 8pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .columns {{
    column-count: 3;
    column-gap: 0.28in;
    column-rule: 1px solid #ccc;
    text-align: justify;
    hyphens: auto;
    -webkit-hyphens: auto;
  }}
  p {{ margin: 0 0 6pt 0; text-indent: 10pt; }}
  p:first-of-type {{ text-indent: 0; }}
  p:first-of-type::first-letter {{
    font-size: 2.6em;
    font-weight: 700;
    float: left;
    line-height: 0.85;
    padding-right: 3pt;
    padding-top: 2pt;
  }}
  .subhead {{ font-weight: 700; text-indent: 0; margin-top: 4pt; }}
  .quote {{ font-style: italic; padding-left: 6pt; border-left: 2px solid #999; }}
  .source {{
    font-family: Arial, sans-serif;
    font-size: 6.5pt;
    color: #888;
    text-align: center;
    margin-top: 10pt;
  }}
</style>
</head>
<body>
  <div class="masthead">
    <div class="kicker">Web Clipping</div>
    <h1>{esc(title)}</h1>
  </div>{byline_row}
  <div class="columns">
{body_html}
  </div>
  <div class="source">{esc(url)}</div>
</body>
</html>
"""


def filter_blocks(blocks, from_text, to_text):
    """Trim blocks to the range [from_text, to_text), matched as substrings
    against block text, in document order. Either bound may be omitted."""
    if not from_text and not to_text:
        return blocks

    start_i, start_pos = 0, 0
    if from_text:
        for i, b in enumerate(blocks):
            pos = b["text"].find(from_text)
            if pos != -1:
                start_i, start_pos = i, pos
                break
        else:
            sys.exit(f"--from text {from_text!r} not found in any block of {len(blocks)}.")

    end_i, end_pos = len(blocks) - 1, None
    if to_text:
        for i in range(start_i, len(blocks)):
            search_from = start_pos if i == start_i else 0
            pos = blocks[i]["text"].find(to_text, search_from)
            if pos != -1:
                end_i, end_pos = i, pos
                break
        else:
            print(
                f"Warning: --to text {to_text!r} not found after --from -- "
                "keeping output through the end.",
                file=sys.stderr,
            )

    result = []
    for i in range(start_i, end_i + 1):
        text = blocks[i]["text"]
        if i == start_i and from_text:
            text = text[start_pos:]
        if end_pos is not None and i == end_i:
            cut = end_pos - start_pos if i == start_i and from_text else end_pos
            text = text[:cut]
        if text.strip():
            result.append({**blocks[i], "text": text})
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("article_json")
    ap.add_argument("--out", default=None, help="Output PDF path (default: <dir of input>/YYYYMMDD-HHMMSS.pdf)")
    ap.add_argument("--from", dest="from_text", default=None, metavar="TEXT",
                     help="Start output at the beginning of this text (substring match)")
    ap.add_argument("--to", dest="to_text", default=None, metavar="TEXT",
                     help="Stop output just before this text (substring match)")
    args = ap.parse_args()

    with open(args.article_json, encoding="utf-8") as f:
        article = json.load(f)

    article["blocks"] = filter_blocks(article["blocks"], args.from_text, args.to_text)
    if not article["blocks"]:
        sys.exit("--from/--to left no content to render.")

    if args.out:
        out_pdf = args.out
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_pdf = os.path.join(os.path.dirname(args.article_json) or ".", f"{stamp}.pdf")
    os.makedirs(os.path.dirname(out_pdf) or ".", exist_ok=True)

    doc = render_html(article)

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(doc)
        html_path = f.name

    try:
        result = subprocess.run(
            [
                "google-chrome", "--headless", "--disable-gpu", "--no-sandbox",
                f"--print-to-pdf={out_pdf}",
                "--no-pdf-header-footer",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=10000",
                f"file://{html_path}",
            ],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            sys.exit(f"Chrome PDF render failed:\n{result.stderr}")
    finally:
        os.unlink(html_path)

    print(f"Wrote {out_pdf}")


if __name__ == "__main__":
    main()
