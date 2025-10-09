#!/bin/sh
# $Source: /srv/368-pdf-utilities/30-source/RCS/368-010-add-page-numbers.sh,v $
# $Date: 2025/10/09 17:17:53 $
# $Revision: 1.1 $
# $State: Exp $

case "$1" in
    ""|"-h") echo "\nAdd page numbers to an existing PDF by overlaying"
	     echo "another PDF page by page."
	     echo "\nUsage:"
	     echo '386-040... INPUFILE OVERLAYFILE|"default" [OUTPUTFILE]'
	     echo 'if "default" is specified a default will be usedi as the overlay.'
	     echo 'if the OUTPUTFILE is unspecified, "numbered.pdf" will be used.\n'
	     exit
esac

echo "[green]Not help text" | rich -p -


NUMBERSFILE="blank-numbered-20pp.pdf"
OUTPUTFILE="numbered.pdf"

echo "-----------------------------"
echo "\$1 = $1, \$2 = $2, \$3 = $3"
echo "-----------------------------"

if [ "$2" != "default" ]; then
	NUMBERSFILE="$2"
fi

if [ "$3" != "" ]; then
	OUTPUTFILE="$3"
fi

pdftk "$1" multistamp "$NUMBERSFILE" output "$OUTPUTFILE"

#end
