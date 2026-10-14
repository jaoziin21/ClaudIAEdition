---
name: black-sample
description: Legenda "Black Sample": legenda de TV branca e minúscula numa caixa PRETA justa embaixo no centro; o texto se escreve em pedaços no ritmo da fala (sílabas), com 1 quadro de falha em cada pedaço novo e uma piscada no fim da frase; imagem limpa. Boa para edits de anime/filme com fala.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Black Sample

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `black-sample`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Uma linha, letra tipo Arial (Arimo) branca, tudo minúsculo, numa caixa preta sólida e justa, embaixo no centro.
- O texto entra em PEDAÇOS no tempo da fala: palavra curta inteira, palavra longa em até 3 passos de sílaba ("ob" → "obser" → "observando").
  A frase fica centralizada e a caixa cresce para os dois lados.
- Em cada pedaço novo: 1 quadro de falha (a linha vira um risco achatado e borrado, com varredura e um tracinho de cursor).
- Fim da frase: pisca (some 2 quadros, volta 2, some 2, volta 2) e sai.
- Sem destaque de cor. Opções: `"glitch": false` (sem a falha), `"piscar": false` (sem piscar).
- Imagem limpa (nitidez leve, vinheta suave).

## lado.json do projeto
```json
{"estilo": "black-sample", "cenas": [{"t": 0, "x": 0.5, "y": 0.88}]}
```

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X`.
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
