---
name: legenda-dinamica
description: Legenda "Dinâmica": serifa itálica elegante (Playfair) ao lado de quem fala, mudando de canto a cada frase; palavras surgem do escuro e saem em fumaça, palavra-chave vermelha com brilho; vídeo escuro com cara de Super 8. Boa para diálogo e cena dramática.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Legenda Dinâmica

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `dinamica`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Playfair itálico minúsculo; palavras surgem do fundo e saem em fumaça; palavra-chave acende em vermelho com brilho.
- A legenda fica AO LADO de quem fala e varia de canto a cada cena (sup./inf., esq./dir., centro); nunca no rosto.
- Imagem escura (sombra) com grão e textura de Super 8.
- Mapeie os cortes de cena (`ffmpeg -i X -an -vf "fps=30,scale=480:-1,select='gt(scene,0.2)',metadata=print" -f null -`), veja um quadro de cada cena e escolha o espaço livre. Cena sem lugar bom: `{"t": ..., "nada": true}`.

## lado.json do projeto
```json
{"estilo": "dinamica", "keywords": [...], "cenas": [{"t": 0, "x": 0.3, "y": 0.25, "maxw": 0.4}, {"t": 4.2, "x": 0.7, "y": 0.8}]}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
