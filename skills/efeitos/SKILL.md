---
name: efeitos
description: Índice dos pacotes de efeitos instalados: mostra cada um com a imagem de referência, aplica um ou mais junto com qualquer legenda e também mistura duas legendas no mesmo vídeo.
---
# Efeitos (índice)

1. Liste os pacotes instalados: pastas `.claude/skills/efeito-*` (cada uma tem `exemplo.jpg` e o SKILL.md com a descrição).
   Mostre ao usuário o nome, a descrição e a imagem de cada um.
2. Aplique o que ele escolher no `lado.json`: `"pacote": "sonho"` ou vários `"pacote": ["sonho", "vhs"]`;
   efeitos avulsos com força: `"efeitos": [{"nome": "flash"}, {"nome": "particulas", "forca": 0.5}]`
   (lista completa em `motor/efeitos/efeitos.json`; só funcionam os que têm os arquivos instalados).
3. Duas legendas no mesmo vídeo: a legenda principal em `"estilo"` e, na cena da frase de impacto, `"estilo": "red-sharp"`
   (as duas skills de legenda precisam estar instaladas).
4. Fundo com `node faixa.mjs`, quadros de teste, render. Detalhes na skill **motor**.
