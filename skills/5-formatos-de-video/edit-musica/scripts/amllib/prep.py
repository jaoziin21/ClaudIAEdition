"""Preparação de assets para animação — só transforma o que já existe.

- Recorte do personagem por segmentação (rembg; modelo isnet-anime p/ anime, u2net/isnet-general p/ pinturas/fotos
  se estiverem baixados). Sem rembg → camada única (só câmera) ou máscara fornecida pelo usuário.
- Fundo 2.5D: a área atrás do personagem é preenchida com CÓPIA DESFOCADA DA PRÓPRIA IMAGEM (convolução normalizada
  em várias escalas). Nada é pintado/gerado; o parallax é limitado para quase não revelar esse preenchimento.
- Ponto de interesse (rosto/topo do recorte ou saliência espectral) e enquadramentos: aberto × close.
- Classificação do plano (close / médio / aberto / silhueta / ação) usada para dar variedade ao edit.
- Partes para puppet (ex.: cabeça = faixa superior do recorte) e spritesheet → sequência de quadros.
- Extração de clipes/quadros de vídeos existentes (trechos com mais ação, cortes de cena).
"""
import os
import subprocess

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from . import project, util

REMBG_MODELS = {"anime": "isnet-anime", "geral": "isnet-general-use", "pessoa": "u2net_human_seg", "u2net": "u2net"}


def rembg_available():
    try:
        import rembg  # noqa
        return True
    except Exception:  # noqa
        return False


def local_models():
    out = []
    for root in [os.path.expanduser("~/.rembg/models"), os.path.expanduser("~/.u2net")]:
        if os.path.isdir(root):
            for dp, _, fs in os.walk(root):
                out += [os.path.splitext(f)[0] for f in fs if f.endswith(".onnx")]
    return sorted(set(out))


def segment(img, model="isnet-anime"):
    """Máscara alfa (L) do elemento principal. Levanta RuntimeError se não der."""
    from rembg import new_session, remove
    sess = new_session(model)
    w, h = img.size
    s = min(1.0, 1600 / max(w, h))
    small = img.convert("RGB").resize((int(w * s), int(h * s)), Image.LANCZOS) if s < 1 else img.convert("RGB")
    m = remove(small, session=sess, only_mask=True, post_process_mask=True)
    if m.size != (w, h):
        m = m.resize((w, h), Image.BILINEAR)
    return m.convert("L")


