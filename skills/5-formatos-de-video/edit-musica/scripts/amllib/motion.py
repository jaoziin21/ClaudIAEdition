"""Movimento: easing, keyframes, presets de câmera, shake suave, impulsos de impacto, speed ramp.

Estado de câmera (coordenadas da IMAGEM, normalizadas):
  x, y  centro do enquadramento (0–1)      z  zoom sobre o "cobrir quadro" (1 = imagem cobre a tela)
  r     rotação em graus                    px deriva de parallax (−1…1; move camadas conforme a profundidade)
"""
import math

import numpy as np

# ---------------------------------------------------------------- easing


def _back(u, s=1.70158):
    u -= 1
    return u * u * ((s + 1) * u + s) + 1


EASE = {
    "linear": lambda u: u,
    "inSine": lambda u: 1 - math.cos(u * math.pi / 2),
    "outSine": lambda u: math.sin(u * math.pi / 2),
    "inOutSine": lambda u: -(math.cos(math.pi * u) - 1) / 2,
    "inQuad": lambda u: u * u,
    "outQuad": lambda u: 1 - (1 - u) ** 2,
    "inOutQuad": lambda u: 2 * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 2 / 2,
    "inCubic": lambda u: u ** 3,
    "outCubic": lambda u: 1 - (1 - u) ** 3,
    "inOutCubic": lambda u: 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2,
    "inExpo": lambda u: 0 if u <= 0 else 2 ** (10 * u - 10),
    "outExpo": lambda u: 1 if u >= 1 else 1 - 2 ** (-10 * u),
    "inOutExpo": lambda u: (0 if u <= 0 else 1 if u >= 1 else
                            (2 ** (20 * u - 10) / 2 if u < 0.5 else (2 - 2 ** (-20 * u + 10)) / 2)),
    "outBack": _back,
    "hold": lambda u: 0.0,
}
FIELDS = ("x", "y", "z", "r", "px")
DEFAULT = {"x": 0.5, "y": 0.5, "z": 1.0, "r": 0.0, "px": 0.0}


def ease(name, u):
    u = min(1.0, max(0.0, u))
    return EASE.get(name or "inOutSine", EASE["inOutSine"])(u)


def interp_keys(keys, u):
    """keys: [{"t":0..1, x,y,z,r,px, "ease": nome do trecho que CHEGA nesta key}]"""
    if not keys:
        return dict(DEFAULT)
    keys = sorted(keys, key=lambda k: k["t"])
    full = []
    prev = dict(DEFAULT)
    for k in keys:
        st = dict(prev)
        st.update({f: k[f] for f in FIELDS if f in k})
        st["t"] = k["t"]
        st["ease"] = k.get("ease", "inOutSine")
        full.append(st)
        prev = st
    if u <= full[0]["t"]:
        return {f: full[0][f] for f in FIELDS}
    for a, b in zip(full, full[1:]):
        if u <= b["t"]:
            span = max(1e-9, b["t"] - a["t"])
            e = ease(b["ease"], (u - a["t"]) / span)
            return {f: a[f] + (b[f] - a[f]) * e for f in FIELDS}
    return {f: full[-1][f] for f in FIELDS}


# ---------------------------------------------------------------- presets


