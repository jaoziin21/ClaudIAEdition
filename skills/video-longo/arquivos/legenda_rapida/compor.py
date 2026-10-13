# LEGENDA RÁPIDA — passo 2: monta a legenda quadro a quadro a partir das palavras fotografadas uma vez (sprites.mjs),
# reproduzindo a animação do scene_legenda.html: entrada (opacidade, desfoque, sobe 12 px, inclina, escala), brilho vermelho das
# palavras-chave, onda de saída, sombras do bloco (drop-shadow 0 2px 3px .6 + 0 0 9px .3) e o escurecido atrás do texto.
# Escreve quadros RGBA crus (só a área RECORTE) no stdout, para o ffmpeg sobrepor no fundo.
# uso: python3 -I compor.py <pasta_sprites> <recorte x,y,w,h> <quadro_ini> <quadro_fim> [fps=30]
import sys, json, math, os
import numpy as np, cv2
from PIL import Image

D, REC, F0, F1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
FPS = float(sys.argv[5]) if len(sys.argv) > 5 else 30.0
M = json.load(open(os.path.join(D, 'meta.json')))
PX = M['PX']
RX, RY, RW, RH = [int(v) for v in REC.split(',')]
cw, ch = RW * PX, RH * PX                       # área de trabalho em px do dispositivo
IN, OUTW, STAG = 0.6, 0.42, 0.045

