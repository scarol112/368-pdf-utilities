# wn- : web-to-newspaper

Turn a logged-in web page into a newspaper-style, 3-column, 9pt, letter-size
PDF — without ever giving Claude (or any script) your password.

Part of `368-pdf-utilities`; namespaced with a `wn-` prefix (vs. the numbered
`368-NNN-*` page-numbering scripts) since it's a distinct feature with its
own dependencies. See [Location in this repo](#location-in-this-repo) below.

## For future Claude sessions

This section exists so you don't have to re-discover the following the hard
way — all of it came from actually building and testing this feature.

- **Environment**: runs under WSL2 with WSLg already configured (`DISPLAY=:0`,
  X socket present) — a headed `google-chrome` window genuinely renders here,
  no virtual display setup needed.
- **CDP origin allowlist is required**: recent Chrome rejects DevTools
  WebSocket connections from the `http://localhost:PORT` origin unless told
  otherwise. `wn-launch_chrome.sh` passes `--remote-allow-origins=*` for this
  reason — if you drop it, `wn-scrape.py` fails with
  `WebSocketBadStatusException: 403 Forbidden`.
- **`localhost` is ambiguous when more than one Chrome/CDP instance is
  running.** It can resolve to `127.0.0.1` or `::1` depending on resolver
  order, silently routing a request to the *wrong* browser instance. If
  you're testing while the user's own `wn-launch_chrome.sh` may already be
  running, query `127.0.0.1:PORT` explicitly and use a `--port` distinct
  from theirs.
- **Don't run two headed Chrome/CDP instances at once in this environment.**
  Observed directly during development: the second simultaneous instance
  accepts the CDP connection and reports `Page.frameStartedNavigating`, then
  the navigation silently stalls forever (no `Page.loadEventFired`, empty
  DOM) — a WSLg/resource-contention artifact, not a bug in these scripts. If
  an instance is already running (`pgrep -af remote-debugging-port`), test
  read-only against its already-loaded tab instead of launching a second one.
- **This repo dual-tracks files in RCS *and* git** (`30-source/RCS/*,v`
  alongside the working files). Existing convention: `ci -l -m"description"
  file` checks in a new revision and leaves the working file locked/writable.
  If you edit a `wn-*` file, check it in the same way afterward — don't
  leave RCS unaware of a change that's sitting in git.
- **Never let `chrome-profile/` or `output/`'s contents reach git.** The
  former holds live login session cookies; the latter often holds scraped,
  copyrighted third-party text. Both are gitignored already — keep it that
  way if you touch `.gitignore`.
- **This repo is public** (`github.com/scarol112/368-pdf-utilities`). Treat
  anything you'd hesitate to publish as something that must stay gitignored,
  not as "probably fine."

## Design

The core problem: scraping an authenticated page normally means handing over
a password, a session cookie, or an API token to whatever does the fetching.
This setup avoids that by never fetching the page itself — instead it drives
a **live, already-logged-in browser tab** and asks that tab to hand back the
text it's already rendered.

```
 ┌─────────────────────────────┐      CDP (localhost only)      ┌────────────────┐
 │ Chrome, launched by you      │◄───────────────────────────────┤ wn-scrape.py    │
 │ (wn-launch_chrome.sh)        │  Runtime.evaluate(extractJS)   │                 │
 │ - its own profile dir        │────────────────────────────────► writes         │
 │ - YOU log in here, by hand   │  {title, byline, blocks[]}     │ article.json    │
 └─────────────────────────────┘                                 └───────┬────────┘
                                                                          │
                                                                          ▼
                                                                  ┌────────────────┐
                                                                  │ wn-build_pdf.py │
                                                                  │ HTML+CSS        │
                                                                  │ (3-col, 9pt)    │
                                                                  │ → headless      │
                                                                  │   Chrome        │
                                                                  │   print-to-pdf  │
                                                                  └───────┬────────┘
                                                                          ▼
                                                                  output/article.pdf
```

Three pieces:

1. **`wn-launch_chrome.sh`** — starts a *separate, dedicated* Chrome instance
   with the DevTools Protocol (CDP) exposed on `localhost:9222`, using its
   own profile directory (`chrome-profile/`, isolated from your everyday
   Chrome profile). You log into whatever site you want in that window,
   by hand, exactly as you normally would (including 2FA, SSO, etc.). The
   password/session never leaves that browser process.

2. **`wn-scrape.py`** — connects to that Chrome instance over CDP (a local
   WebSocket on `localhost:9222`, not exposed off the machine) and tells the
   *already-open, already-authenticated tab* to run a small piece of
   JavaScript against its own DOM: pull `document.title`, a byline/date if
   present, and the text of every `<p>`/`<h2>`/`<h3>`/`<blockquote>` inside
   the page's `<article>` (or `<main>`, or `<body>` as a fallback). The
   result is written to `output/article.json`. This step never touches
   cookies, headers, or credentials directly — it only ever asks the tab
   "what does your rendered page say," the same as reading it over someone's
   shoulder.

3. **`wn-build_pdf.py`** — takes that JSON and renders it into an HTML page
   styled as a 3-column, 9pt, justified, letter-size newspaper layout
   (drop-cap lead, masthead, byline row, column rules, hyphenation), then
   shells out to headless Chrome's `--print-to-pdf` to produce
   `output/YYYYMMDD-HHMMSS.pdf` (timestamped so repeated runs don't clobber
   each other).

`wn-newspaper.sh` just chains steps 2 and 3. `wn-rerender.sh` re-runs just step 3
(useful after hand-editing `output/article.json` — see below).

### Why CDP instead of, say, exporting cookies to `curl`?

- Sites with SPA/JS-rendered content, session state held in memory, or bot
  checks on fresh requests often won't render correctly from a bare `curl`
  even with valid cookies. Reading the tab that's already rendered sidesteps
  all of that.
- It keeps the credential boundary crisp: the only thing that ever sees your
  password is the Chrome window you typed it into. Everything downstream
  only sees rendered text.
- The CDP port is bound to `localhost` — nothing off-machine can reach it.

### Known limitations

- This is a heuristic extractor, not Mozilla Readability. It works well on
  pages with a real `<article>`/`<main>` structure (most news sites, blogs).
  On pages without that structure it falls back to the whole `<body>`, which
  can pick up nav/boilerplate text. If a specific site scrapes badly, the
  fix is almost always adjusting the CSS selector in `EXTRACT_JS` inside
  `wn-scrape.py`.
- No image support — text only, matching the original newspaper-clipping
  use case.
- One article per run. For multiple tabs, run `wn-scrape.py` once per tab with
  `--tab-index` or `--url-contains`, into different `--out` paths.

## Location in this repo

These files live flat in `30-source/`, alongside the numbered `368-NNN-*.sh`
page-numbering scripts, distinguished by the `wn-` prefix rather than a
number — this feature is a different tool (Python + a live Chrome browser)
with its own setup step, not another entry in the pdftk/ghostscript-based
numbering sequence.

Not committed to git (see `.gitignore`): `.venv/` (recreate from
`wn-requirements.txt`), `chrome-profile/` (holds live session cookies —
never belongs in version control, especially a public repo), and the
contents of `output/` (your scraped articles/PDFs — personal output, and
often someone else's copyrighted text, not source).

## Setup

Create the virtualenv once (not tracked in git):

```bash
cd 30-source
python3 -m venv .venv
./.venv/bin/pip install -r wn-requirements.txt
```

## Usage

**1. Start the dedicated, CDP-enabled Chrome:**

```bash
./wn-launch_chrome.sh
```

This opens a visible Chrome window (uses WSLg, since this environment is
WSL2 with a Wayland/X display available). Leave it running in that terminal
— it stays in the foreground so you can see it print output/`Ctrl+C` to stop
it. Run the next steps from a *second* terminal.

**2. Log in, by hand, in that window.** Navigate to the page you want.
Leave the tab open.

**3. Scrape + build the PDF:**

```bash
./wn-newspaper.sh
```

If more than one tab is open, point it at the right one:

```bash
./wn-newspaper.sh --url-contains nytimes.com
# or
./.venv/bin/python wn-scrape.py --port 9222 --list          # see indices
./wn-newspaper.sh --tab-index 2
```

Output lands at `output/article.json` (the extracted text — handy to
sanity-check before/without rendering, overwritten each run — rename/move it
first if you want to keep a copy) and `output/YYYYMMDD-HHMMSS.pdf` (the final
newspaper layout, timestamped so successive runs never clobber each other's
PDF).

**4. When done, close the Chrome window** (or `Ctrl+C` the
`wn-launch_chrome.sh` terminal). Its profile directory (`chrome-profile/`,
created on first run) holds that session's cookies — delete it if you want
to fully log out / start clean next time:

```bash
rm -rf chrome-profile
```

## Running the two steps separately

```bash
./.venv/bin/python wn-scrape.py --port 9222 --url-contains example.com --out output/mine.json
./.venv/bin/python wn-build_pdf.py output/mine.json --out output/mine.pdf
```

## Hand-editing `article.json` before rendering

`output/article.json` is plain JSON — feel free to fix a mis-scraped title,
delete a boilerplate paragraph, reorder blocks, etc. before rendering. Once
edited, **don't rerun `wn-newspaper.sh`** — it always re-scrapes first and will
overwrite your edits. Instead, re-render just the PDF:

```bash
./wn-rerender.sh                          # output/article.json -> output/YYYYMMDD-HHMMSS.pdf
./wn-rerender.sh output/mine.json         # a differently-named article -> output/YYYYMMDD-HHMMSS.pdf
./wn-rerender.sh output/mine.json output/mine.pdf   # explicit output path skips the timestamp
```

`wn-rerender.sh` never touches Chrome or the network — it only reads the JSON
and re-runs `wn-build_pdf.py`, so it's safe to run repeatedly while you tweak
the file. It expects valid JSON (a stray trailing comma or unescaped quote
will throw a `json.decoder.JSONDecodeError`) in this shape:

```json
{
  "url": "...",
  "title": "...",
  "byline": "...",
  "dateline": "...",
  "blocks": [
    {"tag": "p", "text": "..."},
    {"tag": "h2", "text": "..."}
  ]
}
```

`tag` can be `p`, `h2`/`h3` (rendered as a bold subhead), or `blockquote`
(rendered italic with a left rule) — anything else falls through to a plain
paragraph.

## Files

| File               | Purpose                                             |
|--------------------|------------------------------------------------------|
| `wn-launch_chrome.sh` | Starts the CDP-enabled, isolated-profile Chrome      |
| `wn-scrape.py`        | Extracts article JSON from a live tab via CDP        |
| `wn-build_pdf.py`     | Renders article JSON → newspaper-style PDF           |
| `wn-newspaper.sh`     | Convenience wrapper: scrape then build               |
| `wn-rerender.sh`      | Re-renders the PDF from an existing (optionally hand-edited) article JSON, without re-scraping |
| `wn-requirements.txt` | Pip deps for `.venv/` (just `websocket-client`)      |
| `chrome-profile/`  | Created on first `wn-launch_chrome.sh` run; holds cookies/session for that dedicated browser instance — not your everyday Chrome profile. **Gitignored.** |
| `output/`          | Scraped JSON + generated PDFs land here. **Contents gitignored** — often someone else's copyrighted text. |
