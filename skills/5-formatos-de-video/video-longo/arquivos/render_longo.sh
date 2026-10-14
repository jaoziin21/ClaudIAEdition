#!/usr/bin/env bash
# Render de vídeo LONGO (ex.: 11 min para YouTube) com a legenda do render_legenda.mjs, em trechos paralelos.
# uso (de dentro de motor/): [OUTW=1920 OUTH=1080 BANDH=1080 LEGY=.. SIZE=..] [JOBS=4] [TRECHO=60]
#   bash render_longo.sh <words.json> <fundo.mp4> <audio> <saida.mp4> <dur_s>
# Cada trecho (TRECHO s) vira um mp4 sem áudio em <saida>_partes/; no fim junta tudo sem reencodar e põe o áudio.
# Se cair no meio, rodar de novo: trechos já prontos são pulados.
set -e
W="$1"; B="$2"; A="$3"; O="$4"; DUR="$5"
JOBS="${JOBS:-$(( $(nproc) ))}"; TRECHO="${TRECHO:-60}"; FPS=30
D="${O%.*}_partes"; mkdir -p "$D"
node render_legenda.mjs "$W" "$B" - - "$DUR" dados > "$D/linhas.txt"
TOT=$(python3 -c "print(round($DUR*$FPS))"); PF=$((TRECHO*FPS)); N=$(( (TOT+PF-1)/PF ))
echo "$TOT quadros, $N trechos de ${TRECHO}s, $JOBS ao mesmo tempo"
: > "$D/lista.txt"
for ((i=0;i<N;i++)); do
  a=$((i*PF)); b=$(( (i+1)*PF )); ((b>TOT)) && b=$TOT
  p=$(printf "%s/p%03d.mp4" "$D" $i); echo "file '$(basename "$p")'" >> "$D/lista.txt"
  [ -s "$p.ok" ] && continue
  while (( $(jobs -rp | wc -l) >= JOBS )); do wait -n || true; done
  ( NODATA=1 FRAMES=$a:$b node render_legenda.mjs "$W" "$B" - "$p" "$DUR" > "$p.log" 2>&1 && echo ok > "$p.ok" && echo "trecho $i pronto" ) &
done
wait || true
for ((i=0;i<N;i++)); do [ -s "$(printf "%s/p%03d.mp4.ok" "$D" $i)" ] || { echo "FALHOU trecho $i (ver $D/p$(printf %03d $i).mp4.log)"; exit 1; }; done
ffmpeg -v error -y -f concat -safe 0 -i "$D/lista.txt" -i "$A" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -af apad -t "$DUR" -movflags +faststart "$O"
echo "PRONTO $O"