def load(f):   # PNG RGBA → float32 pré-multiplicado
    a = np.asarray(Image.open(os.path.join(D, f)).convert('RGBA'), dtype=np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a

shade = load('shade.png')[RY * PX:(RY + RH) * PX, RX * PX:(RX + RW) * PX]
lines = M['lines']
cache = {}
def sprite(li, wi):
    k = (li, wi)
    if k not in cache:
        if len(cache) > 400: cache.clear()
        cache[k] = load(lines[li]['words'][wi]['f'])
    return cache[k]

clamp = lambda x: 0.0 if x < 0 else (1.0 if x > 1 else x)
eOut = lambda t: 1 - (1 - t) ** 5
eIn = lambda t: t * t * t
def gblur(img, sd):
    return img if sd < 0.05 else cv2.GaussianBlur(img, (0, 0), sigmaX=sd, sigmaY=sd, borderType=cv2.BORDER_CONSTANT)
def over(top, bot):   # composição pré-multiplicada: top sobre bot
    return top + bot * (1 - top[..., 3:4])

MARG = 30 * PX   # folga em volta do texto para desfoque/sombras do bloco
shade_a = shade[..., 3].copy()                       # o escurecido é preto: só o alfa importa

def estado(t):
    """linha ativa e parâmetros de cada palavra; a chave igual = quadro idêntico (reaproveita)"""
    L = next((l for l in lines if l['start'] <= t < l['end']), None)
    if L is None: return None, None, ()
    W = L['words']; n = len(W); stag = min(STAG, 0.3 / n)
    exit0 = max(W[-1]['s'] + 0.35, L['end'] - (OUTW + stag * (n - 1)))
    ps = []
    for i, w in enumerate(W):
        if t < w['s']: ps.append(None); continue
        p = eOut(clamp((t - w['s']) / IN)); o = eIn(clamp((t - exit0 - i * stag) / OUTW))
        g = (0.35 + 0.9 * math.sin(math.pi * clamp((t - w['s']) / 0.9))) * (1 - o) if w['k'] else 0.0
        ps.append((round(p, 4), round(o, 4), round(g, 4)))
    shown = max([q[0] * (1 - q[1]) for q in ps if q] or [0])
    op = round(min(1.0, (t - L['start']) / 0.4) * shown, 4)
    return L, ps, (lines.index(L), op, tuple(ps))

def frame(L, ps, op):
    """devolve (alfa do escurecido * op, retângulo do texto, texto pré-multiplicado nesse retângulo)"""
    li = lines.index(L); W = L['words']
    items = []; x0 = y0 = 10 ** 9; x1 = y1 = -1
    for i, (w, q) in enumerate(zip(W, ps)):
        if q is None: continue
        p, o, g = q; a = p * (1 - o)
        if a <= 0.001: continue
        ty = (1 - p) * 12 - o * 14; th = math.radians((1 - p) * 18); s = 0.98 + 0.02 * p + 0.03 * o
        b, c = w['box'], w['crop']
        ox, oy = b['x'] + b['w'] * 0.5, b['y'] + b['h'] * 0.8
        sx, sy = s, s * math.cos(th)
        tx_, ty_ = PX * (ox + (c['x'] - ox) * sx - RX), PX * (oy + (c['y'] - oy) * sy + ty - RY)
        img = sprite(li, i); hh, ww = img.shape[:2]
        items.append((i, w, p, o, g, a, sx, sy, tx_, ty_, img))
        x0 = min(x0, tx_); y0 = min(y0, ty_); x1 = max(x1, tx_ + ww * sx); y1 = max(y1, ty_ + hh * sy)
    if not items: return None
    X0 = max(0, int(x0) - MARG); Y0 = max(0, int(y0) - MARG); X1 = min(cw, int(x1) + MARG + 1); Y1 = min(ch, int(y1) + MARG + 1)
    bw, bh = X1 - X0, Y1 - Y0
    txt = np.zeros((bh, bw, 4), np.float32)
    for (i, w, p, o, g, a, sx, sy, tx_, ty_, img) in items:
        # filtro do span: blur(...) e, na palavra-chave, drop-shadow vermelho (desvio = raio/2); depois opacity
        img = gblur(img, ((1 - p) * 6 + o * 7) * PX)
        if w['k'] and g > 0:
            al = gblur(np.ascontiguousarray(img[..., 3]), (6 + 10 * g) / 2 * PX) * (0.45 * g)
            img = over(img, np.dstack([al, al * (45 / 255), al * (40 / 255), al]))
        img = img * a
        # transform: translateY rotateX scale (origem 50% 80%), sem perspectiva; só dentro do retângulo do texto
        A = np.array([[sx, 0, tx_ - X0], [0, sy, ty_ - Y0]], np.float32)
        warped = cv2.warpAffine(img, A, (bw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        txt = over(warped, txt)
    # filtro do #wrap: drop-shadow(0 2px 3px rgba(0,0,0,.6)) e depois drop-shadow(0 0 9px rgba(0,0,0,.3))
    a1 = gblur(np.ascontiguousarray(txt[..., 3]), 1.5 * PX)
    a1 = np.roll(a1, 2 * PX, axis=0); a1[:2 * PX] = 0
    r1 = txt.copy(); r1[..., 3] += a1 * 0.6 * (1 - txt[..., 3])
    a2 = gblur(np.ascontiguousarray(r1[..., 3]), 4.5 * PX) * 0.3
    r2 = r1.copy(); r2[..., 3] += a2 * (1 - r1[..., 3])
    # escurecido por baixo (preto, alfa do gradiente * op)
    sa = shade_a[Y0:Y1, X0:X1] * op
    r2[..., 3] += sa * (1 - r2[..., 3])
    return (X0, Y0, X1, Y1), r2

def to_bytes(L, ps, op):
    out = np.zeros((ch, cw, 4), np.uint8)
    if L is None: return out.tobytes()
    out[..., 3] = (shade_a * op * 255 + 0.5).astype(np.uint8)
    r = frame(L, ps, op)
    if r:
        (X0, Y0, X1, Y1), img = r
        a = img[..., 3:4]
        rgb = img[..., :3] / np.maximum(a, 1e-6)
        out[Y0:Y1, X0:X1] = (np.clip(np.concatenate([rgb, a], axis=2), 0, 1) * 255 + 0.5).astype(np.uint8)
    return out.tobytes()

prev_key, prev_bytes = None, None
w = sys.stdout.buffer
for f in range(F0, F1):
    L, ps, key = estado(f / FPS)
    if key != prev_key:                                # quadro parado (pausa, frase já toda acesa) = reaproveita
        prev_bytes = to_bytes(L, ps, key[1] if L else 0); prev_key = key
    w.write(prev_bytes)
w.flush()
