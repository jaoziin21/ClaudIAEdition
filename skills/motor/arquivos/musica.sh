#!/usr/bin/env bash
# Põe música de fundo baixinha por baixo da voz (abaixa sozinha quando tem fala, sobe um pouco nas pausas).
# uso: bash musica.sh <video_final.mp4> <musica.(mp3|m4a|mp4)> <saida.mp4> [inicio_da_musica_s=0] [volume_db=-20] [fade_in_s=1.5]
# fade_in_s=0 → a música já começa TOCANDO no primeiro quadro (padrão: a música já está tocando no começo do vídeo;
# junto com inicio_da_musica_s pulando a entrada baixa da faixa).
# A música pode vir dentro de um vídeo (ex.: TikTok salvo) — só o áudio é usado. Repete se for mais curta que o vídeo.
set -e
V="$1"; M="$2"; O="$3"; SS="${4:-0}"; DB="${5:--20}"; FI="${6:-1.5}"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
FO=$(python3 -c "print(max(0,$DUR-2.5))")
FIN=$(python3 -c "print('afade=t=in:d=$FI,' if $FI>0 else '')")
ffmpeg -v error -y -nostdin -i "$V" -stream_loop -1 -ss "$SS" -i "$M" -filter_complex "\
[0:a]asplit[voz][sc];\
[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:$DUR,asetpts=PTS-STARTPTS,highpass=f=60,volume=${DB}dB,${FIN}afade=t=out:st=$FO:d=2.5[mus];\
[mus][sc]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=600:makeup=1[musd];\
[voz][musd]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart -t "$DUR" "$O"
echo "PRONTO $O"
