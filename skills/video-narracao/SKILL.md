---
name: video-narracao
description: Estilo de vídeo "Narração": uma voz narrando um roteiro sobre cenas de fundo tratadas, com zoom lento e a referência no topo (versículo, frase, curiosidade). Use para vídeos de reflexão, motivação ou curiosidade a partir de uma ideia.
---
# Narração

Requer **motor** + uma legenda + **roteiro** e **voz** (ou o áudio do usuário).

1. Ideia → `/roteiro` → o usuário escolhe → `roteiro.txt`.
2. `/voz` gera a narração (ou o usuário manda) → passos 1–3 do motor → `words.json`.
3. Fundo: o vídeo que o usuário mandar (ou cenas que ele indicar). Mais curto que a voz → repetir com `-stream_loop`.
   `node faixa.mjs fundo.mp4 ../projetos/X`.
4. `lado.json` com a legenda escolhida e `"referencia"` no topo quando houver (sempre completa: "Salmos 46:10", nunca só o capítulo;
   com número no começo, use `"refNumeros": "cheios"`).
5. Abertura forte: a primeira frase precisa aparecer escrita já no primeiro segundo.
6. Quadros de teste → render → música → post.
