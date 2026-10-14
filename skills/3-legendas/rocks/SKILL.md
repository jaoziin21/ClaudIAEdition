---
name: rocks
description: Legenda "Rocks": maiúsculas serifadas brancas com relevo cromado e brilho, num plano inclinado, em duas linhas encaixadas em escada, capitular gigante, risco de luz em cada palavra; vídeo com cara de fita VHS. Boa para épico e retrô.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Rocks

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `rocks`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Frases curtas (`maxch` 22) em VERSAL serifada (Tinos) branca com relevo cromado escuro e brilho, num plano inclinado.
- 2 linhas em escada; a palavra-chave (ou a mais longa) fica maior. Frase que começa com letra solta (A, E, O, É) vira capitular gigante.
- Cada palavra entra com risco de luz; fim da frase = corte seco. Vídeo VHS (macio, borda colorida, grão, varredura, tracking nos cortes).
- Posição: embaixo à esquerda (`x ≈ 0.32, y ≈ 0.76`), variando quando o espaço pedir.

## lado.json do projeto
```json
{"estilo": "rocks", "keywords": [...], "cenas": [{"t": 0, "x": 0.32, "y": 0.76}]}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
