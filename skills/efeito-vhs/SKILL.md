---
name: efeito-vhs
description: Pacote de efeitos "vhs" (vhs + flash): Fita VHS: imagem macia, borda colorida, grão, varredura, faixa de tracking + clarão branco nos cortes. Soma com qualquer legenda.
argument-hint: [legenda / vídeo ou pasta do projeto / observações]
---
# Efeito vhs

Fita VHS: imagem macia, borda colorida, grão, varredura, faixa de tracking + clarão branco nos cortes.
Partes: `vhs`, `flash`. Requer a skill **motor** e uma skill de legenda.
Exemplo: `exemplo.jpg` (com legenda) e `exemplo-detalhe.jpg` (detalhe do efeito).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "vhs"`.
   Dá para somar outro pacote (`"pacote": ["vhs", "vhs"]`) ou efeitos avulsos (`"efeitos": [{"nome": "particulas", "forca": 0.5}]`).
2. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — os efeitos de IMAGEM do pacote substituem o filtro da legenda.
3. Render normal (`node render_lado.mjs ...`): os efeitos de TELA (luz, chuva, glitch...) entram sozinhos, atrás ou na frente da legenda.
4. Quadros de teste antes do vídeo inteiro.
