---
name: mistury
description: Legenda "Mistury": cada frase vira um cartaz tipográfico novo, misturando fontes — palavra forte grande e colorida, apoio pequeno e remate em cursiva escrito na hora; a cor se ajusta ao fundo. Boa para versículo, citação e frase marcante.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Mistury

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `mistury`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Cada frase (até fim de frase ou corte; `maxch` 30) vira um CARTAZ: herói = palavra-chave da frase (ou a mais longa) grande numa fonte de destaque; apoio = conectores pequenos; remate = uma palavra forte em cursiva de pincel branca.
- 7 visuais que se alternam: `didone`, `condensada`, `gotica`, `romana`, `bebas`, `bloco`, `fina`. Para forçar um visual numa cena: `"look": "gotica"` na cena.
- `medeFundo`: em fundo claro o herói troca para cor escura e a sombra fica mais densa.
- Cada palavra só aparece quando é falada; o cartaz some inteiro no fim da frase. Varie os cantos, nunca no rosto.

## lado.json do projeto
```json
{"estilo": "mistury", "keywords": ["UMA palavra forte por frase"], "cenas": [{"t": 0, "x": 0.5, "y": 0.4}]}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