def clean_mask(mask):
    """Mantém componentes grandes, suaviza borda, preenche furinhos."""
    from scipy import ndimage
    a = np.asarray(mask, np.float32) / 255.0
    b = a > 0.5
    lab, n = ndimage.label(b)
    if n > 1:
        sizes = ndimage.sum(b, lab, range(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:] = sizes >= max(sizes.max() * 0.08, b.size * 0.002)
        b = keep[lab]
    b = ndimage.binary_fill_holes(b)
    soft = np.where(b, np.maximum(a, 0.5), np.minimum(a, 0.5) * 0)  # mantém antialias da borda
    im = Image.fromarray((np.clip(soft, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    return im


def fill_behind(rgb, mask, levels=6):
    """Preenche a área do recorte com a vizinhança DESFOCADA da própria imagem (convolução normalizada).
    Não cria conteúdo novo: só espalha cores existentes, de propósito borrado."""
    a = np.asarray(rgb, np.float32)
    w, h = mask.size
    # dilata a máscara ~2% (em resolução reduzida) para não puxar a borda do personagem para o fundo
    ds = max(1, min(w, h) // 360)
    small = mask.resize((max(1, w // ds), max(1, h // ds)), Image.BILINEAR).point(lambda v: 255 if v > 20 else 0)
    k = max(3, (int(min(w, h) * 0.02 / ds) // 2) * 2 + 1)
    small = small.filter(ImageFilter.MaxFilter(min(k, 15)))
    if k > 15:
        small = small.filter(ImageFilter.MaxFilter(k - 14 if (k - 14) % 2 else k - 13))
    valid = 1.0 - np.asarray(small.resize((w, h), Image.BILINEAR), np.float32) / 255.0
    valid = (valid > 0.98).astype(np.float32)
    out = a.copy()
    filled = valid.copy()
    for lv in range(levels):
        f = 2 ** (lv + 2)
        sw, sh = max(2, w // f), max(2, h // f)
        num = np.asarray(Image.fromarray(np.clip(a * valid[..., None], 0, 255).astype(np.uint8)).resize(
            (sw, sh), Image.BOX).filter(ImageFilter.GaussianBlur(2)).resize((w, h), Image.BILINEAR), np.float32)
        den = np.asarray(Image.fromarray((valid * 255).astype(np.uint8)).resize((sw, sh), Image.BOX).filter(
            ImageFilter.GaussianBlur(2)).resize((w, h), Image.BILINEAR), np.float32) / 255.0
        est = num / np.maximum(den[..., None], 1e-3)
        need = (filled < 0.99) & (den > 0.02)
        wgt = np.where(need, 1 - filled, 0)[..., None]
        out = out * (1 - wgt) + est * wgt
        filled = np.maximum(filled, np.where(den > 0.02, 1.0, filled))
    out = np.where(valid[..., None] > 0.5, a, out)
    # escurece/desfoca um pouco o que foi preenchido para não chamar atenção
    blur = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14)),
                      np.float32)
    hole = (1 - valid)[..., None]
    out = out * (1 - hole) + blur * 0.9 * hole
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def saliency_point(rgb):
    """Ponto de maior saliência (resíduo espectral, Hou & Zhang 2007) — usado quando não há recorte."""
    g = np.asarray(rgb.convert("L").resize((128, 128), Image.BILINEAR), np.float32)
    F = np.fft.fft2(g)
    la = np.log(np.abs(F) + 1e-6)
    from scipy import ndimage
    sr = la - ndimage.uniform_filter(la, 3)
    sal = np.abs(np.fft.ifft2(np.exp(sr + 1j * np.angle(F)))) ** 2
    sal = ndimage.gaussian_filter(sal, 6)
    sal[:10, :] = sal[-10:, :] = 0  # bordas da FFT geram falso máximo
    sal[:, :10] = sal[:, -10:] = 0
    y, x = np.unravel_index(np.argmax(sal), sal.shape)
    return float(x / 128), float(y / 128), sal


def classify_framing(rec):
    """close / medio / aberto / silhueta / acao — heurística sobre recorte, brilho e movimento medidos."""
    tags = []
    cov = rec.get("subject_coverage")
    bbox = rec.get("subject_bbox")
    if rec.get("kind") in ("video", "sequence"):
        tags.append("clipe")
        if (rec.get("motion") or 0) > 6:
            tags.append("acao")
    if cov is not None and bbox:
        bh = bbox[3] - bbox[1]
        if cov > 0.35 or bh > 0.95 and cov > 0.25:
            tags.append("close")
        elif cov > 0.12:
            tags.append("medio")
        else:
            tags.append("aberto")
    elif rec.get("kind") == "image":
        tags.append("aberto" if (rec.get("aspect") or 1) > 1.3 else "medio")
    if (rec.get("brightness") or 0.5) < 0.22 and (rec.get("contrast") or 0) > 0.35:
        tags.append("silhueta")
    if (rec.get("brightness") or 0.5) < 0.3 and "acao" not in tags:
        tags.append("contemplativo")
    return tags


def prep_image(proj, aid, model=None, force=False, no_segment=False, mask_path=None):
    m = project.load_manifest(proj)
    rec = m["assets"][aid]
    src = os.path.join(proj, rec["file"])
    outdir = os.path.join(proj, "assets", "processed", aid)
    os.makedirs(outdir, exist_ok=True)
    info_path = os.path.join(outdir, "prep.json")
    if os.path.exists(info_path) and not force:
        return util.load_json(info_path)
    img = ImageOps.exif_transpose(Image.open(src))
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    rgb = img.convert("RGB")
    w, h = rgb.size
    info = {"asset": aid, "w": w, "h": h, "layers": [], "method": None}
    mask = None
    if mask_path:
        mask = Image.open(mask_path).convert("L").resize((w, h), Image.BILINEAR)
        info["method"] = f"máscara fornecida ({os.path.basename(mask_path)})"
    elif has_alpha:
        mask = img.convert("RGBA").split()[-1]
        info["method"] = "alfa do próprio PNG"
    elif not no_segment and rembg_available():
        models = local_models()
        model = model or ("isnet-anime" if "isnet-anime" in models else (models[0] if models else "isnet-anime"))
        try:
            mask = clean_mask(segment(rgb, model))
            info["method"] = f"rembg/{model}"
        except Exception as e:  # noqa
            info["segment_error"] = str(e)[:300]
    sx, sy, _ = saliency_point(rgb)
    info["saliency"] = [round(sx, 3), round(sy, 3)]
    if mask is not None:
        ma = np.asarray(mask, np.float32) / 255
        cov = float((ma > 0.5).mean())
        info["subject_coverage"] = round(cov, 3)
        # foco/caixa pela MAIOR figura (2 personagens separados → não mirar o vazio entre eles)
        from scipy import ndimage
        lab, nlab = ndimage.label(ma > 0.5)
        if nlab > 1:
            sizes = ndimage.sum(np.ones_like(ma), lab, range(1, nlab + 1))
            ys, xs = np.where(lab == 1 + int(np.argmax(sizes)))
            info["figures"] = int((sizes > sizes.max() * 0.25).sum())
        else:
            ys, xs = np.where(ma > 0.5)
        usable = 0.01 < cov < 0.85 and len(xs) > 100
        if usable:
            x0, x1, y0, y1 = (float(xs.min() / w), float(xs.max() / w), float(ys.min() / h), float(ys.max() / h))
            info["subject_bbox"] = [round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)]
            # 'rosto' ~ topo do recorte (personagens), centrado na massa da faixa superior
            top = ys < (ys.min() + 0.25 * (ys.max() - ys.min()))
            info["focus"] = [round(float(xs[top].mean() / w), 3), round(float(np.percentile(ys[top], 50) / h), 3)]
            info["wide"] = [round((x0 + x1) / 2, 3), round((y0 + y1) / 2, 3)]
            # borda irregular = recorte ruim → parallax menor
            edge = np.abs(np.diff(ma[::4, ::4], axis=1)).mean()
            info["edge_quality"] = round(float(1 - min(1, edge * 20)), 3)
            bg = fill_behind(rgb, mask)
            bg.save(os.path.join(outdir, "bg.jpg"), quality=93)
            subj = rgb.copy()
            subj.putalpha(mask)
            bb = subj.getbbox()
            subj.save(os.path.join(outdir, "subject.png"))
            mask.save(os.path.join(outdir, "mask.png"))
            # parallax máximo: quanto maior o personagem, mais buraco aparece → menos deslocamento
            info["parallax_max"] = round(float(np.clip(0.035 * (1 - cov) * (0.5 + 0.5 * info["edge_quality"]),
                                                       0.008, 0.03)), 4)
            info["layers"] = [{"name": "fundo", "file": "bg.jpg", "depth": 0.0},
                              {"name": "personagem", "file": "subject.png", "depth": 1.0, "bbox_px": bb}]
            project.record_transform(proj, aid, f"recorte por segmentação ({info['method']}); fundo atrás do "
                                                f"recorte preenchido com desfoque da própria imagem")
        else:
            info["note"] = f"recorte inutilizável (cobertura {cov:.2f}) — usar só câmera"
    if not info["layers"]:
        info["focus"] = info["saliency"]
        info["wide"] = [0.5, 0.5]
        info["parallax_max"] = 0.0
        info["layers"] = [{"name": "imagem", "file": None, "depth": 1.0}]
    info["technique"] = "parallax" if len(info["layers"]) > 1 else "camera"
    util.save_json(info_path, info)
    # copia métricas úteis para o manifesto
    m = project.load_manifest(proj)
    r = m["assets"][aid]
    for k in ("subject_coverage", "subject_bbox", "focus", "parallax_max", "technique", "edge_quality"):
        if k in info:
            r[k] = info[k]
    r["framing"] = classify_framing(r)
    project.save_manifest(proj, m)
    return info


def make_part(proj, aid, name, y0, y1, pivot_y=None):
    """Parte para puppet = faixa vertical do recorte (frações da caixa do personagem). Ex.: cabeça 0–0.28,
    pivô no pescoço. Gera parts/<name>.png (máscara suave) e registra pivô."""
    outdir = os.path.join(proj, "assets", "processed", aid)
    info = util.load_json(os.path.join(outdir, "prep.json"))
    if not info or "subject_bbox" not in info:
        util.die("rode `prep` com recorte antes de criar partes")
    mask = Image.open(os.path.join(outdir, "mask.png")).convert("L")
    w, h = mask.size
    bx0, by0, bx1, by1 = info["subject_bbox"]
    ya, yb = by0 + (by1 - by0) * y0, by0 + (by1 - by0) * y1
    grad = np.zeros((h, w), np.float32)
    rows = np.arange(h) / h
    feather = 0.03 * (by1 - by0)
    wrow = np.clip((rows - ya) / feather + 0.5, 0, 1) * np.clip((yb - rows) / feather + 0.5, 0, 1)
    grad[:] = wrow[:, None]
    part = np.asarray(mask, np.float32) / 255 * grad
    os.makedirs(os.path.join(outdir, "parts"), exist_ok=True)
    Image.fromarray((part * 255).astype(np.uint8)).save(os.path.join(outdir, "parts", f"{name}.png"))
    piv = [round((bx0 + bx1) / 2, 3), round(yb if pivot_y is None else pivot_y, 3)]
    info.setdefault("parts", {})[name] = {"file": f"parts/{name}.png", "pivot": piv, "range": [y0, y1]}
    util.save_json(os.path.join(outdir, "prep.json"), info)
    project.record_transform(proj, aid, f"parte '{name}' separada do recorte (faixa {y0:.2f}–{y1:.2f})")
    return info["parts"][name]


def spritesheet_to_sequence(proj, src, cols, rows, fps=12, count=None, name=None):
    """Corta um spritesheet EXISTENTE em quadros (sequência) e registra como asset 'sequence'."""
    im = Image.open(src)
    fw, fh = im.width // cols, im.height // rows
    name = name or util.slug(os.path.splitext(os.path.basename(src))[0])
    tmp = os.path.join(proj, "work", f"seq_{name}")
    os.makedirs(tmp, exist_ok=True)
    k = 0
    for r in range(rows):
        for c in range(cols):
            if count and k >= count:
                break
            im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)).save(os.path.join(tmp, f"f_{k:04d}.png"))
            k += 1
    return tmp, k


def scene_cuts(path, threshold=0.3):
    """Tempos de troca de cena (ffmpeg select/scene)."""
    p = subprocess.run(["ffmpeg", "-v", "info", "-nostdin", "-i", path, "-vf",
                        f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    import re
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", p.stderr)]


def motion_profile(path, fps=4, w=160):
    """Movimento por segundo (diferença média entre quadros a `fps`)."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vf", f"fps={fps},scale={w}:-2,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    info = util.video_info(path)
    hh = int(round(info["h"] * w / info["w"] / 2) * 2)
    buf = np.frombuffer(p.stdout, np.uint8)
    n = len(buf) // (w * hh)
    if n < 2:
        return np.zeros(1), fps
    fr = buf[:n * w * hh].reshape(n, hh, w).astype(np.float32)
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    return d, fps


def pick_clip_segments(path, n=6, min_len=1.0, max_len=3.0, prefer="acao"):
    """Escolhe trechos de um vídeo EXISTENTE: dentro de uma mesma cena (sem corte no meio), com mais
    movimento (ação) ou menos (contemplativo). Devolve [{start,end,motion}]."""
    info = util.video_info(path)
    cuts = [0.0] + scene_cuts(path) + [info["duration"]]
    mot, fps = motion_profile(path)
    segs = []
    for a, b in zip(cuts, cuts[1:]):
        a2, b2 = a + 0.15, b - 0.15  # evita a borda do corte
        if b2 - a2 < min_len:
            continue
        L = min(max_len, b2 - a2)
        best = None
        t = a2
        while t + L <= b2 + 1e-6:
            i0, i1 = int(t * fps), max(int(t * fps) + 1, int((t + L) * fps))
            mv = float(mot[i0:i1].mean()) if i0 < len(mot) else 0.0
            score = mv if prefer == "acao" else -mv
            if best is None or score > best[0]:
                best = (score, t, mv)
            t += 0.5
        if best:
            segs.append({"start": round(best[1], 2), "end": round(best[1] + L, 2), "motion": round(best[2], 2)})
    segs.sort(key=lambda s: -s["motion"] if prefer == "acao" else s["motion"])
    # espalha pelo vídeo (evita só um trecho)
    chosen = []
    for s in segs:
        if all(abs(s["start"] - c["start"]) > 2.0 for c in chosen):
            chosen.append(s)
        if len(chosen) >= n:
            break
    return sorted(chosen, key=lambda s: s["start"])


def extract_stills(proj, video_aid, times, prefix=None):
    """Tira quadros (ainda) de um vídeo registrado → novos assets de imagem (origem = o vídeo)."""
    m = project.load_manifest(proj)
    rec = m["assets"][video_aid]
    src = os.path.join(proj, rec["file"])
    out = []
    tmpd = os.path.join(proj, "work", "stills")
    os.makedirs(tmpd, exist_ok=True)
    for t in times:
        name = f"{prefix or video_aid}_q{t:06.2f}".replace(".", "_")
        dst = os.path.join(tmpd, name + ".png")
        util.run(["ffmpeg", "-v", "error", "-y", "-nostdin", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", dst])
        aid = project.add_asset(proj, dst, role="quadro de vídeo", source_url=rec.get("source_url", ""),
                                page_url=rec.get("page_url", ""), author=rec.get("author", ""),
                                license=rec.get("license", ""), origin=rec.get("origin", "user"),
                                notes=f"quadro em {t:.2f}s de {video_aid}", copy=False, asset_id=name[:40])
        project.record_transform(proj, aid, f"quadro extraído de {video_aid} em {t:.2f}s")
        out.append(aid)
    return out
