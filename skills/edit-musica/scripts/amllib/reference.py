"""Análise de vídeo de REFERÊNCIA → parâmetros de edição reutilizáveis (não copia a sequência, extrai a linguagem).

Mede: cortes e duração dos planos (média, mediana, ritmo ao longo do tempo), cortes na batida (se tiver áudio),
flashes, proporção P&B/tingido, brilho/contraste/saturação, silhuetas (quadros escuros e contrastados),
tipo de movimento por plano (parado / pan / zoom-ou-complexo, por correlação de fase), e gera uma folha de quadros.
"""
import os
import subprocess

import numpy as np

from . import audio as au
from . import prep, util


def _frames(path, fps, w=160):
    info = util.video_info(path)
    h = int(round(info["h"] * w / info["w"] / 2) * 2)
    p = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vf", f"fps={fps},scale={w}:{h}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    buf = np.frombuffer(p.stdout, np.uint8)
    n = len(buf) // (w * h * 3)
    return buf[:n * w * h * 3].reshape(n, h, w, 3).astype(np.float32), info


def _phase_shift(a, b):
    A, B = np.fft.fft2(a), np.fft.fft2(b)
    R = A * np.conj(B)
    r = np.abs(np.fft.ifft2(R / (np.abs(R) + 1e-6)))
    y, x = np.unravel_index(np.argmax(r), r.shape)
    h, w = a.shape
    y = y - h if y > h // 2 else y
    x = x - w if x > w // 2 else x
    return float(x), float(y), float(r.max())


def analyze(path, outdir=None, fps=10):
    fr, info = _frames(path, fps)
    dur = info["duration"]
    cuts = prep.scene_cuts(path, 0.3)
    bounds = [0.0] + cuts + [dur]
    lens = np.diff(bounds)
    gray = fr.mean(axis=3)
    lum = gray.mean(axis=(1, 2)) / 255
    con = gray.std(axis=(1, 2)) / 128
    r, g, b = fr[..., 0], fr[..., 1], fr[..., 2]
    chroma = np.sqrt((r - g) ** 2 + (0.5 * (r + g) - b) ** 2)
    chroma_frac = (chroma > 12).mean(axis=(1, 2))
    sat = chroma.mean(axis=(1, 2)) / 255
    flashes = [i / fps for i in range(1, len(lum) - 1) if lum[i] > 0.75 and lum[i] - lum[i - 1] > 0.25]
    silh = float(((lum < 0.22) & (con > 0.3)).mean())
    # movimento por plano
    moves = []
    for a, bnd in zip(bounds, bounds[1:]):
        i0, i1 = int(a * fps) + 1, int(bnd * fps) - 1
        if i1 - i0 < 2:
            continue
        sh, res = [], []
        for i in range(i0, i1):
            x, y, pk = _phase_shift(gray[i], gray[i + 1])
            sh.append(np.hypot(x, y))
            res.append(np.abs(gray[i + 1] - gray[i]).mean())
        tr, rd = float(np.median(sh)), float(np.median(res))
        kind = "parado" if rd < 1.5 else ("pan" if tr >= 1 else "zoom/complexo")
        moves.append({"start": round(a, 2), "dur": round(bnd - a, 2), "tipo": kind, "mov": round(rd, 2)})
    prof = {
        "file": path, "duration": dur, "fps": info["fps"], "resolution": f"{info['w']}x{info['h']}",
        "cuts": [round(c, 3) for c in cuts], "n_shots": len(lens),
        "avg_shot_len": round(float(lens.mean()), 3), "median_shot_len": round(float(np.median(lens)), 3),
        "min_shot_len": round(float(lens.min()), 3), "cuts_per_min": round(len(cuts) / max(dur, 1e-6) * 60, 1),
        "brightness": round(float(lum.mean()), 3), "contrast": round(float(con.mean()), 3),
        "saturation": round(float(sat.mean()), 3), "bw_ratio": round(float((chroma_frac < 0.12).mean()), 3),
        "flashes": [round(f, 2) for f in flashes], "flash_rate_per_min": round(len(flashes) / max(dur, 1e-6) * 60, 1),
        "silhouette_ratio": round(silh, 3), "camera_moves": moves,
        "move_mix": {k: sum(1 for m in moves if m["tipo"] == k) for k in ("parado", "pan", "zoom/complexo")},
    }
    # ritmo ao longo do tempo (janelas de 5 s)
    win = []
    for t in np.arange(0, dur, 5.0):
        win.append(sum(1 for c in cuts if t <= c < t + 5))
    prof["cuts_per_5s"] = win
    if info["has_audio"]:
        try:
            a = au.analyze(path)
            bt = np.array(a["beats"])
            if len(bt) and cuts:
                near = [np.min(np.abs(bt - c)) for c in cuts]
                prof["cut_on_beat_ratio"] = round(float(np.mean(np.array(near) < 0.07)), 3)
            prof["tempo"] = a["tempo"]
        except Exception as e:  # noqa
            prof["audio_error"] = str(e)[:200]
    asl = prof["median_shot_len"]  # mediana: robusta a um plano muito longo
    prof["sugestao"] = {
        "preset": "rap" if asl < 0.9 else ("cinematico" if asl < 2.5 else "contemplativo"),
        "grade": "manga_tinta" if prof["bw_ratio"] > 0.5 else ("noir" if prof["saturation"] < 0.05 else
                                                               ("anime_rap" if prof["saturation"] > 0.12 else "epico")),
        "flash_nos_cortes": prof["flash_rate_per_min"] > 6,
        "silhuetas": silh > 0.15,
    }
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        from PIL import Image
        thumbs = []
        for i, c in enumerate([0.0] + cuts[:35]):
            idx = min(len(fr) - 1, int((c + 0.15) * fps))
            p = os.path.join(outdir, f"ref_{i:02d}.jpg")
            Image.fromarray(fr[idx].astype(np.uint8)).save(p)
            thumbs.append(p)
        from .render import contact_sheet
        prof["sheet"] = contact_sheet(thumbs, os.path.join(outdir, "folha_referencia.jpg"), cols=8, width=1600)
        util.save_json(os.path.join(outdir, "perfil_referencia.json"), prof)
    return prof
