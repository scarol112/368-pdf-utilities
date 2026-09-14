#!/usr/bin/env bash
# Convenience wrapper: scrape the current (or matching) tab from the
# running CDP Chrome instance, then render it straight to a newspaper PDF.
#
# Usage:
#   ./wn-newspaper.sh                          # only tab open, or prompts you to pick
#   ./wn-newspaper.sh --url-contains nytimes.com
#   ./wn-newspaper.sh --tab-index 2
#
# Output goes to output/article.json and output/article.pdf (timestamped
# copies are not made -- rename/move output/article.pdf if you want to
# keep it before running again).

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

./.venv/bin/python wn-scrape.py --out output/article.json "$@"
./.venv/bin/python wn-build_pdf.py output/article.json --out output/article.pdf
