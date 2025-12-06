#!/bin/sh
# $Source: /srv/368-pdf-utilities/30-source/RCS/368-021-driver-for-368-020.sh,v $
# $Date: 2025/12/06 04:48:58 $
# $Revision: 1.4 $
# $State: Exp $

#tag Number a PDF file - DRIVER for 368-020

# Driver for 368-020, providing the number of pages by inspecting the input file

echo "Usage: 368-021-driver-for-368-020 INFILE OUTFILE"


INPUT="$1"
OUTPUT="$2"
NUMPAGES=$(pdfinfo "$INPUT" |awk '/Pages:/{print $2}')

sh ./368-020-add-page-numbers-to-PDF.sh -i "$INPUT" -n "$NUMPAGES" -o "$OUTPUT"

