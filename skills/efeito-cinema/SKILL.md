---
name: efeito-cinema
description: Pacote de efeitos "cinema" (cinema + feixes + particulas): Cor de cinema (sombras azul-petróleo, luzes alaranjadas), feixes de luz quentes passando e poeira de luz — épico e limpo. Soma com qualquer legenda.
argument-hint: [legenda / vídeo ou pasta do projeto / observações]
---
# Efeito cinema

Cor de cinema (sombras azul-petróleo, luzes alaranjadas), feixes de luz quentes passando e poeira de luz — épico e limpo.
Partes: `cinema`, `feixes`, `particulas`. Requer a skill **motor** e uma skill de legenda.
Exemplo: `exemplo.jpg` (com legenda) e `exemplo-detalhe.jpg` (detalhe do efeito).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "cinema"`.
   Dá para somar outro pacote (`"pacote": ["cinema", "vhs"]`) ou efeitos avulsos (`"efeitos": [{"nome": "particulas", "forca": 0.5}]`).
2. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — os efeitos de IMAGEM do pacote substituem o filtro da legenda.
3. Render normal (`node render_lado.mjs ...`): os efeitos de TELA (luz, chuva, glitch...) entram sozinhos, atrás ou na frente da legenda.
4. Quadros de teste antes do vídeo inteiro.
