#!/usr/bin/env bash
# RENDER RÁPIDO da legenda dos versículos (vídeos longos): mesma aparência do render_legenda.mjs, ~10x mais rápido.
# Em vez de fotografar a tela inteira em todo quadro, fotografa cada palavra UMA vez (legenda_rapida/sprites.mjs) e monta os
# quadros em numpy/OpenCV (legenda_rapida/compor.py), que vão direto para o ffmpeg por cima do fundo. Conferido contra o motor
# antigo no vídeo do Judas: diferença média < 0,5/255 (invisível).
# uso (de dentro de motor/): OUTW=1920 OUTH=1080 BANDH=1080 SIZE=66 LEGX=.. LEGY=.. LEGW=.. MAXCH=56 RECORTE=x,y,w,h [LOOP=1]
#   [JOBS=4] [CRF=16] [ESCALA=1]  bash render_rapido.sh <words.json> <fundo.mp4> <audio> <saida.mp4> <dur_s>
# (sem "referencia" no topo — é para os vídeos longos horizontais; legenda.json ao lado do words.json como sempre)
set -e
W="$1"; B="$2"; A="$3"; O="$4"; DUR="$5"
JOBS="${JOBS:-$(nproc)}"; FPS=30; CRF="${CRF:-16}"; PX="${ESCALA:-1}"; PRESET="${PRESET:-veryfast}"   # veryfast = 2x o medium, mesma qualidade (SSIM 0,986)
[ -n "$RECORTE" ] || { echo "defina RECORTE=x,y,w,h (área da legenda)"; exit 1; }
IFS=, read RX RY RW RH <<< "$RECORTE"
BW=${OUTW:-1080}; BH=${BANDH:-608}; OH=${OUTH:-1920}; BY=$(( (OH-BH)/2 ))
D="${O%.*}_rapido"; mkdir -p "$D"; rm -f "$D"/s*.mp4.ok; t0=$(date +%s)
node render_legenda.mjs "$W" "$B" - - "$DUR" dados > "$D/linhas.txt"
# palavras já fotografadas com o mesmo texto/posição = reaproveita (refazer: apagar a pasta sprites)
if [ -f "$D/sprites/meta.json" ] && cmp -s "$D/linhas.txt" "$D/sprites/linhas.txt" && cmp -s legenda_data.js "$D/sprites/legenda_data.js"; then echo "palavras reaproveitadas"
else rm -rf "$D/sprites"; node legenda_rapida/sprites.mjs "$D/sprites" | tail -1; cp "$D/linhas.txt" legenda_data.js "$D/sprites/"; fi
TOT=$(python3 -c "print(round($DUR*$FPS))"); NF=0
[ -n "$LOOP" ] && NF=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$B")
PARTE=$(( (TOT+JOBS-1)/JOBS )); : > "$D/lista.txt"
for ((j=0;j<JOBS;j++)); do
  a=$((j*PARTE)); b=$(( (j+1)*PARTE )); ((b>TOT)) && b=$TOT; ((a>=b)) && continue
  p="$D/s$j.mp4"; echo "file 's$j.mp4'" >> "$D/lista.txt"
  if [ "$NF" -gt 0 ]; then BIN=(-stream_loop -1 -ss "$(python3 -c "print(($a % $NF)/$FPS)")" -i "$B"); else BIN=(-ss "$(python3 -c "print($a/$FPS)")" -i "$B"); fi
  TL=$(python3 -c "print(($b-$a)/$FPS)")
  ( python3 -I legenda_rapida/compor.py "$D/sprites" "$RECORTE" $a $b $FPS | ffmpeg -v error -y "${BIN[@]}" \
      -f rawvideo -pix_fmt rgba -s $((RW*PX))x$((RH*PX)) -r $FPS -i - \
      -filter_complex "[0:v]fps=$FPS,trim=0:$TL,setpts=PTS-STARTPTS,scale=$((BW*PX)):$((BH*PX))[b];[b][1:v]overlay=$((RX*PX)):$((RY*PX)):shortest=1,pad=$((BW*PX)):$((OH*PX)):0:$((BY*PX)):black,format=yuv420p[o]" \
      -map "[o]" -an -t "$TL" -c:v libx264 -preset $PRESET -crf $CRF -r $FPS "$p" && echo ok > "$p.ok" ) &
done
wait
for ((j=0;j<JOBS;j++)); do [ -f "$D/s$j.mp4" ] && { [ -s "$D/s$j.mp4.ok" ] || { echo "FALHOU parte $j"; exit 1; }; }; done
ffmpeg -v error -y -f concat -safe 0 -i "$D/lista.txt" -i "$A" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -af apad -t "$DUR" -movflags +faststart "$O"
echo "PRONTO $O em $(( ($(date +%s)-t0)/60 )) min $(( ($(date +%s)-t0)%60 )) s"
