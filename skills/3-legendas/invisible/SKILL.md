---
name: invisible
description: Legenda "Invisible": a letra é feita da própria imagem do vídeo, como vidro, e pega sozinha as cores de cada cena; maiúscula grossa (Montserrat Black) no centro com relevo. Boa para visual estético e frases curtas.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Invisible

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `invisible`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- O motor tira os quadros do vídeo em meia resolução (pasta `motor/quadros/`, refeita só se a faixa mudar) e desenha a face de cada letra com o quadro atual, deslocado como vidro.
- Relevo com extrusão translúcida, sombra longa e fio de luz na borda. Montserrat Black VERSAL no centro, frases curtas (`maxch` 18).
- Letras sobem em sequência; risco de luz atravessa a frase; palavra-chave com luz mais forte; saída em dissolve. Imagem limpa e viva.

## lado.json do projeto
```json
{"estilo": "invisible", "keywords": ["poucas"], "cenas": [{"t": 0, "x": 0.5, "y": 0.5}]}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
