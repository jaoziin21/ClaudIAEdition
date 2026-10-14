---
name: efeito-parallax
description: Efeito "parallax" (Parallax Cutout / Temporal Collage): recorta o sujeito do próprio vídeo e, por ~4 s, monta uma colagem 2.5D em camadas (fundo deslizando e desfocado, sujeito com sombra e borda de papel, ecos dele de outros quadros com outra cor, placas de papel e de cor, marcas de corte) e volta ao original. Soma com qualquer legenda.
argument-hint: [legenda / vídeo ou pasta do projeto / momentos em segundos / observações]
---
# Efeito parallax

Colagem editorial em camadas feita com os PRÓPRIOS quadros do vídeo (não é montagem de imagens paradas). Em cada momento, ~4 s:
1. **separação**: o sujeito ganha sombra e borda de papel; o fundo escurece e perde cor;
2. **profundidade**: o fundo (sem o sujeito, preenchido) desliza e desfoca; o sujeito cresce e anda para o outro lado;
3. **colagem temporal**: 2-3 ecos do sujeito, de quadros anteriores e/ou posteriores, saem de dentro dele, translúcidos e com outra cor;
4. **composição**: placa de foto P&B do lugar com borda de papel, bloco de cor e marcas de corte;
5. **retorno**: tudo volta e se funde na filmagem original.
O sujeito fica sempre colorido e na frente.

Requer a skill **motor** (com `setup.sh` rodado: instala numpy, OpenCV e rembg) e uma skill de legenda.
O modelo de recorte de pessoa (176 MB) baixa sozinho no primeiro uso (precisa de internet para github.com).
Exemplo: `exemplo.jpg` (anime, com legenda) e `exemplo-detalhe.jpg` (pessoa dançando; filmagem de Kimberly Keyes, CC BY 4.0, Internet Archive).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "parallax"`.
   Sem mais nada, entra nos cortes das cenas (uns 5 s de folga entre um e outro). Para escolher quando:
   `"efeitos": [{"nome": "parallax", "momentos": [2.0]}]`.
2. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — o parallax roda no fim, por cima da faixa pronta.
3. Render normal (`node render_lado.mjs ...`).
4. Antes do vídeo inteiro, quadros de teste no meio do momento (momento + 2 s): confira o recorte.

Vídeo solto, sem legenda (mantém resolução, fps e áudio; o original não é alterado):
`python3 motor/efeitos/processo/parallax.py entrada.mp4 saida.mp4 --momentos 0.9`

## Recorte (o ponto delicado)
- Padrão `u2net_human_seg`: pessoas filmadas e também personagem humano de anime (testado). `"modelo": "isnet-anime"` para
  personagem não humano; `"isnet-general-use"` para objetos.
- Ele segue a mesma pessoa quadro a quadro e ignora as outras. Se pegar a pessoa errada: `"sujeito": "0.4,0.5"` (ponto x,y de 0 a 1).
- Borda: `"borda_ajuste": 2` encolhe 2 px (tira halo), `-2` engorda; `"suavidade"` deixa a borda mais macia.
- Recorte ruim (cabelo, mão rápida, perna borrada pelo movimento)? Use uma máscara própria: `"mascara": "mascara.mp4"`
  (vídeo P&B do mesmo tamanho e duração, branco = sujeito; pode vir do After Effects/DaVinci). Uma forma simples
  (uma elipse) também funciona e vira recorte oval de revista.
- Tempo: ~0,75 s por quadro do efeito (uns 2 min para cada 4 s). Em close (sujeito enorme) o efeito fica mais contido.

## Controles (no mesmo objeto do lado.json, ou `--nome valor` no comando)
| Controle | Padrão | O que faz |
|---|---|---|
| `intensidade` / `duracao` / `curva` | 1.0 / 4 / suave | força geral, segundos, easing (`suave`, `forte`, `elastica`) |
| `paralaxe` / `profundidade` | 1.0 / 1.0 | quanto os planos se separam / desfoque e escala do fundo |
| `vel_fundo` / `vel_sujeito` / `vel_ecos` / `vel_placas` | 1.0 | velocidade de cada plano |
| `ecos` / `atraso` / `eco_direcao` | 3 / 0.22 / antes | quantos ecos (0-3), atraso entre eles (s), `antes`, `depois` ou `ambos` |
| `eco_escala` / `eco_opacidade` / `eco_estilo` | 0.9 / 0.62 / mix | tamanho, transparência, cor (`mix`, `mono`, `duotone`, `contraste`, `cor`) |
| `placas` / `cor_placa` | 2 / 2b5cff | 0 = sem placas, 1 = só a foto, 2 = foto + bloco de cor |
| `borda` | papel | `papel`, `rasgada`, `suave`, `nenhuma` |
| `sujeito_escala` / `sujeito_contraste` | 1.0 / 1.08 | quanto o sujeito cresce / contraste dele |
| `fundo_cor` / `fundo_luz` | 0.45 / 0.72 | saturação e luz do fundo no pico (1 = sem mudança) |
| `sombra` / `graficos` / `camera` / `separacao` | true | liga/desliga cada componente |
| `lado` / `semente` | 1 / 3 | para que lado o fundo anda (1 ou -1) / variação |
