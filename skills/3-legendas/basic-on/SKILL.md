---
name: basic-on
description: Legenda "Basic On": frase inteira de uma vez, corte seco, sem caixa — Helvetica Bold creme com sombra suave, centralizada abaixo do meio; em diálogo a 2ª pessoa sai em amarelo; crédito do filme embaixo à esquerda. Boa para cenas de filme/série com diálogo.
argument-hint: [vídeo ou pasta do projeto / quem fala quando / nome do filme / observações]
---
# Legenda Basic On

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `basic-on`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Pedaços de frase que entram INTEIROS no começo da fala e saem secos no fim — sem animação, sem caixa.
- Nimbus Sans Bold (cópia livre da Helvetica Bold; vem em `motor/fontes/nimbus-sans/`, licença AGPL com exceção para fontes — ver LICENSE)
  alargada e justa, creme com sombra suave, UMA linha centralizada um pouco abaixo do meio.
- DIÁLOGO: a fala da 2ª pessoa sai em AMARELO. Marcar no lado.json `"falantes": [[t0, t1], ...]` (trechos da 2ª pessoa)
  ou `"falante": 2` na cena. Ouvir o áudio para marcar certo. `"cor2": "#..."` troca o amarelo.
- Crédito opcional embaixo à esquerda: `"credito": {"titulo": "Nome do Filme (ano)", "sub": "@seucanal"}`.
- Imagem limpa e levemente quente.

## lado.json do projeto
```json
{"estilo": "basic-on", "falantes": [[5.8, 9.5]], "credito": {"titulo": "Nome do Filme (2008)", "sub": "@seucanal"},
 "cenas": [{"t": 0, "x": 0.5, "y": 0.72}]}
```

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X`.
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
