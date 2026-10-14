---
name: efeito-xerox
description: Efeito "xerox" (Xerox Halftone / Pixel Sort): nos cortes (ou nos momentos pedidos), a própria imagem vira cópia de xerox numa região que se espalha (retícula de pontos, papel, toner, contraste), com rastros de pixel sort, glitch em faixas e RGB separado no pico, e volta ao normal em ~3 s. Soma com qualquer legenda.
argument-hint: [legenda / vídeo ou pasta do projeto / momentos em segundos / observações]
---
# Efeito xerox

Estética de revista underground e impressão xerográfica, feita na PRÓPRIA imagem do vídeo, quadro a quadro (não é uma camada
por cima). Em cada momento, por uns 3 segundos:
- **entrada**: a textura de xerox (retícula de pontos que cresce nas sombras, preto chapado, papel, toner) invade uma região e se espalha;
- **pico**: rastros de pixel sort em faixas, glitch direcional e separação RGB (falha de registro de impressão);
- **saída**: a distorção se desfaz pelas bordas e a filmagem original volta.

Requer a skill **motor** (com `setup.sh` rodado: instala numpy e OpenCV) e uma skill de legenda.
Exemplo: `exemplo.jpg` (com legenda) e `exemplo-detalhe.jpg` (detalhe do efeito em filmagem real).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "xerox"`.
   Sem mais nada, o efeito entra nos cortes das cenas (com uns 4 s de folga entre um e outro).
   Para escolher quando: `"efeitos": [{"nome": "xerox", "momentos": [2.1, 8.4]}]`.
   Dá para somar outros pacotes (`"pacote": ["xerox", "cinema"]`).
2. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — o xerox roda no fim, por cima da faixa pronta.
3. Render normal (`node render_lado.mjs ...`).
4. Quadros de teste no pico (momento + 1,5 s) antes do vídeo inteiro.

Vídeo solto, sem legenda (mantém resolução, fps e áudio; o original não é alterado):
`python3 motor/efeitos/processo/xerox.py entrada.mp4 saida.mp4 --momentos 1.2,6.5`

## Controles (no mesmo objeto do lado.json, ou `--nome valor` no comando)
| Controle | Padrão | O que faz |
|---|---|---|
| `intensidade` | 1.0 | força geral (0 a 1.5) |
| `mistura` | 1.0 | original x processado no pico (0 a 1) |
| `reticula` / `densidade` / `angulo` | 9 / 1.0 / 45 | tamanho da célula, tamanho dos pontos, ângulo da retícula |
| `contraste` / `grao` | 1.0 / 0.6 | contraste xerox e granulação/toner (menos contraste = mais detalhe nas sombras) |
| `sort_dir` / `sort_comp` / `sort_limiar` | h / 0.5 / 0.38 | direção do pixel sort (h ou v), comprimento máximo do rastro, brilho mínimo |
| `frag` / `rgb` | 0.7 / 7 | quantidade de glitch em faixas e deslocamento dos canais RGB (px) |
| `regiao` / `raio` | auto / 0.55 | onde começa (`auto` = parte com mais detalhe, `tudo`, ou `"x,y"` de 0 a 1) e até onde se espalha |
| `duracao` / `entrada` / `saida` | 3.0 / 0.9 / 0.8 | segundos: tempo total, de invasão e de dissolução |
| `semente` | 7 | mesma semente = mesmo resultado |

Desempenho: uns 13 s de processamento para cada 3 s de efeito na faixa do vídeo (1080x760); ~35 s em Full HD.
Os trechos sem efeito são só copiados. O pixel sort é feito em faixas (geométrico e rápido), não no quadro inteiro.
