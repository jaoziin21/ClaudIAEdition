"""Inspeção de mídia: resolução, nitidez, contraste, cor, alfa, movimento — e pontuação de potencial de animação.
Tudo medido de verdade no arquivo (nada estimado a partir do nome/URL)."""
import os
import subprocess

import numpy as np
from PIL import Image, ImageOps

from . import util

Image.MAX_IMAGE_PIXELS = 300_000_000


def _gray_small(img, maxside=1024):
    g = ImageOps.exif_transpose(img).convert("L")
    s = maxside / max(g.size)
    if s < 1:
        g = g.resize((max(1, int(g.width * s)), max(1, int(g.height * s))), Image.BILINEAR)
    return np.asarray(g, dtype=np.float32)


def sharpness(gray):
    """Variância do Laplaciano (escala ~1024 px). <60 borrado, 60–200 ok, >200 nítido."""
    g = gray
    lap = (-4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:])
    return float(lap.var())


def image_stats(img):
    rgb = np.asarray(ImageOps.exif_transpose(img).convert("RGB").resize((256, 256), Image.BILINEAR),
                     dtype=np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rg, yb = r - g, 0.5 * (r + g) - b
    colorful = float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    # dispersão de matiz: imagem P&B ou tingida de UMA cor (mangá, duotone) tem matiz concentrado
    chroma = np.sqrt(rg ** 2 + yb ** 2)
    sel = chroma > 12
    frac = float(sel.mean())
    if sel.sum() > 50:
        h = np.arctan2(yb[sel], rg[sel])
        w = chroma[sel]
        spread = 1.0 - float(np.abs((w * np.exp(1j * h)).sum()) / w.sum())
    else:
        spread = 0.0
    return {"brightness": round(float(lum.mean()) / 255, 3), "contrast": round(float(lum.std()) / 128, 3),
            "colorfulness": round(colorful, 1), "chroma_frac": round(frac, 3), "hue_spread": round(spread, 3)}


def describe_image(path):
    img = Image.open(path)
    img.load()
    w, h = ImageOps.exif_transpose(img).size
    d = {"w": w, "h": h, "megapixels": round(w * h / 1e6, 2), "aspect": round(w / h, 3), "format": img.format,
         "mode": img.mode}
    d["sharpness"] = round(sharpness(_gray_small(img)), 1)
    d.update(image_stats(img))
    if img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info):
        a = np.asarray(img.convert("RGBA"))[..., 3]
        cov = float((a > 16).mean())
        d["alpha_coverage"] = round(cov, 3)
        d["has_alpha"] = cov < 0.98
    else:
        d["has_alpha"] = False
    if getattr(img, "is_animated", False):
        d["animated_frames"] = getattr(img, "n_frames", 1)
    return d


def _sample_frames(path, times, w=320):
    frames = []
    for t in times:
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                            "-vf", f"scale={w}:-2", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
        if p.returncode == 0 and p.stdout:
            n = len(p.stdout)
            hh = n // w
            if hh > 0:
                frames.append(np.frombuffer(p.stdout[:w * hh], np.uint8).reshape(hh, w).astype(np.float32))
    return frames


def describe_video(path):
    info = util.video_info(path)
    d = dict(info)
    d["aspect"] = round(info["w"] / info["h"], 3)
    dur = max(info["duration"], 0.04)
    ts = [dur * k / 8 for k in range(1, 8)]
    fr = _sample_frames(path, ts)
    if fr:
        d["sharpness"] = round(float(np.median([sharpness(f) for f in fr])), 1)
        # movimento: diferença média entre quadros a 1/fps de distância em 3 pontos
        mot = []
        for t in ts[1::2]:
            a = _sample_frames(path, [t, t + 1.0 / max(info["fps"], 1)])
            if len(a) == 2 and a[0].shape == a[1].shape:
                mot.append(float(np.abs(a[0] - a[1]).mean()))
        d["motion"] = round(float(np.mean(mot)), 2) if mot else None
        d["brightness"] = round(float(np.mean([f.mean() for f in fr])) / 255, 3)
    return d


def describe(path):
    kind = util.media_kind(path)
    if kind == "image":
        return describe_image(path)
    if kind == "video":
        return describe_video(path)
    if kind == "sequence":
        files = sorted(f for f in os.listdir(path) if os.path.splitext(f)[1].lower() in util.IMAGE_EXT)
        if not files:
            return {"nframes": 0}
        d = describe_image(os.path.join(path, files[0]))
        d["nframes"] = len(files)
        return d
    if kind == "audio":
        return {"duration": round(util.audio_duration(path), 3)}
    return {}


def score_asset(rec, fmt):
    """Pontua 0–1 o asset para o formato de saída. Devolve (score, motivos)."""
    W, H = fmt["w"], fmt["h"]
    w, h = rec.get("w") or 1, rec.get("h") or 1
    reasons = []
    cover = max(W / w, H / h)          # ampliação para cobrir o quadro
    fit = min(W / w, H / h)            # ampliação para caber inteiro
    need = min(cover, fit * 1.6)       # aceita 'fit_blur' em vez de cobrir
    if need <= 1.0:
        res_s = 1.0
    else:
        res_s = max(0.0, 1.0 - (need - 1.0) / 2.0)
        reasons.append(f"precisa ampliar {need:.1f}x")
    sh = rec.get("sharpness") or 0
    sh_s = min(1.0, sh / 250.0)
    if sh < 60:
        reasons.append("pouco nítida")
    contrast = rec.get("contrast") or 0.3
    con_s = min(1.0, contrast / 0.45)
    s = 0.45 * res_s + 0.35 * sh_s + 0.2 * con_s
    if rec.get("kind") in ("video", "sequence") or rec.get("animated_frames"):
        s = min(1.0, s + 0.1)
        reasons.append("já tem movimento real")
    if rec.get("has_alpha"):
        s = min(1.0, s + 0.05)
        reasons.append("já recortado (PNG transparente)")
    return round(s, 3), reasons
