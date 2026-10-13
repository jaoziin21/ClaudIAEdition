---
name: sample-yellow
description: Legenda "Sample Yellow": legenda de TV que chama atenção, amarela em itálico fino, palavra por palavra numa caixinha escura translúcida; imagem sonhadora com brilho, grão e luz. Boa para reflexão, fala de personagem e Shorts de GIF.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Sample Yellow

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `sample-yellow`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Roboto itálico fino amarelo, minúsculo, palavra por palavra no lugar final; a caixinha escura cresce junto com as palavras.
- `medeFundo`: caixa forte em fundo claro, fraca em fundo médio, nenhuma em fundo escuro. Separação RGB leve; palavra-chave = amarelo mais claro com um pulinho de brilho (use poucas).
- Imagem: brilho estourado, grão e vinheta; na cena, vazamentos de luz, clarão em cada corte e risco verde de glitch.
- Posição padrão: embaixo no centro (`x: 0.5, y: 0.86`), uma linha.
- Variação em 2 linhas ao lado do personagem (como se ele falasse): `"multilinha": true`, `"maxch": 56`, `"tamanho": 50`, cena `{"t":0,"x":0.36,"y":0.5,"maxw":0.56}` (ajuste o x para o lado livre).

## lado.json do projeto
```json
{"estilo": "sample-yellow", "keywords": ["poucas"], "cenas": [{"t": 0, "x": 0.5, "y": 0.86}]}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
