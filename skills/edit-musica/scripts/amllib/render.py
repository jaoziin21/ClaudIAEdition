"""Compositor por quadro → FFmpeg.

Cada plano (shot) é uma função pura do tempo: geometria (câmera + camadas 2.5D + deformação do personagem +
motion blur por subamostragem) → cor/luz/efeitos → transições → texto. Planos são renderizados em paralelo
(um processo por plano, cada um com seu encoder x264) e concatenados sem reencode; o áudio é muxado no fim.
"""
import math
import multiprocessing as mp
import os
import subprocess
import time

import numpy as np
from PIL import Image, ImageFilter

from . import effects as fx
from . import motion, project, util

Image.MAX_IMAGE_PIXELS = 300_000_000

# ---------------------------------------------------------------- utilidades de geometria


def _rot(theta_deg):
    a = math.radians(theta_deg)
    return math.cos(a), math.sin(a)


def build_mesh(W, H, gx, gy, fn):
    """fn(X, Y) -> (SX, SY) nos vértices de uma grade gx×gy do quadro de saída. Devolve dados p/ Image.MESH."""
    xs = np.linspace(0, W, gx + 1)
    ys = np.linspace(0, H, gy + 1)
    X, Y = np.meshgrid(xs, ys)
    SX, SY = fn(X, Y)
    mesh = []
    xi = np.round(xs).astype(int)
    yi = np.round(ys).astype(int)
    for j in range(gy):
        for i in range(gx):
            mesh.append(((int(xi[i]), int(yi[j]), int(xi[i + 1]), int(yi[j + 1])),
                         (SX[j, i], SY[j, i], SX[j + 1, i], SY[j + 1, i],
                          SX[j + 1, i + 1], SY[j + 1, i + 1], SX[j, i + 1], SY[j, i + 1])))
    return mesh


# ---------------------------------------------------------------- leitores de mídia


class ClipReader:
    """Decodifica um vídeo/GIF sequencialmente a partir de `t_in`, já redimensionado (w,h). get(t) devolve o
    quadro mais próximo (ou mistura de 2 quadros para câmera lenta)."""

    def __init__(self, path, t_in, w, h, max_dur):
        info = util.video_info(path)
        self.fps = info["fps"] or 30.0
        self.w, self.h = w, h
        self.t0 = t_in
        self.proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{t_in:.3f}", "-i", path, "-t", f"{max_dur + 0.5:.3f}",
             "-vf", f"scale={w}:{h}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.buf = {}
        self.next_idx = 0
        self.eof = False

    def _read_until(self, idx):
        n = self.w * self.h * 3
        while self.next_idx <= idx and not self.eof:
            data = self.proc.stdout.read(n)
            if len(data) < n:
                self.eof = True
                break
            self.buf[self.next_idx] = np.frombuffer(data, np.uint8).reshape(self.h, self.w, 3)
            self.next_idx += 1
        for k in [k for k in self.buf if k < idx - 2]:
            del self.buf[k]

    def get(self, t_rel, blend=False):
        x = max(0.0, t_rel * self.fps)
        i = int(x)
        self._read_until(i + 1)
        if not self.buf:
            return None
        last = max(self.buf)
        a = self.buf.get(min(i, last), self.buf[last])
        if blend and (i + 1) in self.buf:
            f = x - i
            if f > 0.05:
                b = self.buf[i + 1]
                return (a.astype(np.float32) * (1 - f) + b.astype(np.float32) * f).astype(np.uint8)
        return a

    def close(self):
        try:
            self.proc.stdout.close()
            self.proc.kill()
        except Exception:  # noqa
            pass


# ---------------------------------------------------------------- plano


