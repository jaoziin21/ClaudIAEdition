---
name: efeito-manga
description: Pacote de efeitos "manga" (luz-quente + manga): Luz quente dourada + traço de tinta, retícula e hachura de mangá + feixes de luz + linhas de impacto nas palavras-chave. Soma com qualquer legenda.
argument-hint: [legenda / vídeo ou pasta do projeto / observações]
---
# Efeito manga

Luz quente dourada + traço de tinta, retícula e hachura de mangá + feixes de luz + linhas de impacto nas palavras-chave.
Partes: `luz-quente`, `manga`. Requer a skill **motor** e uma skill de legenda.
Exemplo: `exemplo.jpg` (com legenda) e `exemplo-detalhe.jpg` (detalhe do efeito).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "manga"`.
   Dá para somar outro pacote (`"pacote": ["manga", "vhs"]`) ou efeitos avulsos (`"efeitos": [{"nome": "particulas", "forca": 0.5}]`).
2. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — os efeitos de IMAGEM do pacote substituem o filtro da legenda.
3. Render normal (`node render_lado.mjs ...`): os efeitos de TELA (luz, chuva, glitch...) entram sozinhos, atrás ou na frente da legenda.
4. Quadros de teste antes do vídeo inteiro.
