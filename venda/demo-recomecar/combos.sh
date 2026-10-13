#!/usr/bin/env bash
# 3 combinações (legenda + fonte + efeitos) com a mesma narração (primeiros 9,2 s do demo).
set -e
S=/tmp/claude-0/-home-user/063bb3a9-aa90-5c57-a776-b32035416c1c/scratchpad; P=$S/demo; E=/home/user/getsemani---canal-/getsemani-videos/engine
DUR=9.2
python3 - <<EOF
import json
w=[x for x in json.load(open('$P/words.json')) if x['s']<$DUR-0.1]
cfgs={
 'A':{"estilo":"sample-yellow","trocaFonte":"pirata-one","pacote":["cinema","sonho"],"tamanho":60,"keywords":["Recomeçar"],"cenas":[{"t":0,"x":0.5,"y":0.86}]},
 'B':{"estilo":"red-sharp","pacote":["filme-antigo","vhs"],"keywords":["filme."],"cenas":[{"t":0,"x":0.5,"y":0.55}]},
 'C':{"estilo":"street","trocaFonte":{"CAP":"bebas-neue"},"pacote":["rua"],"efeitos":["flash"],"keywords":["Recomeçar","manhã."],"gritos":["Recomeçar","contas,"],"cenas":[{"t":0,"x":0.5,"y":0.5}]}}
import os
for k,c in cfgs.items():
    d=f'$P/combo{k}'; os.makedirs(d,exist_ok=True)
    json.dump(w,open(f'{d}/words.json','w'),ensure_ascii=False); json.dump(c,open(f'{d}/lado.json','w'),ensure_ascii=False)
EOF
for k in A B C; do ffmpeg -v error -y -t $DUR -i $P/audio.wav $P/combo$k/audio.wav; done
# fundos: A = Terra (NASA), B = Gulliver (1939, domínio público), C = anime
cp $P/fundo.mp4 $P/comboA/fundo.mp4
ffmpeg -v error -y -ss 3105 -t 10 -i $S/livres/gulliver.mp4 -an -vf "scale=1920:-2:flags=lanczos,crop=1920:1080,fps=30" -c:v libx264 -crf 17 -preset fast $P/comboB/fundo.mp4
ffmpeg -v error -y -ss 62 -t 10 -i /home/user/getsemani---canal-/getsemani-videos/entrada/eu-nao-tenho-inimigos-2s.mp4 -an -c:v libx264 -crf 17 -preset fast $P/comboC/fundo.mp4
cd $E
for k in A B C; do
  node faixa.mjs $P/combo$k/fundo.mp4 $P/combo$k $P/combo$k/faixa.mp4 0 $DUR >/dev/null
  node render_lado.mjs $P/combo$k $P/combo$k/faixa.mp4 $P/combo$k/audio.wav $P/combo$k/clip.mp4 $DUR > $P/combo$k/render.log 2>&1
  echo "combo $k ok"
done
