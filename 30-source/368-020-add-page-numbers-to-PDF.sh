#!/bin/sh
# $Source: /srv/368-pdf-utilities/30-source/RCS/368-020-add-page-numbers-to-PDF.sh,v $
# $Date: 2025/12/06 04:48:58 $
# $Revision: 1.4 $
# $State: Exp $

#tag Number a pdf file - driver is 368-021

# original created by Anthopic Claude 20251010

show_help() {
cat << EOF
Usage: $(basename "$0") -n NUMPAGES -i INPUT.pdf -o OUTPUT.pdf

Overlay page numbers at the bottom center of a PDF.

Options:
  -h          Show this help message
  -n NUMPAGES Number of pages to number (required)
  -i INPUT    Input PDF file (required)
  -o OUTPUT   Output PDF file (required)
  -s SKIP     (tbd) Number of pages to skip before numbering

Requirements:
  - ghostscript (gs command)
  - pdftk

Example:
  $(basename "$0") -n 25  -s 1 -i document.pdf -o numbered.pdf
EOF
}


echo "\n[green] cmd line options: $@" | rich -p -


# Initialize variables
NUMPAGES=""
INPUT=""
OUTPUT=""
SKIP=0

# Parse arguments
while getopts "hn:i:o:s:" opt; do
  case $opt in
    h) show_help; exit 0 ;;
    n) NUMPAGES="$OPTARG" ;;
    i) INPUT="$OPTARG" ;;
    o) OUTPUT="$OPTARG" ;;
    s) SKIP="$OPTARG" ;;
    *) show_help; exit 1 ;;
  esac
done

# Validate required arguments
if [ -z "$NUMPAGES" ] || [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
  echo "Error: Missing required arguments" >&2
  show_help
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "Error: Input file '$INPUT' not found" >&2
  exit 1
fi

SKIPTO=$((SKIP + 1 ))

# Create temporary PostScript file
TMPPS=$(mktemp /tmp/pagenums.XXXXXX.ps)
TMPPDF=$(mktemp /tmp/pagenums.XXXXXX.pdf)

cat > "$TMPPS" << 'EOF'
/Arial findfont 12 scalefont setfont

1 1 NUMPAGES {
  /pagenum exch def
  << /PageSize [612 792] >> setpagedevice
  306 20 moveto
  pagenum =string cvs dup stringwidth pop 2 div neg 0 rmoveto show
  showpage
} for
EOF

# Substitute NUMPAGES value
sed -i.bak "s/NUMPAGES/$NUMPAGES/" "$TMPPS"
# sed -i.bak "s/SKIPTO/$SKIPTO/" "$TMPPS"

# Convert PostScript to PDF
gs -dBATCH -dNOPAUSE -dQUIET -sDEVICE=pdfwrite -sOutputFile="$TMPPDF" "$TMPPS"

# Overlay page numbers
pdftk "$INPUT" multistamp "$TMPPDF" output "$OUTPUT"

# Cleanup
rm -f "$TMPPS" "$TMPPS.bak" "$TMPPDF"

echo "Page numbers added: $OUTPUT"

