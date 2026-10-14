# Técnicas de animação (como o motor faz cada coisa)

Tudo é transformação de pixels que já existem. Arquivo principal: `scripts/amllib/render.py`.

## A — Câmera (motion.py)
- Estado `x,y,z,r,px` interpolado por keyframes com easing (`interp_keys`). `z=1` = a imagem cobre o quadro.
- Antes do render, `_fit_keys` redistribui x/y dentro da área possível da imagem (o movimento corre do início ao
  fim, sem travar na borda e disparar depois — defeito real achado no QA do teste do Goku).
- Zoom mínimo automático garante que nunca apareça borda vazia (rotação/shake incluídos).
- Impacto: `z *= 1 + zoom·impulso(t)` (ataque de ~1 quadro, decaimento exponencial `tau`) + shake suave (soma de
  senos com fase sorteada, determinística) com amplitude proporcional ao impulso.
- Motion blur real: quando o deslocamento entre quadros passa de ~7 px, o quadro é a média de 2–5 subamostras no
  tempo (obturador 180°).
- Speed ramp: `ramp` remapeia o progresso da câmera; em clipes, `clip.speed` remapeia o tempo da fonte (câmera lenta
  com mistura de quadros vizinhos).

## B — Parallax 2.5D (prep.py)
- Recorte com rembg (`isnet-anime` local). Componentes pequenos descartados; furos preenchidos; borda suave.
- Fundo: a área do personagem (dilatada ~2%) é preenchida por convolução normalizada multi-escala (cores vizinhas
  da PRÓPRIA imagem) e desfocada — sem inventar conteúdo. `parallax_max` diminui quanto maior o personagem e pior a
  borda, para quase não revelar esse preenchimento.
- No render: o fundo recebe 60% do zoom e 75% do deslocamento do plano do personagem; `px` empurra as camadas em
  sentidos opostos conforme a profundidade (`orbit`).
- Foco/caixa calculados pela MAIOR figura (2 personagens → não mira o vazio entre eles).

## C — Personagem
- Transformação MESH (grade 18x32 sobre o quadro de saída) = câmera + deformação num único passo:
  respiração (escala vertical presa na base), balanço (rotação em torno da base), contorno tremulando (só perto da
  borda do recorte, mais forte em cima: cabelo/roupa), partes de puppet (máscara suave + pivô + rotação por keyframe).
- Amplitudes pequenas de propósito: sem informação na imagem para movimentos grandes. Corpo/rosto animados de verdade
  → usar clipe existente. Pessoa real → sem deformação.

## D — Efeitos (effects.py)
Cor por LUT (Image.point) + saturação; glow (bright-pass desfocado em 1/4 e "screen"); aberração cromática radial;
RGB split com borda repetida; glitch (faixas deslocadas, blocos, canais); flash branco/cor; zoom burst (média de
cópias escaladas, centro nítido); borrão direcional (whip); onda; vinheta; grão de filme 2 px; light sweep; light
leak; negativo; letterbox; textura existente com blend (overlay/multiply/screen/softlight); transições wipe/iris;
texto cinético (impact: pop + tremor; cinematic: fade + subida).
Ordem: geometria → cor → luz/efeitos do plano → glow → aberração/RGB → textura → transição → vinheta → letterbox →
grão → texto → fades.

## Desempenho medido (4 CPUs, sem GPU)
1080x1920: ~0,2–0,6 s por quadro por processo; 4 processos em paralelo (um encoder x264 por plano) → ~4 quadros/s.
Prévia (meia resolução) ~4x mais rápida. `--gpu` usa h264_nvenc só se um teste real de encode passar.