class ShotRenderer:
    def __init__(self, proj, edit, shot, W, H, fps, scale=1.0):
        self.proj, self.edit, self.shot = proj, edit, shot
        self.W, self.H, self.fps, self.scale = W, H, fps, scale
        man = project.load_manifest(proj)
        if shot["asset"] not in man["assets"]:
            raise RuntimeError(f"asset {shot['asset']} não está no manifesto")
        self.rec = man["assets"][shot["asset"]]
        self.path = os.path.join(proj, self.rec["file"])
        pdir = os.path.join(proj, "assets", "processed", shot["asset"])
        self.prep = util.load_json(os.path.join(pdir, "prep.json"), {}) or {}
        self.kind = self.rec.get("kind", "image")
        self.technique = shot.get("technique") or ("clip" if self.kind in ("video", "sequence") else
                                                   self.prep.get("technique", "camera"))
        cam = shot.get("camera") or {"preset": "push_in_slow"}
        focus = cam.get("focus") or self.prep.get("focus") or [0.5, 0.45]
        wide = cam.get("wide") or self.prep.get("wide") or [0.5, 0.5]
        self.keys = [dict(k) for k in cam.get("keys") or []] or motion.expand_preset(cam.get("preset", "push_in_slow"), focus,
                                                            cam.get("intensity", 1.0), wide, cam.get("ease"))
        self.ramp = shot.get("ramp")
        zcap = shot.get("zmax")
        kz = max(k.get("z", 1.0) for k in self.keys)
        if zcap and kz > zcap:  # comprime o zoom para não ampliar além do detalhe que a fonte tem
            f_ = (zcap - 1.0) / max(1e-6, kz - 1.0)
            self.keys = [dict(k, z=1.0 + (k.get("z", 1.0) - 1.0) * f_) if "z" in k else k for k in self.keys]
        self.zmax = max(k.get("z", 1.0) for k in self.keys) * 1.25
        self.shake = motion.Shake(seed=hash(shot.get("id", "s")) & 0xFFFF)
        st = edit.get("impact_style", {})
        self.imp_style = {"zoom": 0.07, "shake": 0.010, "chroma": 0.004, "rgb": 5, "flash": 0.0, "tau": 0.16}
        self.imp_style.update(st)
        self.imp_style.update(shot.get("impact_style", {}))
        self.base_shake = shot.get("shake", edit.get("shake", 0.0))
        self.fill = shot.get("fill", "cover")
        self.layers = []
        self.clip = None
        self.parallax = float(shot.get("parallax", self.prep.get("parallax_max", 0.0) or 0.0))
        self.char = shot.get("character") or {}
        self.silhouette = shot.get("silhouette")
        self._load()
        if self.technique != "clip" or True:
            self._fit_keys()

    # -- carga e pré-redimensionamento (uma vez por plano)
    def _load(self):
        W, H = self.W, self.H
        if self.technique == "clip":
            if self.kind == "sequence":
                self.seq = sorted(os.path.join(self.path, f) for f in os.listdir(self.path)
                                  if os.path.splitext(f)[1].lower() in util.IMAGE_EXT)
                im0 = Image.open(self.seq[0])
                self.iw, self.ih = im0.size
            else:
                info = util.video_info(self.path)
                self.iw, self.ih = info["w"], info["h"]
            self._set_scales()
            kw, kh = self.kw, self.kh
            if self.kind != "sequence":
                c = self.shot.get("clip", {})
                spd = c.get("speed", 1.0)
                vmax = max(p[1] for p in spd) if isinstance(spd, list) else float(spd)
                self.clip = ClipReader(self.path, float(c.get("in", 0.0)), kw, kh, self.shot["dur"] * vmax + 1.0)
            return
        img = Image.open(self.path)
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
        self.iw, self.ih = img.size
        self._set_scales()
        pdir = os.path.join(self.proj, "assets", "processed", self.shot["asset"])
        use_layers = self.technique == "parallax" and len(self.prep.get("layers", [])) > 1
        if use_layers:
            for L in self.prep["layers"]:
                im = Image.open(os.path.join(pdir, L["file"]))
                im = im.convert("RGBA" if L["depth"] > 0 else "RGB")
                self.layers.append({"depth": L["depth"], "img": self._resize(im), "name": L["name"]})
        else:
            self.layers.append({"depth": 1.0, "img": self._resize(img.convert("RGB")), "name": "imagem"})
        # mapas para deformação do personagem (baixa resolução)
        self.edge_map = None
        self.parts = []
        if use_layers and (self.char.get("flutter") or self.shot.get("puppet")):
            mask = Image.open(os.path.join(pdir, "mask.png")).convert("L").resize((256, 256), Image.BILINEAR)
            ma = np.asarray(mask, np.float32) / 255
            from scipy import ndimage
            inside = ndimage.distance_transform_edt(ma > 0.5)
            self.edge_map = np.clip(1 - inside / 10.0, 0, 1) * (ma > 0.05)
            for pp in self.shot.get("puppet", []):
                part = self.prep.get("parts", {}).get(pp["part"])
                if not part:
                    continue
                pm = np.asarray(Image.open(os.path.join(pdir, part["file"])).convert("L").resize(
                    (256, 256), Image.BILINEAR), np.float32) / 255
                self.parts.append({"w": pm, "pivot": part["pivot"], "rot": pp.get("rot", [[0, 0], [1, 0]])})
        if self.fill == "fit_blur":
            base = self.layers[0]["img"].convert("RGB")
            s = max(self.W / base.width, self.H / base.height) * 1.1
            bb = base.resize((max(1, int(base.width * s / 8)), max(1, int(base.height * s / 8))), Image.BILINEAR)
            bb = bb.filter(ImageFilter.GaussianBlur(6)).resize((int(base.width * s), int(base.height * s)),
                                                               Image.BILINEAR)
            x0, y0 = (bb.width - self.W) // 2, (bb.height - self.H) // 2
            arr = np.asarray(bb.crop((x0, y0, x0 + self.W, y0 + self.H)), np.float32) * 0.45
            self.fit_bg = arr

    def _resize(self, im):
        """Redimensiona (LANCZOS). Ampliação grande → só realce de nitidez do traço existente (unsharp)."""
        out = im.resize((self.kw, self.kh), Image.LANCZOS)
        if self.k > 1.4 and self.edit.get("sharpen", True):
            amt = int(min(90, 40 + (self.k - 1.4) * 40))
            if out.mode == "RGBA":
                a = out.split()[-1]
                out = out.convert("RGB").filter(ImageFilter.UnsharpMask(2, amt, 2))
                out.putalpha(a)
            else:
                out = out.filter(ImageFilter.UnsharpMask(2, amt, 2))
        return out

    def _fit_keys(self):
        """Redistribui x/y dos keyframes dentro da área que a imagem permite (cover), para o movimento ser contínuo
        do começo ao fim em vez de travar na borda e disparar depois."""
        if self.fill == "fit_blur":
            return
        W, H = self.W, self.H
        multi = len(self.layers) > 1
        for ax, half_px, size in (("x", W / 2, self.iw), ("y", H / 2, self.ih)):
            vals, los, his = [], [], []
            for k in self.keys:
                z = k.get("z", 1.0)
                zb = 1 + (z - 1) * 0.6 if multi else z
                hw = half_px / (self.s0 * zb * size) * 1.02 + (self.parallax if (multi and ax == "x") else 0)
                los.append(hw)
                his.append(1 - hw)
                vals.append(k.get(ax, 0.5))
            lo, hi = max(los), min(his)
            if hi <= lo:
                lo = hi = 0.5
            if all(lo - 1e-6 <= v <= hi + 1e-6 for v in vals):
                continue
            vmin, vmax = min(vals), max(vals)
            a, b = max(lo, vmin), min(hi, vmax)
            for k, v in zip(self.keys, vals):
                if ax not in k:
                    continue
                if vmax - vmin < 1e-6 or b < a:
                    k[ax] = min(max(v, lo), hi)
                else:
                    k[ax] = a + (v - vmin) / (vmax - vmin) * (b - a)

    def _set_scales(self):
        W, H = self.W, self.H
        self.s_cover = max(W / self.iw, H / self.ih)
        self.s_fit = min(W / self.iw, H / self.ih)
        self.s0 = self.s_fit if self.fill == "fit_blur" else self.s_cover
        # resolução de trabalho: até o zoom máximo se a fonte tiver detalhe; nunca amplia além do 'cobrir'
        # (o resto da ampliação é feito na transformação). Clipes: no máximo o tamanho de 'cobrir'.
        if self.technique == "clip":
            k = min(self.s0, max(1.0, self.s0 * 0.75)) if self.s0 > 1 else self.s0 * min(self.zmax, 1.0 / self.s0)
        else:
            k = max(self.s0, min(self.s0 * self.zmax, 1.0))
        self.k = k
        self.kw, self.kh = max(2, int(round(self.iw * k))), max(2, int(round(self.ih * k)))

    # -- câmera no tempo
    def camera(self, tl):
        dur = self.shot["dur"]
        u = min(1.0, max(0.0, tl / dur)) if dur > 0 else 0.0
        u2 = motion.remap(u, self.ramp)
        cam = motion.interp_keys(self.keys, u2)
        if tl > dur:  # extrapola um pouco (usado em transições sobrepostas)
            c2 = motion.interp_keys(self.keys, 1.0)
            c1 = motion.interp_keys(self.keys, max(0, 1.0 - 0.05))
            k = (tl - dur) / (0.05 * dur + 1e-6)
            cam = {f: c2[f] + (c2[f] - c1[f]) * min(k, 3) for f in motion.FIELDS}
        t = self.shot["start"] + tl
        ev = [(i["t"], i.get("s", 1.0)) for i in self.shot.get("_impacts", [])]
        imp = motion.impulse(t, ev, tau=self.imp_style["tau"])
        cam["z"] = cam["z"] * (1 + self.imp_style["zoom"] * imp)
        amp = self.base_shake + self.imp_style["shake"] * imp
        dx, dy, dr = self.shake(t, amp)
        cam["sx"], cam["sy"] = dx * self.H, dy * self.H
        cam["r"] = cam["r"] + dr
        cam["imp"] = imp
        return cam

    # -- geometria de uma camada
    def _layer_map(self, cam, depth, extra_off=(0.0, 0.0)):
        W, H = self.W, self.H
        if depth >= 1:
            z = cam["z"]
            cx, cy = cam["x"], cam["y"]
        else:  # fundo: menos zoom e menos deslocamento que o plano do personagem
            k0 = self.keys[0]
            z = 1 + (cam["z"] - 1) * 0.6
            cx = k0.get("x", 0.5) + (cam["x"] - k0.get("x", 0.5)) * 0.75
            cy = k0.get("y", 0.5) + (cam["y"] - k0.get("y", 0.5)) * 0.75
        S = self.s0 * z / self.k
        rot = cam["r"]
        c, s = _rot(rot)
        offx = cam.get("px", 0.0) * self.parallax * W * (depth - 1.0) + cam["sx"] + extra_off[0]
        offy = cam["sy"] + extra_off[1]
        if self.fill != "fit_blur":
            hx = (W / 2 * abs(c) + H / 2 * abs(s) + abs(offx)) / S
            hy = (W / 2 * abs(s) + H / 2 * abs(c) + abs(offy)) / S
            need = max(hx / (self.kw / 2), hy / (self.kh / 2))
            if need > 1:  # zoom mínimo para nunca mostrar borda vazia
                S *= need * 1.001
                hx, hy = hx / need, hy / need
        px_c = cx * self.kw
        py_c = cy * self.kh
        if self.fill == "fit_blur":
            # imagem inteira visível: se ficou maior que a tela num eixo, não deixa sobrar faixa vazia; senão centraliza
            sw, sh_ = self.kw * S / 2, self.kh * S / 2
            hx, hy = W / 2 / S, H / 2 / S
            px_c = min(max(px_c, hx), self.kw - hx) if sw >= W / 2 else self.kw / 2
            py_c = min(max(py_c, hy), self.kh - hy) if sh_ >= H / 2 else self.kh / 2
        elif depth < 1 or len(self.layers) == 1:
            px_c = min(max(px_c, hx), self.kw - hx)
            py_c = min(max(py_c, hy), self.kh - hy)
        return S, c, s, offx, offy, px_c, py_c

    def _clamped_center(self, cam):
        """Centro do plano do personagem alinhado ao fundo depois do clamp do fundo."""
        if self.fill == "fit_blur" or len(self.layers) == 1:
            return None
        S, c, s, offx, offy, px_c, py_c = self._layer_map(cam, 0.0)
        k0 = self.keys[0]
        # inverte a relação fundo→personagem para manter os dois alinhados após o clamp
        bx = px_c / self.kw
        by = py_c / self.kh
        cx = k0.get("x", 0.5) + (bx - k0.get("x", 0.5)) / 0.75
        cy = k0.get("y", 0.5) + (by - k0.get("y", 0.5)) / 0.75
        return cx, cy

    def geometry(self, tl, cam=None, extra_off=(0.0, 0.0)):
        cam = cam or self.camera(tl)
        W, H = self.W, self.H
        if self.technique == "clip":
            return self._clip_frame(tl, cam, extra_off)
        cc = self._clamped_center(cam)
        if cc:
            cam = dict(cam, x=cc[0], y=cc[1])
        out = None
        for L in self.layers:
            S, c, s, offx, offy, pxc, pyc = self._layer_map(cam, L["depth"], extra_off)
            im = L["img"]
            deform = L["depth"] >= 1 and len(self.layers) > 1 and (self.char or self.parts)
            if deform:
                fn = self._deform_fn(tl, S, c, s, offx, offy, pxc, pyc)
                res = im.transform((W, H), Image.MESH, build_mesh(W, H, 18, 32, fn), Image.BILINEAR)
            else:
                # src = centro + R(-rot)·(tela − meio − off)/S
                a, b = c / S, s / S
                d, e = -s / S, c / S
                x0, y0 = -(W / 2 + offx), -(H / 2 + offy)
                coeffs = (a, b, pxc + a * x0 + b * y0, d, e, pyc + d * x0 + e * y0)
                res = im.transform((W, H), Image.AFFINE, coeffs, Image.BILINEAR)
            if out is None:
                if res.mode == "RGBA":
                    base = Image.fromarray(self.fit_bg.astype(np.uint8)) if self.fill == "fit_blur" else \
                        Image.new("RGB", (W, H))
                    if self.silhouette:
                        res = self._silhouette(res)
                    base.paste(res, (0, 0), res)
                    out = base
                else:
                    if self.fill == "fit_blur":
                        base = Image.fromarray(self.fit_bg.astype(np.uint8))
                        mask = Image.new("L", im.size, 255).transform((W, H), Image.AFFINE, coeffs, Image.BILINEAR)
                        base.paste(res, (0, 0), mask)
                        out = base
                    else:
                        out = res
            else:
                if self.silhouette and res.mode == "RGBA":
                    res = self._silhouette(res)
                out.paste(res, (0, 0), res)
        return np.asarray(out, np.float32)

    def _silhouette(self, rgba):
        col = util.hex_color(self.silhouette if isinstance(self.silhouette, str) else "#000000")
        a = rgba.split()[-1]
        solid = Image.new("RGBA", rgba.size, col + (255,))
        solid.putalpha(a)
        return solid

    def _deform_fn(self, tl, S, c, s, offx, offy, pxc, pyc):
        ch = self.char
        t = self.shot["start"] + tl
        bbox = self.prep.get("subject_bbox", [0.3, 0.1, 0.7, 1.0])
        kw, kh = self.kw, self.kh
        ax, ay = (bbox[0] + bbox[2]) / 2 * kw, bbox[3] * kh  # âncora: base do personagem
        bh = max(1.0, (bbox[3] - bbox[1]) * kh)
        breathe = ch.get("breathe", 0.0) * 0.006 * math.sin(2 * math.pi * t / 3.6)
        sway = ch.get("sway", 0.0) * 0.6 * math.sin(2 * math.pi * t / 5.1 + 0.7)
        flutter = ch.get("flutter", 0.0)
        cs, sn = _rot(-sway)
        edge = self.edge_map
        parts = self.parts
        u = min(1.0, max(0.0, tl / max(1e-6, self.shot["dur"])))

        def fn(X, Y):
            dx, dy = X - self.W / 2 - offx, Y - self.H / 2 - offy
            SX = pxc + (c * dx + s * dy) / S
            SY = pyc + (-s * dx + c * dy) / S
            # respiração (escala vertical presa na base) e balanço (rotação em torno da base)
            SY = ay + (SY - ay) / (1 + breathe)
            rx, ry = SX - ax, SY - ay
            SX, SY = ax + cs * rx - sn * ry, ay + sn * rx + cs * ry
            if parts:
                for p in parts:
                    ang = float(np.interp(u, [q[0] for q in p["rot"]], [q[1] for q in p["rot"]]))
                    if abs(ang) < 1e-3:
                        continue
                    wv = _sample(p["w"], SX / kw, SY / kh)
                    pcx, pcy = p["pivot"][0] * kw, p["pivot"][1] * kh
                    ca, sa = _rot(-ang)
                    qx, qy = SX - pcx, SY - pcy
                    RX, RY = pcx + ca * qx - sa * qy, pcy + sa * qx + ca * qy
                    SX, SY = SX + (RX - SX) * wv, SY + (RY - SY) * wv
            if flutter and edge is not None:
                wv = _sample(edge, SX / kw, SY / kh)
                yrel = np.clip((ay - SY) / bh, 0, 1)
                SX = SX - flutter * 0.006 * kw * wv * yrel * np.sin(2 * math.pi * (1.3 * t - SY / (0.35 * bh)))
            return SX, SY
        return fn

    def _clip_frame(self, tl, cam, extra_off):
        c = self.shot.get("clip", {})
        spd = c.get("speed", 1.0)
        dur = self.shot["dur"]
        if isinstance(spd, list):
            us = np.linspace(0, 1, 101)
            vs = np.interp(us, [p[0] for p in spd], [p[1] for p in spd])
            cum = np.concatenate([[0], np.cumsum((vs[1:] + vs[:-1]) / 2 * np.diff(us))]) * dur
            src_t = float(np.interp(min(tl, dur) / max(dur, 1e-6), us, cum)) + max(0, tl - dur) * vs[-1]
            slow = min(vs) < 0.75
        else:
            src_t = tl * float(spd)
            slow = float(spd) < 0.75
        if self.kind == "sequence":
            sfps = c.get("fps", 12)
            i = int(src_t * sfps)
            if c.get("loop", True):
                i %= len(self.seq)
            im = Image.open(self.seq[min(i, len(self.seq) - 1)]).convert("RGBA")
            bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
            bg.alpha_composite(im)
            frame = np.asarray(bg.convert("RGB").resize((self.kw, self.kh), Image.LANCZOS))
        else:
            frame = self.clip.get(src_t, blend=slow)
            if frame is None:
                frame = np.zeros((self.kh, self.kw, 3), np.uint8)
        im = Image.fromarray(frame)
        S, cc, ss, offx, offy, pxc, pyc = self._layer_map(cam, 1.0, extra_off)
        a, b = cc / S, ss / S
        d, e = -ss / S, cc / S
        x0, y0 = -(self.W / 2 + offx), -(self.H / 2 + offy)
        coeffs = (a, b, pxc + a * x0 + b * y0, d, e, pyc + d * x0 + e * y0)
        res = im.transform((self.W, self.H), Image.AFFINE, coeffs, Image.BILINEAR)
        if self.fill == "fit_blur":
            if not hasattr(self, "fit_bg"):
                small = im.resize((max(1, im.width // 8), max(1, im.height // 8)), Image.BILINEAR)
                s2 = max(self.W / small.width, self.H / small.height) * 1.1
                bb = small.filter(ImageFilter.GaussianBlur(5)).resize(
                    (int(small.width * s2), int(small.height * s2)), Image.BILINEAR)
                x0b, y0b = (bb.width - self.W) // 2, (bb.height - self.H) // 2
                self.fit_bg_clip = np.asarray(bb.crop((x0b, y0b, x0b + self.W, y0b + self.H)), np.float32) * 0.45
            base = Image.fromarray(getattr(self, "fit_bg_clip").astype(np.uint8))
            mask = Image.new("L", im.size, 255).transform((self.W, self.H), Image.AFFINE, coeffs, Image.BILINEAR)
            base.paste(res, (0, 0), mask)
            res = base
            if tl > 0.5:  # atualiza o fundo borrado de vez em quando
                self.__dict__.pop("fit_bg_clip", None)
        return np.asarray(res, np.float32)

    # -- quadro final do plano (geometria + motion blur + pós)
    def frame(self, tl, fidx, next_shot_tr=None):
        cam = self.camera(tl)
        dt = 1.0 / self.fps
        cam2 = self.camera(tl + dt)
        # deslocamento na tela entre quadros (centro) → decide subamostras de motion blur
        S = self.s0 * cam["z"]
        disp = math.hypot((cam2["x"] - cam["x"]) * self.iw * S, (cam2["y"] - cam["y"]) * self.ih * S)
        disp += abs(cam2["z"] - cam["z"]) / max(cam["z"], 1e-6) * max(self.W, self.H) / 2
        disp += math.hypot(cam2["sx"] - cam["sx"], cam2["sy"] - cam["sy"])
        disp *= self.edit.get("motion_blur", 1.0)
        n = 1 if disp < 7 * self.scale or self.edit.get("motion_blur", 1.0) == 0 else min(5, int(math.ceil(disp / (6 * self.scale))))
        if n > 1:
            acc = None
            for i in range(n):
                tt = tl + (i / (n - 1) - 0.5) * 0.5 * dt  # obturador 180°
                g = self.geometry(tt, self.camera(tt))
                acc = g if acc is None else acc + g
            f = acc / n
        else:
            f = self.geometry(tl, cam)
        return self.post(f, tl, cam, fidx)

    def post(self, f, tl, cam, fidx):
        e, sh = self.edit, self.shot
        t = sh["start"] + tl
        g = sh.get("grade", e.get("grade", "neutro"))
        f = fx.grade(f, g, amount=sh.get("grade_amount", e.get("grade_amount", 1.0)))
        u = min(1.0, max(0.0, tl / max(sh["dur"], 1e-6)))
        imp = cam.get("imp", 0.0)
        st = self.imp_style
        glow_amt = e.get("glow", 0.0)
        chroma_amt = e.get("chroma", 0.0) + st["chroma"] * imp
        rgb = st["rgb"] * imp * self.scale
        for item in sh.get("fx", []):
            ty = item.get("type")
            t0, t1 = item.get("t0", sh["start"]), item.get("t1", sh["start"] + sh["dur"])
            if not (t0 <= t <= t1) and ty not in ("glow", "chroma"):
                continue
            k = (t - t0) / max(1e-6, t1 - t0)
            if ty == "glow":
                glow_amt = item.get("amount", 0.4)
            elif ty == "chroma":
                chroma_amt += item.get("amount", 0.004)
            elif ty == "exposure":
                f = fx.exposure(f, float(np.interp(k, [p[0] for p in item["ev"]], [p[1] for p in item["ev"]])))
            elif ty == "light_sweep":
                f = fx.light_sweep(f, k, item.get("angle", 25), item.get("width", 0.08), item.get("intensity", 0.6),
                                   util.hex_color(item.get("color"), (255, 240, 210)))
            elif ty == "light_leak":
                f = fx.light_leak(f, k, util.hex_color(item.get("color"), (255, 150, 60)), item.get("intensity", 0.55))
            elif ty == "glitch":
                f = fx.glitch(f, item.get("strength", 0.8), seed=fidx)
            elif ty == "wave":
                f = fx.wave(f, item.get("amount", 8) * self.scale * (1 - k), item.get("freq", 3), t)
            elif ty == "rgb_split":
                rgb += item.get("amount", 6) * self.scale
            elif ty == "flash":
                f = fx.flash(f, (1 - k) ** 2 * item.get("strength", 1.0), util.hex_color(item.get("color")))
            elif ty == "zoom_burst":
                f = fx.zoom_burst(f, item.get("amount", 0.08) * (1 - k))
            elif ty == "invert":
                f = fx.invert(f, item.get("amount", 1.0))
        if glow_amt:
            f = fx.glow(f, glow_amt, e.get("glow_threshold", 170))
        if chroma_amt > 0.0005:
            f = fx.chroma(f, chroma_amt)
        if rgb >= 1:
            f = fx.rgb_split(f, rgb)
        if st["flash"] and imp > 0.6:
            f = fx.flash(f, (imp - 0.6) * st["flash"])
        tex = e.get("texture")
        if tex:
            f = fx.texture(f, tex.get("path"), tex.get("mode", "overlay"), tex.get("opacity", 0.25))
        return f

    def close(self):
        if self.clip:
            self.clip.close()


def _sample(arr, u, v):
    """Amostragem bilinear de um mapa 2D (0–1 coords)."""
    h, w = arr.shape
    x = np.clip(u * (w - 1), 0, w - 1)
    y = np.clip(v * (h - 1), 0, h - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
    fx_, fy_ = x - x0, y - y0
    return (arr[y0, x0] * (1 - fx_) * (1 - fy_) + arr[y0, x1] * fx_ * (1 - fy_) +
            arr[y1, x0] * (1 - fx_) * fy_ + arr[y1, x1] * fx_ * fy_)


# ---------------------------------------------------------------- transições + pós global


def _apply_global(f, edit, t, fidx, scale):
    fo = edit.get("fade_out", 0)
    total = edit.get("duration") or 0
    if fo and total and t > total - fo:
        f = f * max(0.0, (total - t) / fo)
    fi = edit.get("fade_in", 0)
    if fi and t < fi:
        f = f * (t / fi)
    if edit.get("vignette", 0):
        f = fx.vignette(f, edit["vignette"])
    if edit.get("letterbox"):
        f = fx.letterbox(f, edit["letterbox"])
    if edit.get("grain", 0):
        f = fx.grain(f, edit["grain"], fidx)
    for tx in edit.get("text", []):
        if tx["start"] <= t < tx["end"]:
            u = (t - tx["start"]) / max(1e-6, tx["end"] - tx["start"])
            f = fx.draw_text(f, tx["text"], u, tx.get("style", "impact"), tuple(tx.get("pos", (0.5, 0.78))),
                             tx.get("size", 0.075), util.hex_color(tx.get("color")), tx.get("font"), fidx)
    return f


def _transition(sr, prev_r, next_tr, tl, fidx, f):
    """Aplica transição de entrada (deste plano) e de saída (para o próximo)."""
    sh = sr.shot
    tr = sh.get("transition_in") or {"type": "cut"}
    ty, d = tr.get("type", "cut"), float(tr.get("dur", 0.2))
    W = sr.W
    if ty != "cut" and tl < d:
        k = tl / d
        if ty == "flash":
            f = fx.flash(f, (1 - k) ** 2 * tr.get("strength", 1.0), util.hex_color(tr.get("color")))
        elif ty in ("dissolve", "wipe", "iris") and prev_r is not None:
            fp = prev_r.post(prev_r.geometry(prev_r.shot["dur"] + tl), prev_r.shot["dur"] + tl,
                             prev_r.camera(prev_r.shot["dur"] + tl), fidx)
            if ty == "dissolve":
                e = motion.ease("inOutSine", k)
                f = fp * (1 - e) + f * e
            elif ty == "wipe":
                f = fx.wipe(fp, f, motion.ease("inOutCubic", k), tr.get("angle", 20))
            else:
                f = fx.iris(fp, f, motion.ease("outCubic", k))
        elif ty == "dip":
            if k < 0.5:
                f = f * 0.0
            else:
                f = f * motion.ease("outSine", (k - 0.5) * 2)
        elif ty == "whip":
            sgn = -1 if tr.get("dir", "left") == "left" else 1
            e = 1 - motion.ease("outExpo", k)
            off = sgn * -e * W * 0.6
            f = fx.dir_blur(np.roll(f, int(off), axis=1), e * W * 0.35, 0)
        elif ty == "zoom_burst":
            f = fx.zoom_burst(f, 0.25 * (1 - k))
        elif ty == "glitch":
            f = fx.glitch(f, 1.0 - k, seed=fidx * 7 + 3)
        elif ty == "light_leak":
            f = fx.light_leak(f, 0.5 + 0.5 * k, util.hex_color(tr.get("color"), (255, 150, 60)), 0.8)
    if next_tr:
        ty, d = next_tr.get("type", "cut"), float(next_tr.get("dur", 0.2))
        rem = sh["dur"] - tl
        if ty == "dip" and rem < d / 2:
            f = f * motion.ease("inSine", rem / (d / 2))
        elif ty == "whip" and rem < d:
            k = 1 - rem / d
            sgn = -1 if next_tr.get("dir", "left") == "left" else 1
            e = motion.ease("inExpo", k)
            f = fx.dir_blur(np.roll(f, int(sgn * e * W * 0.6), axis=1), e * W * 0.35, 0)
        elif ty == "zoom_burst" and rem < d / 2:
            f = fx.zoom_burst(f, 0.25 * (1 - rem / (d / 2)))
        elif ty == "glitch" and rem < min(d, 0.1):
            f = fx.glitch(f, 0.8, seed=fidx * 5 + 1)
        elif ty == "light_leak" and rem < d / 2:
            f = fx.light_leak(f, 0.5 * (1 - rem / (d / 2)), util.hex_color(next_tr.get("color"), (255, 150, 60)), 0.8)
    return f


# ---------------------------------------------------------------- orquestração


def _encoder_args(gpu, preview, fps):
    if gpu:
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "19", "-pix_fmt", "yuv420p"]
    return ["-c:v", "libx264", "-preset", "veryfast" if preview else "medium", "-crf", "23" if preview else "18",
            "-maxrate", "8M" if preview else "20M", "-bufsize", "40M", "-pix_fmt", "yuv420p", "-g", str(int(fps * 2)),
            "-threads", "2"]


def gpu_available():
    try:
        p = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=256x256:d=0.1", "-c:v",
                            "h264_nvenc", "-f", "null", "-"], capture_output=True, timeout=30)
        return p.returncode == 0
    except Exception:  # noqa
        return False


def _prepare_shots(edit):
    shots = edit["shots"]
    imps = edit.get("impacts", [])
    for i, sh in enumerate(shots):
        sh.setdefault("id", f"s{i:02d}")
        a, b = sh["start"] - 0.05, sh["start"] + sh["dur"] + 0.3
        sh["_impacts"] = [x for x in imps if a <= x["t"] < b] + [
            {"t": f_["t"], "s": f_.get("s", 1.0)} for f_ in sh.get("fx", []) if f_.get("type") == "impact"]
    return shots


def _render_shot(args):
    proj, edit, idx, W, H, fps, scale, seg_path, gpu, preview = args
    shots = edit["shots"]
    sh = shots[idx]
    t_start = time.time()
    sr = ShotRenderer(proj, edit, sh, W, H, fps, scale)
    prev_r = None
    tr = (sh.get("transition_in") or {}).get("type", "cut")
    if idx > 0 and tr in ("dissolve", "wipe", "iris"):
        prev_r = ShotRenderer(proj, edit, shots[idx - 1], W, H, fps, scale)
    next_tr = shots[idx + 1].get("transition_in") if idx + 1 < len(shots) else None
    f0 = int(round(sh["start"] * fps))
    f1 = int(round((sh["start"] + sh["dur"]) * fps))
    cmd = ["ffmpeg", "-v", "error", "-y", "-nostdin", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-"] + _encoder_args(gpu, preview, fps) + ["-an", seg_path]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for fi in range(f0, f1):
            t = fi / fps
            tl = t - sh["start"]
            f = sr.frame(tl, fi, next_tr)
            f = _transition(sr, prev_r, next_tr, tl, fi, f)
            f = _apply_global(f, edit, t, fi, scale)
            enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
        enc.stdin.close()
        err = enc.stderr.read().decode()
        enc.wait()
        if enc.returncode != 0:
            raise RuntimeError(f"ffmpeg falhou no plano {sh['id']}: {err[-500:]}")
    finally:
        sr.close()
        if prev_r:
            prev_r.close()
    return idx, f1 - f0, round(time.time() - t_start, 1)


def render(proj, out=None, preview=False, scale=None, workers=None, gpu=False, t_range=None, keep_segments=False):
    edit = util.load_json(os.path.join(proj, "edit.json"))
    if not edit:
        util.die("edit.json não encontrado (rode `plan` antes)")
    pj = project.load_project(proj)
    fmt = edit.get("format") or pj["format"]
    sc = scale or (0.5 if preview else 1.0)
    W, H = int(round(fmt["w"] * sc / 2) * 2), int(round(fmt["h"] * sc / 2) * 2)
    fps = int(edit.get("fps", fmt.get("fps", 30)))
    shots = _prepare_shots(edit)
    idxs = list(range(len(shots)))
    if t_range:
        a, b = t_range
        idxs = [i for i, s in enumerate(shots) if s["start"] < b and s["start"] + s["dur"] > a]
    if gpu and not gpu_available():
        util.log("GPU/NVENC indisponível — usando CPU (libx264)")
        gpu = False
    segdir = os.path.join(proj, "work", "segments" + ("_prev" if preview else ""))
    os.makedirs(segdir, exist_ok=True)
    jobs = [(proj, edit, i, W, H, fps, sc, os.path.join(segdir, f"{i:03d}.mp4"), gpu, preview) for i in idxs]
    nw = workers or max(1, min(len(jobs), (os.cpu_count() or 2)))
    t0 = time.time()
    util.log(f"render {len(jobs)} planos · {W}x{H} @ {fps} fps · {nw} processos · {'GPU' if gpu else 'CPU'}")
    # planos mais longos primeiro (melhor balanceamento)
    jobs.sort(key=lambda j: -shots[j[2]]["dur"])
    if nw == 1:
        results = [_render_shot(j) for j in jobs]
    else:
        ctx = mp.get_context("fork")
        with ctx.Pool(nw) as pool:
            results = []
            for r in pool.imap_unordered(_render_shot, jobs):
                results.append(r)
                util.log(f"  plano {r[0]:02d}: {r[1]} quadros em {r[2]}s")
    nframes = sum(r[1] for r in results)
    lst = os.path.join(segdir, "lista.txt")
    with open(lst, "w") as f:
        for i in sorted(idxs):
            f.write(f"file '{os.path.join(segdir, f'{i:03d}.mp4')}'\n")
    out = out or os.path.join(proj, "output", ("previa" if preview else "final") + ".mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    vtmp = os.path.join(segdir, "video.mp4")
    util.run(["ffmpeg", "-v", "error", "-y", "-nostdin", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vtmp])
    first = shots[min(idxs)]["start"]
    vdur = nframes / fps
    audio = edit.get("audio")
    if audio:
        apath = audio if os.path.isabs(audio) else os.path.join(proj, audio)
        ast = float(edit.get("audio_start", 0.0)) + first
        cmd = ["ffmpeg", "-v", "error", "-y", "-nostdin", "-i", vtmp, "-ss", f"{ast:.3f}", "-i", apath, "-t",
               f"{vdur:.3f}", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k"]
        fo = edit.get("audio_fade_out", 0.0)
        if fo and not t_range:
            cmd += ["-af", f"afade=t=out:st={max(0, vdur - fo):.3f}:d={fo:.3f}"]
        cmd += ["-movflags", "+faststart", out]
        util.run(cmd)
    else:
        util.run(["ffmpeg", "-v", "error", "-y", "-nostdin", "-i", vtmp, "-c", "copy", "-movflags", "+faststart", out])
    if not keep_segments and not preview:
        for i in idxs:
            p = os.path.join(segdir, f"{i:03d}.mp4")
            if os.path.exists(p):
                os.remove(p)
    el = time.time() - t0
    util.log(f"pronto: {out} · {nframes} quadros · {vdur:.2f}s · {el:.0f}s de render ({nframes / max(el, 1e-6):.1f} q/s)")
    return out


def stills(proj, times, outdir=None, scale=0.5):
    """Renderiza quadros soltos (revisão rápida, sem encode)."""
    edit = util.load_json(os.path.join(proj, "edit.json"))
    pj = project.load_project(proj)
    fmt = edit.get("format") or pj["format"]
    W, H = int(round(fmt["w"] * scale / 2) * 2), int(round(fmt["h"] * scale / 2) * 2)
    fps = int(edit.get("fps", fmt.get("fps", 30)))
    shots = _prepare_shots(edit)
    outdir = outdir or os.path.join(proj, "work", "stills_review")
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for t in times:
        idx = max([i for i, s in enumerate(shots) if s["start"] <= t] or [0])
        sh = shots[idx]
        sr = ShotRenderer(proj, edit, sh, W, H, fps, scale)
        prev_r = ShotRenderer(proj, edit, shots[idx - 1], W, H, fps, scale) if idx > 0 and (
            sh.get("transition_in") or {}).get("type") in ("dissolve", "wipe", "iris") else None
        fi = int(round(t * fps))
        tl = fi / fps - sh["start"]
        nxt = shots[idx + 1].get("transition_in") if idx + 1 < len(shots) else None
        f = sr.frame(tl, fi, nxt)
        f = _transition(sr, prev_r, nxt, tl, fi, f)
        f = _apply_global(f, edit, fi / fps, fi, scale)
        p = os.path.join(outdir, f"q_{t:07.3f}.jpg")
        Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).save(p, quality=90)
        paths.append(p)
        sr.close()
    return paths


def contact_sheet(paths, out, cols=4, width=1600):
    ims = [Image.open(p) for p in paths]
    if not ims:
        return None
    w0, h0 = ims[0].size
    cw = width // cols
    ch = int(h0 * cw / w0)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, ch * rows), (20, 20, 20))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((cw, ch), Image.BILINEAR), ((i % cols) * cw, (i // cols) * ch))
    sheet.save(out, quality=88)
    return out


def export_share(src, dst=None, max_mb=28.0):
    """Cópia leve para enviar no chat/celular (≤ ~28 MB), H.264 + AAC, mesma resolução."""
    info = util.video_info(src)
    dur = max(info["duration"], 0.1)
    kbps = int(min(9000, max_mb * 8 * 1024 / dur - 200))
    dst = dst or os.path.splitext(src)[0] + "_envio.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-nostdin", "-i", src, "-c:v", "libx264", "-preset", "medium",
           "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.4)}k", "-bufsize", f"{kbps * 2}k", "-pix_fmt", "yuv420p"]
    cmd += (["-c:a", "aac", "-b:a", "160k"] if info["has_audio"] else ["-an"]) + ["-movflags", "+faststart", dst]
    util.run(cmd)
    return dst
