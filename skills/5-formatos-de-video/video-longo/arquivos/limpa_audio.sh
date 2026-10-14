#!/usr/bin/env bash
# Limpa cada parte da voz (chiado de fundo, "s" estridente, graves inúteis) e iguala o volume (-16 LUFS cada, 2 passadas).
# uso: bash limpa_audio.sh entrada.wav saida.wav
set -e
F="highpass=f=60,afftdn=nr=18:nf=-50:tn=1,deesser=i=0.35:m=0.5:f=0.5,aresample=48000"
J=$(ffmpeg -nostdin -i "$1" -af "$F,loudnorm=I=-16:TP=-2:LRA=11:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -v error -y -nostdin -i "$1" -af "$F,loudnorm=I=-16:TP=-2:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" -ac 1 -c:a pcm_s24le "$2"
echo "PRONTO $2"
