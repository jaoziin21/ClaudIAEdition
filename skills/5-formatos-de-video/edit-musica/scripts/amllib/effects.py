"""Efeitos cinematográficos procedurais (sobre a arte original — nada é gerado por IA).

Todos recebem/devolvem quadro float32 HxWx3 (0–255). Caches por tamanho para manter ~10–30 ms por efeito.
Presets de cor: GRADES. Efeitos: glow, chroma (aberração radial), rgb_split, glitch, flash, zoom_burst
(radial blur), dir_blur (motion/whip), wave (distorção), vignette, grain, light_sweep, light_leak, exposure,
texture (sobreposição de textura EXISTENTE), letterbox, transições com máscara (wipe/iris), texto cinético.
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- cor


GRADES = {
    # contraste, saturação, (sombra RGB), (luz RGB), lift (preto), gamma
    "neutro": dict(contrast=1.0, sat=1.0, shadow=(0, 0, 0), high=(0, 0, 0), lift=0, gamma=1.0),
    "anime_rap": dict(contrast=1.18, sat=1.18, shadow=(-4, 2, 10), high=(8, 2, -6), lift=0, gamma=0.97),
    "epico": dict(contrast=1.25, sat=1.05, shadow=(-8, 4, 14), high=(14, 4, -10), lift=0, gamma=0.95),
    "noir": dict(contrast=1.3, sat=0.12, shadow=(-2, 0, 6), high=(0, 0, 0), lift=0, gamma=0.92),
    "dourado": dict(contrast=1.08, sat=0.95, shadow=(6, 0, -6), high=(18, 8, -14), lift=6, gamma=1.02),
    "celestial": dict(contrast=1.05, sat=0.9, shadow=(-4, 2, 10), high=(16, 12, 0), lift=10, gamma=1.06),
    "sepia": dict(contrast=1.12, sat=0.25, shadow=(10, 0, -12), high=(22, 10, -18), lift=8, gamma=1.0),
    "frio": dict(contrast=1.15, sat=0.85, shadow=(-6, 0, 14), high=(-4, 4, 12), lift=0, gamma=0.97),
    "manga_tinta": dict(contrast=1.32, sat=0.06, shadow=(-3, 0, 6), high=(10, 6, -6), lift=4, gamma=0.98),
    "sangue": dict(contrast=1.3, sat=1.1, shadow=(10, -6, -6), high=(14, -4, -8), lift=0, gamma=0.93),
}


@lru_cache(maxsize=32)
def _grade_lut(name, contrast, gamma, lift):
    g = GRADES[name]
    x = np.arange(256, dtype=np.float32) / 255.0
    # curva S em torno de 0.5
    c = contrast
    y = 0.5 + (x - 0.5) * c
    y = np.where(c > 1, y * 0.85 + (0.5 - 0.5 * np.cos(np.clip(y, 0, 1) * math.pi)) * 0.15, y)
    y = np.clip(y, 0, 1) ** (1.0 / max(gamma, 1e-3))
    y = lift / 255.0 + y * (1 - lift / 255.0)
    luts = []
    for ch in range(3):
        sh, hi = g["shadow"][ch], g["high"][ch]
        yy = y * 255 + sh * (1 - y) ** 2 * 1.0 + hi * y ** 2
        luts.append(np.clip(yy, 0, 255).astype(np.float32))
    return np.stack(luts)


def grade(f, name="neutro", amount=1.0, contrast=None, sat=None):
    """Correção de cor por LUT (Image.point, em C) + saturação (ImageEnhance) — ~10 ms em 1080x1920."""
    if name not in GRADES or (name == "neutro" and contrast is None and sat is None):
        return f
    from PIL import ImageEnhance
    g = GRADES[name]
    c = contrast if contrast is not None else g["contrast"]
    s = sat if sat is not None else g["sat"]
    lut = _grade_lut(name, round(c, 3), g["gamma"], g["lift"])
    im = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8))
    im = im.point(np.clip(lut, 0, 255).astype(np.uint8).reshape(-1).tolist())
    if abs(s - 1) > 1e-3:
        im = ImageEnhance.Color(im).enhance(s)
    out = np.asarray(im, np.float32)
    if amount < 1:
        out = f + (out - f) * amount
    return out


def invert(f, amount=1.0):
    """Negativo (clássico em edit de mangá na batida forte)."""
    return f + (255 - 2 * f) * amount


def exposure(f, ev):
    return f * (2.0 ** ev) if ev else f


# ---------------------------------------------------------------- luz


def _blur_small(f, factor=4, radius=8):
    h, w = f.shape[:2]
    im = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8))
    sm = im.resize((max(1, w // factor), max(1, h // factor)), Image.BILINEAR)
    sm = sm.filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(sm.resize((w, h), Image.BILINEAR), dtype=np.float32)


def glow(f, amount=0.5, threshold=170, radius=10):
    if amount <= 0:
        return f
    bright = np.clip(f - threshold, 0, 255) * (255.0 / max(1, 255 - threshold))
    b = _blur_small(bright, 4, radius)
    return 255 - (255 - f) * (255 - b * amount) / 255.0  # screen


@lru_cache(maxsize=8)
def _proj_grid(h, w, angle_deg):
    a = math.radians(angle_deg)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return (xx * math.cos(a) + yy * math.sin(a)) / max(h, w)


def light_sweep(f, u, angle=25, width=0.08, intensity=0.6, color=(255, 240, 210)):
    """Faixa de luz atravessando o quadro (u: 0→1)."""
    h, w = f.shape[:2]
    p = _proj_grid(h, w, angle)
    lo, hi = float(p.min()), float(p.max())
    pos = lo - width * 2 + (hi - lo + width * 4) * u
    band = np.exp(-((p - pos) / width) ** 2) * intensity
    col = np.array(color, np.float32)
    return 255 - (255 - f) * (1 - band[..., None] * col / 255.0)


@lru_cache(maxsize=8)
def _radial(h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    return np.sqrt(((xx - cx) / (w / 2)) ** 2 + ((yy - cy) / (h / 2)) ** 2) / math.sqrt(2)


def light_leak(f, u, color=(255, 150, 60), intensity=0.55, side="left"):
    """Vazamento de luz quente vindo da borda (transição/clímax)."""
    h, w = f.shape[:2]
    yy, xx = np.mgrid[0:h:8, 0:w:8].astype(np.float32)
    cx = {"left": -0.2 + 0.9 * u, "right": 1.2 - 0.9 * u}.get(side, 0.5) * w
    cy = h * (0.3 + 0.4 * u)
    d = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 0.7) ** 2) / (0.6 * max(w, h))
    m = np.clip(1 - d, 0, 1) ** 2 * intensity * math.sin(math.pi * min(1, max(0, u)))
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32) / 255
    col = np.array(color, np.float32)
    return 255 - (255 - f) * (1 - m[..., None] * col / 255.0)


def vignette(f, amount=0.35):
    if amount <= 0:
        return f
    h, w = f.shape[:2]
    r = _radial(h, w)
    m = 1 - amount * np.clip(r * 1.25 - 0.25, 0, 1) ** 1.6
    return f * m[..., None]


@lru_cache(maxsize=4)
def _grain_frames(h, w, n=6, seed=7):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        g = rng.normal(0, 1, (h // 2 + 1, w // 2 + 1)).astype(np.float32)
        g = np.repeat(np.repeat(g, 2, 0), 2, 1)[:h, :w]  # grão de 2 px (cara de filme, não ruído digital)
        out.append(g)
    return out


def grain(f, amount=0.05, frame_idx=0):
    if amount <= 0:
        return f
    h, w = f.shape[:2]
    g = _grain_frames(h, w)[frame_idx % 6]
    lum = f.mean(axis=2, keepdims=True) / 255.0
    k = amount * 255 * (0.6 + 0.8 * lum * (1 - lum) * 4) * 0.5  # mais visível nos meios-tons
    return f + g[..., None] * k


# ---------------------------------------------------------------- impacto / glitch


def flash(f, alpha, color=(255, 255, 255)):
    if alpha <= 0:
        return f
    a = min(1.0, alpha)
    return f * (1 - a) + np.array(color, np.float32) * a


def _shift_channel(ch, dx, dy):
    """Desloca um canal repetindo a borda (sem 'dar a volta' no quadro)."""
    dx, dy = int(dx), int(dy)
    if dx == 0 and dy == 0:
        return ch
    h, w = ch.shape
    ys = np.clip(np.arange(h) - dy, 0, h - 1)
    xs = np.clip(np.arange(w) - dx, 0, w - 1)
    return ch[ys][:, xs]


def rgb_split(f, amount=6, angle=0.0):
    if amount < 0.5:
        return f
    dx = int(round(amount * math.cos(math.radians(angle))))
    dy = int(round(amount * math.sin(math.radians(angle))))
    out = f.copy()
    out[..., 0] = _shift_channel(f[..., 0], dx, dy)
    out[..., 2] = _shift_channel(f[..., 2], -dx, -dy)
    return out


def chroma(f, amount=0.006):
    """Aberração cromática radial: R ampliado, B reduzido em torno do centro."""
    if amount <= 0:
        return f
    h, w = f.shape[:2]
    out = f.copy()
    for ch, s in ((0, 1 + amount), (2, 1 - amount)):
        im = Image.fromarray(np.clip(f[..., ch], 0, 255).astype(np.uint8), "L")
        a = 1 / s
        im = im.transform((w, h), Image.AFFINE, (a, 0, w / 2 * (1 - a), 0, a, h / 2 * (1 - a)), Image.BILINEAR)
        out[..., ch] = np.asarray(im, np.float32)
    # bordas sem dado ficam com o canal original
    return out


def glitch(f, strength=1.0, seed=0):
    """Faixas horizontais deslocadas + separação de canais + blocos (determinístico por seed)."""
    if strength <= 0:
        return f
    rng = np.random.default_rng(seed)
    h, w = f.shape[:2]
    out = f.copy()
    nb = int(3 + 6 * strength)
    for _ in range(nb):
        y0 = int(rng.integers(0, h - 4))
        bh = int(rng.integers(4, max(6, int(h * 0.06 * strength))))
        dx = int(rng.normal(0, w * 0.04 * strength))
        y1 = min(h, y0 + bh)
        out[y0:y1] = np.roll(f[y0:y1], dx, axis=1)
        if rng.random() < 0.5:
            out[y0:y1, :, int(rng.integers(0, 3))] = np.roll(f[y0:y1, :, 0], dx + int(w * 0.01), axis=1)
    if rng.random() < 0.5 * strength:
        bw, bh = int(w * rng.uniform(0.1, 0.3)), int(h * rng.uniform(0.02, 0.06))
        x0, y0 = int(rng.integers(0, w - bw)), int(rng.integers(0, h - bh))
        sx, sy = int(rng.integers(0, w - bw)), int(rng.integers(0, h - bh))
        out[y0:y0 + bh, x0:x0 + bw] = f[sy:sy + bh, sx:sx + bw]
    return rgb_split(out, 4 * strength)


def zoom_burst(f, amount=0.08, n=6, center=(0.5, 0.5)):
    """Radial blur / zoom burst (meio da tela nítido, bordas riscadas)."""
    if amount <= 0:
        return f
    h, w = f.shape[:2]
    small = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).resize((w // 2, h // 2), Image.BILINEAR)
    sw, sh = small.size
    cx, cy = center[0] * sw, center[1] * sh
    acc = np.zeros((sh, sw, 3), np.float32)
    for i in range(n):
        s = 1 + amount * i / max(1, n - 1)
        a = 1 / s
        im = small.transform((sw, sh), Image.AFFINE, (a, 0, cx * (1 - a), 0, a, cy * (1 - a)), Image.BILINEAR)
        acc += np.asarray(im, np.float32)
    acc /= n
    acc = np.asarray(Image.fromarray(acc.astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32)
    m = np.clip(_radial(h, w) * 1.6, 0, 1)[..., None]
    return f * (1 - m) + acc * m


def dir_blur(f, dx, dy, n=8):
    """Borrão direcional (whip pan) de comprimento (dx,dy) px."""
    if abs(dx) + abs(dy) < 1:
        return f
    h, w = f.shape[:2]
    small = np.asarray(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).resize((w // 2, h // 2),
                                                                                   Image.BILINEAR), np.float32)
    acc = np.zeros_like(small)
    for i in range(n):
        k = (i / max(1, n - 1) - 0.5)
        acc += np.roll(small, (int(dy * k / 2), int(dx * k / 2)), axis=(0, 1))
    acc /= n
    return np.asarray(Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR),
                      np.float32)


def wave(f, amount=8, freq=3.0, t=0.0):
    """Distorção ondulada horizontal (choque/calor)."""
    if amount < 0.5:
        return f
    h, w = f.shape[:2]
    rows = np.arange(h)
    off = (amount * np.sin(2 * math.pi * (rows / h * freq + t * 2))).astype(np.int32)
    idx = (np.arange(w)[None, :] + off[:, None]) % w
    return f[rows[:, None], idx]


def letterbox(f, ratio=2.39):
    h, w = f.shape[:2]
    target_h = int(w / ratio)
    if target_h >= h:
        return f
    bar = (h - target_h) // 2
    out = f.copy()
    out[:bar] = 0
    out[h - bar:] = 0
    return out


# ---------------------------------------------------------------- texturas existentes


@lru_cache(maxsize=8)
def _texture(path, h, w):
    im = Image.open(path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, int(im.width * s + 1)), max(h, int(im.height * s + 1))), Image.LANCZOS)
    x0, y0 = (im.width - w) // 2, (im.height - h) // 2
    return np.asarray(im.crop((x0, y0, x0 + w, y0 + h)), np.float32)


def texture(f, path, mode="overlay", opacity=0.3):
    if not path or not os.path.exists(path) or opacity <= 0:
        return f
    h, w = f.shape[:2]
    t = _texture(path, h, w)
    a, b = f / 255.0, t / 255.0
    if mode == "multiply":
        r = a * b
    elif mode == "screen":
        r = 1 - (1 - a) * (1 - b)
    elif mode == "softlight":
        r = (1 - 2 * b) * a * a + 2 * b * a
    else:  # overlay
        r = np.where(a < 0.5, 2 * a * b, 1 - 2 * (1 - a) * (1 - b))
    return f + (r * 255 - f) * opacity


# ---------------------------------------------------------------- transições com máscara


def wipe(fa, fb, u, angle=20, softness=0.06):
    h, w = fa.shape[:2]
    p = _proj_grid(h, w, angle)
    lo, hi = float(p.min()), float(p.max())
    pos = lo - softness + (hi - lo + 2 * softness) * u
    m = np.clip((pos - p) / softness + 0.5, 0, 1)[..., None]
    return fa * (1 - m) + fb * m


def iris(fa, fb, u, softness=0.05):
    h, w = fa.shape[:2]
    r = _radial(h, w) * math.sqrt(2)
    m = np.clip((u * 1.5 - r) / softness + 0.5, 0, 1)[..., None]
    return fa * (1 - m) + fb * m


# ---------------------------------------------------------------- texto cinético (opcional)

FONT_CANDIDATES = {
    "impact": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
    "cinematic": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                  "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"],
    "serif_italic": ["/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"],
}


def find_font(style, custom=None):
    for p in ([custom] if custom else []) + FONT_CANDIDATES.get(style, FONT_CANDIDATES["impact"]):
        if p and os.path.exists(p):
            return p
    return None


@lru_cache(maxsize=64)
def _font(path, size):
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()


def draw_text(f, text, u, style="impact", pos=(0.5, 0.78), size=0.075, color=(255, 255, 255),
              font=None, frame_idx=0):
    """Texto cinético. u = progresso dentro do intervalo do texto (0–1).
    impact: CAIXA ALTA, entra com 'pop' (outBack) + tremor; cinematic: fade + subida leve + espaçamento."""
    h, w = f.shape[:2]
    fp = find_font(style, font)
    px = int(size * h if style == "impact" else size * h * 0.8)
    txt = text.upper() if style == "impact" else text
    if style == "impact":
        k = min(1.0, u / 0.12)
        sc = 1.35 - 0.35 * (1 - (1 - k) ** 3) if k < 1 else 1.0
        alpha = min(1.0, u / 0.05) * min(1.0, (1 - u) / 0.08)
        jitter = (math.sin(frame_idx * 2.3) * 0.004 * h, math.cos(frame_idx * 1.7) * 0.004 * h) if u < 0.2 else (0, 0)
    else:
        alpha = min(1.0, u / 0.2) * min(1.0, (1 - u) / 0.2)
        sc = 1.0
        jitter = (0, -(1 - min(1, u / 0.4)) * 0.01 * h)
    fnt = _font(fp, max(8, int(px * sc)))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    spacing = int(px * 0.08) if style == "cinematic" else 0
    if spacing:
        txt = (" " if spacing > 6 else "").join(txt) if False else txt
    bbox = d.multiline_textbbox((0, 0), txt, font=fnt, align="center", stroke_width=max(2, px // 14))
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = pos[0] * w - tw / 2 + jitter[0]
    y = pos[1] * h - th / 2 + jitter[1]
    sw = max(2, px // 14) if style == "impact" else max(1, px // 30)
    d.multiline_text((x, y), txt, font=fnt, fill=tuple(color) + (int(255 * alpha),), align="center",
                     stroke_width=sw, stroke_fill=(0, 0, 0, int(220 * alpha)))
    arr = np.asarray(layer, np.float32)
    a = arr[..., 3:4] / 255.0
    return f * (1 - a) + arr[..., :3] * a
