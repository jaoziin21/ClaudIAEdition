---
name: getsup
description: Legenda "Getsup": Times apertada na horizontal — narração branca pequena no centro, somando palavra por palavra (seca) na mesma linha; nas frases de impacto, letreiro VERMELHO (minúsculas grandes empilhadas com as linhas sobrepostas, ou versal estreita com espaço grande entre as palavras no alto à esquerda). Tudo entra e sai seco. Estilo de edit cristão/reflexivo de TikTok.
argument-hint: [vídeo ou pasta do projeto / frases de impacto / observações]
---
# Legenda Getsup

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `getsup`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
- Fonte: Tinos (= Times) APERTADA na horizontal, letras quase encostando (vem no motor).
- 3 modos por frase:
  - **linha** — branca pequena no centro da imagem; cada palavra aparece SECA e soma na mesma linha (a frase já nasce no lugar
    certo, o começo não anda); sombra leve.
  - **empilha** — vermelha, minúscula, GRANDE, 1–2 palavras por linha, linhas sobrepostas, alinhada à esquerda, palavra por palavra.
  - **caixa** — vermelha, versal estreita e alta, ESPAÇO GRANDE entre as palavras, no alto à esquerda da imagem.
- Sem nada marcado: frase com palavra-chave (`"keywords"`) vira vermelha (alterna empilha/caixa); o resto é linha.
  Por isso use POUCAS palavras-chave (6–8), só nas frases de impacto. Para escolher o modo de uma frase: `"look"` na cena.
- Entra e sai seco (sem animação). `"escala"` na cena aumenta/diminui. Imagem: levemente quente, cor forte, grão fino.

## lado.json do projeto
```json
{"estilo": "getsup", "keywords": ["medo", "coragem", "caminho"],
 "cenas": [{"t": 0, "x": 0.5, "y": 0.5},
           {"t": 12.4, "x": 0.5, "y": 0.5, "look": "caixa"}]}
```

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X`.
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
4. Combina com qualquer efeito (`/efeitos`) e dá para misturar com outra legenda (`"estilo"` por cena).
