---
name: legenda-3d-invisivel
description: Legenda "3D Invisível": uma palavra por vez no centro, letra grossa maiúscula (Montserrat Black) com relevo 3D, palavra-chave azul-gelo com linhas de impacto de mangá; imagem com luz quente e textura de mangá. Boa para frases curtas de impacto.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda 3D Invisível

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `3d-invisivel`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- UMA palavra por vez no centro, Montserrat Black maiúscula off-white com relevo 3D profundo; letras sobem em sequência e saem em dissolve.
- Palavra-chave azul-gelo com linhas de impacto de mangá (escolha as 5–6 palavras mais fortes do vídeo).
- Imagem com luz quente e textura de mangá (traço de tinta, retícula e hachura) — já vem no filtro do estilo.
- Cenas: todas `x: 0.5, y: 0.5` (os cortes servem só para a palavra sumir no corte).

## lado.json do projeto
```json
{"estilo": "3d-invisivel", "keywords": ["5 a 6 palavras fortes"], "cenas": [{"t": 0, "x": 0.5, "y": 0.5}]}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
