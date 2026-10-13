---
name: efeito-sombrio
description: Pacote de efeitos "sombrio" (noir + vinheta-vermelha + chuva): Escuro, frio e sem cor, chuva fina caindo e bordas pulsando em vermelho nas palavras-chave — para vídeos pesados/de luta. Soma com qualquer legenda.
argument-hint: [legenda / vídeo ou pasta do projeto / observações]
---
# Efeito sombrio

Escuro, frio e sem cor, chuva fina caindo e bordas pulsando em vermelho nas palavras-chave — para vídeos pesados/de luta.
Partes: `noir`, `vinheta-vermelha`, `chuva`. Requer a skill **motor** e uma skill de legenda.
Exemplo: `exemplo.jpg` (com legenda) e `exemplo-detalhe.jpg` (detalhe do efeito).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "sombrio"`.
   Dá para somar outro pacote (`"pacote": ["sombrio", "vhs"]`) ou efeitos avulsos (`"efeitos": [{"nome": "particulas", "forca": 0.5}]`).
2. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — os efeitos de IMAGEM do pacote substituem o filtro da legenda.
3. Render normal (`node render_lado.mjs ...`): os efeitos de TELA (luz, chuva, glitch...) entram sozinhos, atrás ou na frente da legenda.
4. Quadros de teste antes do vídeo inteiro.
