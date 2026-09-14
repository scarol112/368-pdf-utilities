#!/usr/bin/env bash
# Re-renders the PDF from an existing article JSON WITHOUT re-scraping --
# safe to run after hand-editing output/article.json (or any other
# article JSON you point it at).
#
# Usage:
#   ./wn-rerender.sh                          # output/article.json -> output/YYYYMMDD-HHMMSS.pdf
#   ./wn-rerender.sh output/mine.json         # output/mine.json -> output/YYYYMMDD-HHMMSS.pdf
#   ./wn-rerender.sh output/mine.json output/mine.pdf   # explicit output path skips the timestamp
#   ./wn-rerender.sh output/mine.json --from "Once upon a time" --to "Related Articles"
#                                              # trim miscellania -- see wn-build_pdf.py --help

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IN="${1:-output/article.json}"
[ "$#" -gt 0 ] && shift

# A second positional (not starting with "-") is the legacy explicit OUT
# path; anything else (--from, --to, --out, ...) passes straight through
# to wn-build_pdf.py.
if [ "$#" -gt 0 ] && [[ "$1" != -* ]]; then
  OUT="$1"
  shift
  ./.venv/bin/python wn-build_pdf.py "$IN" --out "$OUT" "$@"
else
  ./.venv/bin/python wn-build_pdf.py "$IN" "$@"
fi
