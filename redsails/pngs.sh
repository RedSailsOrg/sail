rsvg-convert -w 256 -h 256 articles/static/icon.svg -o /pngs/icon.png
convert /pngs/icon.png -gravity center -background linen -extent 360x480 /pngs/tall.png
convert /pngs/icon.png -gravity center -background linen -extent 600x300 /pngs/social.png
convert /pngs/icon.png -gravity center -background black -extent 350x350 /pngs/icon-black.png
