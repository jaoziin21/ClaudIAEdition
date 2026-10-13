#!/usr/bin/env bash
# Junta os trechos da vitrine: compilado com som (720x1280) + quadradinhos sem som para a galeria da página.
set -e
V="$(cd "$(dirname "$0")" && pwd)"; OUT="$V/../pag/vid"; mkdir -p "$OUT"
junta() {  # $1 = legendas|efeitos
  local L="$V/$1/lista.txt"; : > "$L"
  for d in $(ls -d "$V/$1"/s* | sort -V); do echo "file '$d/final.mp4'" >> "$L"; done
  ffmpeg -v error -y -f concat -safe 0 -i "$L" -vf "scale=720:1280:flags=lanczos,fps=30" -c:v libx264 -preset slow -b:v 1700k -maxrate 2400k -bufsize 4000k \
    -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart "$OUT/$1.mp4"
}
junta legendas; junta efeitos
# galeria: recorte da referência + telão (y 420..1340), 480 de largura, sem som
LEG=(street sample-yellow rocks samplerocks mistury dinamica invisible 3d-invisivel red-sharp)
EFE=(filme-antigo manga sonho vhs sombrio cinema rua)
for i in "${!LEG[@]}"; do ffmpeg -v error -y -i "$V/legendas/s$i/final.mp4" -an -vf "crop=1080:940:0:420,scale=480:-2" -c:v libx264 -crf 30 -preset slow -pix_fmt yuv420p -movflags +faststart "$OUT/t-${LEG[$i]}.mp4"; done
for i in "${!EFE[@]}"; do ffmpeg -v error -y -i "$V/efeitos/s$i/final.mp4" -an -vf "crop=1080:940:0:420,scale=480:-2" -c:v libx264 -crf 30 -preset slow -pix_fmt yuv420p -movflags +faststart "$OUT/t-${EFE[$i]}.mp4"; done
ls -la "$OUT"; du -sh "$OUT"
