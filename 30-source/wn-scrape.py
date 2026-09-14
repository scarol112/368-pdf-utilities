#!/usr/bin/env python3
"""
Connects to a running Chrome instance over the DevTools Protocol (CDP) and
extracts article-like content (title + paragraphs) from one of its open,
already-authenticated tabs. Does not touch cookies, passwords, or the
Chrome profile directly -- it only asks the live tab to run JavaScript
against its own already-rendered DOM.

Requires wn-launch_chrome.sh to be running (or any Chrome/Chromium started
with --remote-debugging-port), with the target page loaded and logged in.

Usage:
  .venv/bin/python wn-scrape.py --port 9222 --list
  .venv/bin/python wn-scrape.py --port 9222 --url-contains nytimes.com --out output/article.json
  .venv/bin/python wn-scrape.py --port 9222 --tab-index 0 --out output/article.json
"""

import argparse
import json
import sys
import urllib.request

import websocket  # from websocket-client

EXTRACT_JS = r"""
(() => {
  const clean = s => (s || '').replace(/[ \t\f\v]+/g, ' ').replace(/\n{2,}/g, '\n').trim();

  const root = document.querySelector('article')
    || document.querySelector('main')
    || document.body;

  const title = clean(document.title);

  let byline = '';
  const bylineEl = document.querySelector('[rel="author"], .byline, [itemprop="author"]');
  if (bylineEl) byline = clean(bylineEl.innerText);

  let dateline = '';
  const timeEl = document.querySelector('time[datetime], time');
  if (timeEl) dateline = clean(timeEl.innerText || timeEl.getAttribute('datetime') || '');

  const blocks = Array.from(root.querySelectorAll('p, h2, h3, blockquote'))
    .map(el => ({ tag: el.tagName.toLowerCase(), text: clean(el.innerText) }))
    .filter(b => b.text.length > 1);

  return JSON.stringify({
    url: location.href,
    title,
    byline,
    dateline,
    blocks,
  });
})()
"""


def get_tabs(port):
    with urllib.request.urlopen(f"http://localhost:{port}/json/list", timeout=5) as resp:
        return json.load(resp)


def pick_tab(tabs, args):
    pages = [t for t in tabs if t.get("type") == "page"]
    if not pages:
        sys.exit("No open page tabs found on that Chrome instance.")

    if args.tab_index is not None:
        if args.tab_index >= len(pages):
            sys.exit(f"--tab-index {args.tab_index} out of range (found {len(pages)} tabs).")
        return pages[args.tab_index]

    if args.url_contains:
        matches = [t for t in pages if args.url_contains in t.get("url", "")]
        if not matches:
            sys.exit(f"No open tab with URL containing {args.url_contains!r}.")
        return matches[0]

    if len(pages) == 1:
        return pages[0]

    print("Multiple tabs open -- which one do you want to render?")
    for i, t in enumerate(pages):
        print(f"  [{i}] {t.get('title', '')} -- {t.get('url', '')}")

    if not sys.stdin.isatty():
        sys.exit(
            "Not running interactively -- pass --tab-index or --url-contains to pick one."
        )

    while True:
        try:
            choice = input(f"Tab number [0-{len(pages) - 1}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nAborted.")
        if not choice.isdigit() or not (0 <= int(choice) < len(pages)):
            print(f"Enter a number between 0 and {len(pages) - 1}.")
            continue
        return pages[int(choice)]


def evaluate(ws_url, expression, timeout=15):
    ws = websocket.create_connection(ws_url, timeout=timeout)
    try:
        ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": expression, "returnByValue": True},
        }))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                result = msg.get("result", {}).get("result", {})
                if "value" not in result:
                    sys.exit(f"CDP evaluate failed: {json.dumps(msg)[:500]}")
                return result["value"]
    finally:
        ws.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=9222, help="CDP port (default 9222, matches launch_chrome.sh)")
    ap.add_argument("--list", action="store_true", help="List open tabs and exit")
    ap.add_argument("--tab-index", type=int, default=None, help="Pick tab by index from --list")
    ap.add_argument("--url-contains", default=None, help="Pick the first open tab whose URL contains this substring")
    ap.add_argument("--out", default="output/article.json", help="Where to write the extracted article JSON")
    args = ap.parse_args()

    try:
        tabs = get_tabs(args.port)
    except Exception as e:
        sys.exit(
            f"Could not reach Chrome DevTools on port {args.port}: {e}\n"
            "Is launch_chrome.sh running?"
        )

    pages = [t for t in tabs if t.get("type") == "page"]

    if args.list:
        for i, t in enumerate(pages):
            print(f"[{i}] {t.get('title', '')} -- {t.get('url', '')}")
        return

    tab = pick_tab(tabs, args)
    print(f"Extracting from: {tab.get('title', '')} -- {tab.get('url', '')}")

    raw = evaluate(tab["webSocketDebuggerUrl"], EXTRACT_JS)
    article = json.loads(raw)

    if not article["blocks"]:
        sys.exit("No paragraph-like content found on that page (unusual page structure?).")

    import os
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(article, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(article['blocks'])} blocks to {args.out}")


if __name__ == "__main__":
    main()
