#!/usr/bin/env bash
# Tempos das palavras para vídeo LONGO com o TEXTO do roteiro (roteiro.txt na pasta do projeto): corta o áudio em trechos curtos nas
# pausas (tempos certos), transcreve em PARTES PARALELAS e alinha com o roteiro (o texto do roteiro manda, a transcrição só dá os tempos).
# uso (de dentro de motor/): [PARTES=3] bash transcreve_longo.sh <pasta_projeto> <audio.wav>   → <pasta>/words.json
set -e
P="$1"; A="$2"; N="${PARTES:-3}"; t0=$(date +%s)
[ -f "$P/roteiro.txt" ] || { echo "falta $P/roteiro.txt (o texto do roteiro)"; exit 1; }
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$A")
ffmpeg -nostdin -i "$A" -af silencedetect=n=-38dB:d=0.18 -f null - 2>&1 | grep -o "silence_\(start\|end\): [0-9.]*" > "$P/silencios.txt"
python3 -I - "$P" "$DUR" "$N" <<'EOF'
import json, sys
P, DUR, N = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
s, st = [], None
for l in open(f'{P}/silencios.txt').read().split('\n'):
    if l.startswith('silence_start'): st = float(l.split()[1])
    elif l.startswith('silence_end') and st is not None: s.append((st, float(l.split()[1]))); st = None
mids = [(a + b) / 2 for a, b in s if (a + b) / 2 > 0.5]
cuts = [0.0]
for m in mids:   # trechos de 2,5–6 s cortados no meio das pausas
    if m - cuts[-1] >= 2.5:
        nxt = [x for x in mids if x > m]
        if not nxt or nxt[0] - cuts[-1] > 6: cuts.append(m)
cuts.append(DUR); clips = []
for a, b in zip(cuts, cuts[1:]):
    n = max(1, -(-int((b - a) * 100) // 700))
    clips += [[round(a + (b - a) * k / n, 2), round((b - a) / n, 2)] for k in range(n)]
for i in range(N): json.dump(clips[i::N], open(f'{P}/clips_{i}.json', 'w'))
print(len(clips), 'trechos em', N, 'partes')
EOF
for ((i=0;i<N;i++)); do node transcribe_clips.mjs "$A" "$P/clips_$i.json" "$P/clips_words_$i.json" > "$P/transcricao_$i.log" 2>&1 & done
wait
for ((i=0;i<N;i++)); do [ -s "$P/clips_words_$i.json" ] || { echo "FALHOU parte $i (ver $P/transcricao_$i.log)"; exit 1; }; done
python3 -I alinha.py "$P" $(for ((i=0;i<N;i++)); do echo "$P/clips_words_$i.json"; done) > "$P/alinha.log"
head -1 "$P/alinha.log"
echo "PRONTO $P/words.json em $(( ($(date +%s)-t0)/60 )) min $(( ($(date +%s)-t0)%60 )) s"
