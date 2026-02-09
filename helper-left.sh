echo "Kindle Appをアクティブにしてください。"
sleep 3

./kindle-to-pdf.sh --crop-top 70 --crop-bottom 40 --crop-right 40 \
 --pages-per-file 500 \
 --wait 1.0 \
 --page-key left \
 --title "$1" \
 --pdf-filename "$1.pdf" \
 --max-pages $2