def expand_preset(name, focus=(0.5, 0.45), intensity=1.0, wide=None, ease_name=None):
    """Gera keyframes para um preset. focus = ponto de interesse (ex.: rosto), wide = centro do plano aberto."""
    fx, fy = focus
    wx, wy = wide or (0.5, 0.5)
    I = float(intensity)
    P = {
        "push_in_slow": [dict(t=0, x=wx, y=wy, z=1.02), dict(t=1, x=fx, y=fy, z=1.02 + 0.13 * I, ease=ease_name or "inOutSine")],
        "push_in_fast": [dict(t=0, x=wx, y=wy, z=1.0), dict(t=1, x=fx, y=fy, z=1.0 + 0.38 * I, ease=ease_name or "outExpo")],
        "pull_out": [dict(t=0, x=fx, y=fy, z=1.0 + 0.3 * I), dict(t=1, x=wx, y=wy, z=1.0, ease=ease_name or "outCubic")],
        "pan_lr": [dict(t=0, x=0.0, y=fy, z=1.12 + 0.05 * I), dict(t=1, x=1.0, y=fy, ease=ease_name or "inOutSine")],
        "pan_rl": [dict(t=0, x=1.0, y=fy, z=1.12 + 0.05 * I), dict(t=1, x=0.0, y=fy, ease=ease_name or "inOutSine")],
        "tilt_up": [dict(t=0, x=fx, y=1.0, z=1.1 + 0.05 * I), dict(t=1, x=fx, y=0.0, ease=ease_name or "inOutSine")],
        "tilt_down": [dict(t=0, x=fx, y=0.0, z=1.1 + 0.05 * I), dict(t=1, x=fx, y=1.0, ease=ease_name or "inOutSine")],
        "zoom_accel": [dict(t=0, x=wx, y=wy, z=1.0), dict(t=1, x=fx, y=fy, z=1.0 + 0.32 * I, ease=ease_name or "inCubic")],
        "reframe": [dict(t=0, x=wx, y=wy, z=1.02), dict(t=0.48, x=wx, y=wy, z=1.06, ease="linear"),
                    dict(t=0.56, x=fx, y=fy, z=1.55 + 0.25 * I, ease="outExpo"),
                    dict(t=1, x=fx, y=fy, z=1.62 + 0.25 * I, ease="linear")],
        "orbit": [dict(t=0, x=wx, y=wy, z=1.06, r=-0.8 * I, px=-1.0),
                  dict(t=1, x=wx, y=wy, z=1.12, r=0.8 * I, px=1.0, ease=ease_name or "inOutSine")],
        "dutch_push": [dict(t=0, x=wx, y=wy, z=1.04, r=0.0), dict(t=1, x=fx, y=fy, z=1.2 + 0.1 * I, r=-3.0 * I,
                                                                   ease=ease_name or "inOutCubic")],
        "drift": [dict(t=0, x=wx - 0.04, y=wy, z=1.05), dict(t=1, x=wx + 0.04, y=wy, z=1.08, ease=ease_name or "linear")],
        "hold": [dict(t=0, x=fx, y=fy, z=1.04), dict(t=1, x=fx, y=fy, z=1.06, ease="linear")],
        "close_hold": [dict(t=0, x=fx, y=fy, z=1.7), dict(t=1, x=fx, y=fy, z=1.78, ease="linear")],
    }
    if name not in P:
        raise ValueError(f"preset de câmera desconhecido: {name} (opções: {', '.join(sorted(P))})")
    return P[name]


CAMERA_PRESETS = sorted([
    "push_in_slow", "push_in_fast", "pull_out", "pan_lr", "pan_rl", "tilt_up", "tilt_down", "zoom_accel",
    "reframe", "orbit", "dutch_push", "drift", "hold", "close_hold"])


# ---------------------------------------------------------------- tempo / impulsos


def remap(u, ramp):
    """Speed ramp: ramp=[[u0,vel0],[u1,vel1],...] (vel relativa). Devolve progresso u' (0–1) com a mesma
    duração total: integra a velocidade e normaliza."""
    if not ramp:
        return u
    pts = sorted(ramp)
    us = np.linspace(0, 1, 201)
    vs = np.interp(us, [p[0] for p in pts], [max(1e-3, p[1]) for p in pts])
    cum = np.concatenate([[0], np.cumsum((vs[1:] + vs[:-1]) / 2 * np.diff(us))])
    cum /= cum[-1]
    return float(np.interp(u, us, cum))


def impulse(t, events, tau=0.18, attack=0.035):
    """Soma de impulsos (ataque rápido, decaimento exponencial). events=[(t_i, força)]."""
    v = 0.0
    for ti, s in events:
        d = t - ti
        if d < -attack or d > tau * 6:
            continue
        if d < 0:
            v += s * (1 + d / attack)  # sobe nos ~1 quadro antes do golpe
        else:
            v += s * math.exp(-d / tau)
    return v


class Shake:
    """Tremor suave e determinístico (soma de senos com fases sorteadas)."""

    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        self.fx = rng.uniform(5, 13, 3)
        self.fy = rng.uniform(5, 13, 3)
        self.fr = rng.uniform(3, 8, 2)
        self.px = rng.uniform(0, 2 * math.pi, 3)
        self.py = rng.uniform(0, 2 * math.pi, 3)
        self.pr = rng.uniform(0, 2 * math.pi, 2)

    def __call__(self, t, amp):
        """amp em fração da altura do quadro. Devolve (dx, dy, drot_graus)."""
        if amp <= 0:
            return 0.0, 0.0, 0.0
        dx = sum(math.sin(2 * math.pi * f * t + p) for f, p in zip(self.fx, self.px)) / 3
        dy = sum(math.sin(2 * math.pi * f * t + p) for f, p in zip(self.fy, self.py)) / 3
        dr = sum(math.sin(2 * math.pi * f * t + p) for f, p in zip(self.fr, self.pr)) / 2
        return dx * amp, dy * amp, dr * amp * 40
