---
name: bruce
description: Legenda "Bruce": 1–2 palavras por vez em maiúsculas serifadas pequenas e espaçadas, ao lado de quem fala; cada palavra surge desfocada → nítida, o bloco desliza devagar e sai seco; imagem escura, dessaturada e verde-azulada (cara de filme do Batman). Boa para falas sérias e motivacionais.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Bruce

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `bruce`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Blocos de 1–2 palavras, Tinos (= Times) em MAIÚSCULAS, pequena e espaçada, branca com sombra discreta.
- A 1ª palavra entra; a 2ª entra à direita dela. Cada palavra surge em 3 quadros (cinza e desfocada → branca e nítida).
- O bloco desliza devagar (o lado alterna a cada bloco) e sai seco. Palavra-chave (poucas): um pouco mais clara com brilho leve.
- Imagem escura, com contraste, pouca cor, verde-azulada, grão e vinheta.

## POSIÇÃO (o mais importante)
AO LADO de quem fala, na altura da cabeça/ombro, no espaço vazio. Cada cena tem o seu `x,y`:
rosto à esquerda → `x: 0.68`; rosto à direita → `x: 0.32`; `y` entre 0.3 e 0.45. Conferir nos quadros de teste: nunca em cima do rosto.

## lado.json do projeto
```json
{"estilo": "bruce", "cenas": [{"t": 0, "x": 0.68, "y": 0.38}, {"t": 4.2, "x": 0.3, "y": 0.4}]}
```

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X`; ver em que lado está o rosto em cada cena.
3. `lado.json` com o x,y de cada cena → quadros de teste (posição!) → mandar → ajustar → render → música → `final_envio.mp4`.
