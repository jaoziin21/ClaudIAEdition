# edit.json — formato e receitas

Gerado por `aml.py plano`/`montar`; pode ser editado à mão e re-renderizado (`aml.py render`). Tempos em segundos.

```json
{
  "format": {"w": 1080, "h": 1920, "fps": 30}, "fps": 30, "duration": 20.0,
  "preset": "rap", "grade": "manga_tinta", "grain": 0.05, "vignette": 0.35, "letterbox": null,
  "fade_in": 0, "fade_out": 0.6, "motion_blur": 1.0, "sharpen": true,
  "audio": "audio/trilha.wav", "audio_start": 0.0, "audio_fade_out": 0.8,
  "impact_style": {"zoom": 0.085, "shake": 0.014, "chroma": 0.004, "rgb": 6, "flash": 0.5, "tau": 0.15},
  "impacts": [{"t": 11.2, "s": 1.0}],
  "texture": {"path": "assets/originals/papel.jpg", "mode": "multiply", "opacity": 0.2},
  "text": [{"text": "ULTRA INSTINCT", "start": 11.2, "end": 12.4, "style": "impact", "pos": [0.5, 0.8]}],
  "shots": [ { ...plano... } ]
}
```

## Plano (shot)
| campo | valores |
|---|---|
| `asset`, `start`, `dur` | id do manifesto; início e duração (planos encostados, sem buraco) |
| `technique` | `parallax` (camadas do `prep`) · `camera` (imagem única) · `clip` (vídeo/GIF/sequência) |
| `camera` | `{"preset": P, "intensity": 1.0, "focus": [x,y], "wide": [x,y], "ease": "..."}` ou `{"keys": [...]}` |
| presets | `push_in_slow` `push_in_fast` `pull_out` `pan_lr` `pan_rl` `tilt_up` `tilt_down` `zoom_accel` `reframe` (aberto → close de supetão no meio) `orbit` (paralaxe) `dutch_push` (inclina) `drift` `hold` `close_hold` |
| `keys` | `[{"t":0,"x":.5,"y":.4,"z":1.0,"r":0,"px":-1},{"t":1,"z":1.3,"ease":"outExpo"}]` — x,y centro na imagem (0–1), z zoom sobre "cobrir", r graus, px deriva de paralaxe |
| easing | `linear inSine outSine inOutSine in/out/inOutQuad in/out/inOutCubic inExpo outExpo inOutExpo outBack hold` |
| `ramp` | speed ramp da câmera `[[u,vel],...]` |
| `zmax` | zoom máximo útil (comprime as keys) — o plano calcula pela resolução da fonte |
| `fill` | `cover` (padrão) · `fit_blur` (imagem inteira sobre cópia desfocada dela) |
| `parallax` | amplitude (fração da largura; o `prep` sugere `parallax_max`) |
| `character` | `{"breathe":1,"sway":0.5,"flutter":0.6}` respiração/balanço/contorno tremulando |
| `puppet` | `[{"part":"cabeca","rot":[[0,0],[0.5,-4],[1,0]]}]` (parte criada com `aml.py parte`) |
| `silhouette` | `"#000000"` → personagem vira silhueta da própria máscara |
| `clip` | `{"in": 12.3, "speed": 1.0 \| [[u,vel],...], "fps": 12, "loop": true}` |
| `grade`, `impact_style`, `shake` | sobrescrevem o global no plano |
| `transition_in` | `{"type": T, "dur": s}` — `cut flash(color) dissolve dip whip(dir) zoom_burst glitch wipe(angle) iris light_leak(color)` |
| `fx` | lista: `impact{t,s}` `glow{amount}` `chroma{amount}` `exposure{ev:[[u,ev]]}` `light_sweep{t0,t1,angle,width,intensity,color}` `light_leak` `glitch{t0,t1,strength}` `wave{amount,freq}` `rgb_split{amount}` `flash{t0,t1,color}` `zoom_burst{amount}` `invert{t0,t1}` |

Cores (`grade`): `neutro anime_rap epico noir dourado celestial sepia frio sangue manga_tinta`.

## Receitas
- **Impacto no beat**: deixe `impacts` com os impactos do áudio; ajuste `impact_style` (rap: zoom .08, shake .014,
  rgb 6; cinemático: .045/.006/2; contemplativo: .015/0/0).
- **Troca de enquadramento na mesma arte**: dois planos seguidos do mesmo asset, um `pull_out` com `fill: fit_blur`
  e outro `close_hold` no `focus` — ou um só plano `reframe`.
- **Whip entre duas artes**: `transition_in: {"type":"whip","dur":0.22,"dir":"left"}` no plano B.
- **Pausa dramática**: plano `hold`/`push_in_slow` de 1–2,5 s sem efeitos antes do drop; o seguinte entra com
  `flash` ou `zoom_burst` + impacto forte.
- **Silhueta gráfica**: plano parallax com `"silhouette": "#000000"`, fundo claro (`exposure` +0.4) e `glow`.
- **Clipe em câmera lenta no clímax**: `technique: clip` + `speed [[0,1.4],[0.35,0.4],[1,1]]` (mistura de quadros).
- **Jesus contemplativo**: preset `contemplativo`, `grade: dourado`, `light_sweep` lento, `dissolve` 0,8 s, sem shake.
