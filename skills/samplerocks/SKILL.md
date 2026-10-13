---
name: samplerocks
description: Legenda "Samplerocks": layout inclinado do Rocks com letra sem serifa branca e palavras AMARELAS; cada palavra entra esticada da direita e encaixa; imagem limpa com grão. Boa para fala de personagem com visual limpo.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Samplerocks

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `samplerocks`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Versal Archivo 600 branca, 1–3 linhas curtas em escada, plano inclinado, sombra discreta.
- Palavras-chave AMARELAS; frase sem chave → última linha amarela.
- Cada palavra vem da direita esticada com rastro e encaixa; fim da frase = corte seco. Imagem limpa com grão fino.
- Posição: embaixo à esquerda (`x ≈ 0.33, y ≈ 0.76`).

## lado.json do projeto
```json
{"estilo": "samplerocks", "keywords": ["1 a 2 por frase"], "cenas": [{"t": 0, "x": 0.33, "y": 0.76}]}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
