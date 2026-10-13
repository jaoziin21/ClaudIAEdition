---
name: street
description: Legenda "Street": legenda pequena que se escreve sílaba por sílaba, palavra-chave vermelha, palavras de grito piscando GIGANTES em letra gótica, colagem de painéis com outros momentos do próprio vídeo; imagem escura e contrastada. Boa para edit agressivo, anime e luta.
argument-hint: [vídeo ou pasta do projeto / observações]
---
# Legenda Street

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `street`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Legenda pequena (Arimo branco), frases curtas (`maxch` 24), no centro; palavra longa se escreve por sílabas; palavra-chave vermelha.
- **Gritos**: palavras da lista `"gritos"` (sem lista = palavras-chave) piscam GIGANTES na altura da imagem em gótica fina, alternando vermelho e branco com contorno. Máx. 1 grito a cada 2,5 s — escolha 4 a 8 no vídeo.
- **Colagem**: o motor tira quadros do próprio vídeo; nos cortes e nos gritos pipocam 1–3 painéis com outros momentos.
- Precisa do fim de cada palavra no `words.json` (o fluxo padrão já gera). Nos quadros de teste, inclua o quadro de cada grito (tempo da palavra + 0,05).

## lado.json do projeto
```json
{"estilo": "street", "keywords": [...], "gritos": ["4 a 8 palavras de impacto"], "cenas": [{"t": 0, "x": 0.5, "y": 0.5}]}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
