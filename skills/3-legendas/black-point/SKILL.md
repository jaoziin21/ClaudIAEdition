---
name: black-point
description: Legenda "Black Point": itálico branco tipo Arial numa caixa escura translúcida embaixo no centro; palavra por palavra; reticências que entram ponto a ponto; palavra-chave dividida em 3 cores; sai se desfazendo letra por letra; imagem de cinema (pele quente, sombra fria, grão).
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Black Point

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `black-point`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Uma linha, Arimo ITÁLICO (= Arial itálico) branco com brilho leve, numa caixa escura translúcida folgada, embaixo no centro.
- Palavra por palavra, entrando seca no tempo da fala; a caixa cresce junto.
- Frase que termina "no ar" (sem ? ou ! e com pausa depois) ganha reticências que entram UM PONTO POR VEZ. `"reticencias": false` desliga.
- Palavra-chave (use poucas) dividida em 3 cores: padrão azul/branco/vermelho. Trocar: `"coresChave": ["#1f9d55", "#f2d530", "#2a4fbf"]`.
- Saída: a frase se desfaz letra por letra em ~0,25 s.
- Imagem de cinema: pele quente, sombra fria, um pouco dessaturada, grão e vinheta.

## lado.json do projeto
```json
{"estilo": "black-point", "keywords": ["poucas"], "cenas": [{"t": 0, "x": 0.5, "y": 0.9}]}
```

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X`.
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
