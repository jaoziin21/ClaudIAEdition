---
name: efeito-sonho
description: Pacote de efeitos "sonho" (sonhador + particulas + glitch): Sonhador: brilho estourado suave, grão fino, vazamentos de luz, clarão nos cortes, poeira de luz flutuando e risco verde de glitch. Soma com qualquer legenda.
argument-hint: [legenda / vídeo ou pasta do projeto / observações]
---
# Efeito sonho

Sonhador: brilho estourado suave, grão fino, vazamentos de luz, clarão nos cortes, poeira de luz flutuando e risco verde de glitch.
Partes: `sonhador`, `particulas`, `glitch`. Requer a skill **motor** e uma skill de legenda.
Exemplo: `exemplo.jpg` (com legenda) e `exemplo-detalhe.jpg` (detalhe do efeito).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "sonho"`.
   Dá para somar outro pacote (`"pacote": ["sonho", "vhs"]`) ou efeitos avulsos (`"efeitos": [{"nome": "particulas", "forca": 0.5}]`).
2. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — os efeitos de IMAGEM do pacote substituem o filtro da legenda.
3. Render normal (`node render_lado.mjs ...`): os efeitos de TELA (luz, chuva, glitch...) entram sozinhos, atrás ou na frente da legenda.
4. Quadros de teste antes do vídeo inteiro.
