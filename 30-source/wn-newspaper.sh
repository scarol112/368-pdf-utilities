#!/usr/bin/env bash
# Convenience wrapper: scrape the current (or matching) tab from the
# running CDP Chrome instance, then render it straight to a newspaper PDF.
#
# Usage:
#   ./wn-newspaper.sh                          # only tab open, or prompts you to pick
#   ./wn-newspaper.sh --url-contains nytimes.com
#   ./wn-newspaper.sh --tab-index 2
#   ./wn-newspaper.sh --from "Once upon a time" --to "Related Articles"
#                                              # trim miscellania -- see wn-build_pdf.py --help
#
# --tab-index/--url-contains/--port/--list go to wn-scrape.py; --from/--to
# go to wn-build_pdf.py; any of these can be combined in one call.
#
# Output goes to output/article.json (each run overwrites it -- rename/move
# it first if you want to keep a copy) and output/YYYYMMDD-HHMMSS.pdf (each
# run gets its own timestamped filename, so PDFs never clobber each other).

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SCRAPE_ARGS=()
BUILD_ARGS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --from|--to)
      BUILD_ARGS+=("$1" "$2")
      shift 2
      ;;
    --from=*|--to=*)
      BUILD_ARGS+=("$1")
      shift
      ;;
    *)
      SCRAPE_ARGS+=("$1")
      shift
      ;;
  esac
done

./.venv/bin/python wn-scrape.py --out output/article.json "${SCRAPE_ARGS[@]}"
./.venv/bin/python wn-build_pdf.py output/article.json "${BUILD_ARGS[@]}"
