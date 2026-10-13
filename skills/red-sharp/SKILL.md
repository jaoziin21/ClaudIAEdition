---
name: red-sharp
description: Legenda "Red Sharp": legenda pequena serifada numa tarja preta e, nas frases de impacto, palavras VERMELHAS empilhadas com a última em itálico, com soco, tremida e vinheta vermelha; imagem escura. Boa para motivação e frase forte.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Red Sharp

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `red-sharp`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Legenda normal: serifada (Tinos) branca minúscula numa tarja preta que cresce palavra por palavra, no centro.
- Frase com palavra-chave = IMPACTO: palavras VERMELHAS empilhadas (máx. 4 linhas), Montserrat Black, a última em Bodoni itálico maior; soco + tremida + vinheta vermelha.
- Use POUCAS palavras-chave (2 a 4 no vídeo), nas frases mais fortes e curtas. Imagem escura e dessaturada com grão.

## lado.json do projeto
```json
{"estilo": "red-sharp", "keywords": ["2 a 4 palavras das frases mais fortes"], "cenas": [{"t": 0, "x": 0.5, "y": 0.55}]}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
