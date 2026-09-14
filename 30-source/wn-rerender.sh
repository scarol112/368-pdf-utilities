#!/usr/bin/env bash
# Re-renders the PDF from an existing article JSON WITHOUT re-scraping --
# safe to run after hand-editing output/article.json (or any other
# article JSON you point it at).
#
# Usage:
#   ./wn-rerender.sh                          # output/article.json -> output/YYYYMMDD-HHMMSS.pdf
#   ./wn-rerender.sh output/mine.json         # output/mine.json -> output/YYYYMMDD-HHMMSS.pdf
#   ./wn-rerender.sh output/mine.json output/mine.pdf   # explicit output path skips the timestamp

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IN="${1:-output/article.json}"
OUT="${2:-}"

if [ -n "$OUT" ]; then
  ./.venv/bin/python wn-build_pdf.py "$IN" --out "$OUT"
else
  ./.venv/bin/python wn-build_pdf.py "$IN"
fi
