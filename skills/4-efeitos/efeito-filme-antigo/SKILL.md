---
name: efeito-filme-antigo
description: Pacote de efeitos "filme-antigo" (super8 + sombra): Filme Super 8 escuro: cor quente saturada, sombras densas, grão forte, poeira, riscos, vazamento laranja nos cortes, janela de projetor arredondada. Soma com qualquer legenda.
argument-hint: [legenda / vídeo ou pasta do projeto / observações]
---
# Efeito filme-antigo

Filme Super 8 escuro: cor quente saturada, sombras densas, grão forte, poeira, riscos, vazamento laranja nos cortes, janela de projetor arredondada.
Partes: `super8`, `sombra`. Requer a skill **motor** e uma skill de legenda.
Exemplo: `exemplo.jpg` (com legenda) e `exemplo-detalhe.jpg` (detalhe do efeito).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "filme-antigo"`.
   Dá para somar outro pacote (`"pacote": ["filme-antigo", "vhs"]`) ou efeitos avulsos (`"efeitos": [{"nome": "particulas", "forca": 0.5}]`).
2. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — os efeitos de IMAGEM do pacote substituem o filtro da legenda.
3. Render normal (`node render_lado.mjs ...`): os efeitos de TELA (luz, chuva, glitch...) entram sozinhos, atrás ou na frente da legenda.
4. Quadros de teste antes do vídeo inteiro.
