---
name: video-fala
description: Estilo de vídeo "Personagem falando": uma cena com o áudio original; transcreve, mapeia cada corte e coloca a legenda no espaço vazio ao lado de quem fala, nunca em cima do rosto. Use quando o usuário mandar um trecho de filme, anime, série ou entrevista para legendar.
---
# Personagem falando

Requer **motor** + uma legenda (Dinâmica, Sample Yellow, Samplerocks e Mistury combinam bem).

1. Vídeo do usuário em `entrada/`. Partes separadas → juntar com `concat` (com áudio) e conferir as emendas.
2. Áudio original: `audio.wav` com loudnorm −14. Transcrever (passo 3 do motor). Sem roteiro: escreva `roteiro.txt` a partir da
   transcrição, corrigindo nomes e palavras erradas, e só então alinhe.
3. Cortes de cena: `ffmpeg -i X -an -vf "fps=30,scale=480:-1,select='gt(scene,0.2)',metadata=print" -f null -` → tempos.
   Veja um quadro de cada cena (no recorte do telão, com grade) e escolha o espaço livre AO LADO de quem fala.
4. `lado.json`: uma cena por corte `{"t", "x", "y", "maxw"}` ou `{"t", "nada": true}`. Palavra falada bem no corte caindo no rosto →
   adiante o `t` da cena e use `"separa": true`.
5. Fundo com `node faixa.mjs`, quadros de teste (inclua quadros logo depois dos cortes) → render (o áudio é o original) → post.
