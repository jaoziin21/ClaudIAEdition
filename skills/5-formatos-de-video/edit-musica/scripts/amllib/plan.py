"""Planejamento automático do edit → edit.json (+ metadata/plano.md explicando cada decisão).

Entradas: assets aprovados/preparados, análise do áudio (opcional), preset de direção (rap | cinematico |
contemplativo), perfil de referência (opcional, de reference.py). Sem áudio: grade de ritmo VIRTUAL (não se cria
som nenhum) com arco de energia intro → crescimento → clímax → final.
"""
import os

import numpy as np

from . import project, util

PRESETS = {
    "rap": dict(beats={"low": 4, "mid": 2, "high": 1}, min_shot=0.38, bpm=100, grade="anime_rap", grain=0.05,
                vignette=0.35, impact=dict(zoom=0.085, shake=0.014, chroma=0.004, rgb=6, flash=0.5, tau=0.15),
                cams={"low": ["push_in_slow", "orbit", "drift", "pull_out", "tilt_down"],
                      "mid": ["orbit", "dutch_push", "push_in_slow", "reframe", "pan_lr", "pull_out"],
                      "high": ["push_in_fast", "zoom_accel", "close_hold", "pull_out", "reframe", "push_in_fast"]},
                trans={"section": ["flash", "zoom_burst"], "strong": ["whip", "glitch", "flash", "cut", "zoom_burst"],
                       "normal": ["cut", "cut", "cut", "whip", "cut", "glitch"]}),
    "cinematico": dict(beats={"low": 8, "mid": 4, "high": 2}, min_shot=0.8, bpm=85, grade="epico", grain=0.04,
                       vignette=0.3, impact=dict(zoom=0.045, shake=0.006, chroma=0.002, rgb=2, flash=0.2, tau=0.22),
                       cams={"low": ["push_in_slow", "orbit", "pull_out", "drift"],
                             "mid": ["orbit", "push_in_slow", "dutch_push", "tilt_up", "pull_out"],
                             "high": ["push_in_fast", "reframe", "pull_out", "zoom_accel"]},
                       trans={"section": ["light_leak", "dip", "flash"], "strong": ["cut", "flash", "whip"],
                              "normal": ["cut", "dissolve", "cut"]}),
    "contemplativo": dict(beats={"low": 8, "mid": 8, "high": 4}, min_shot=2.0, bpm=72, grade="dourado", grain=0.035,
                          vignette=0.3, impact=dict(zoom=0.015, shake=0.0, chroma=0.0, rgb=0, flash=0.0, tau=0.4),
                          cams={"low": ["push_in_slow", "drift", "pull_out", "orbit"],
                                "mid": ["push_in_slow", "orbit", "tilt_up", "pull_out"],
                                "high": ["push_in_slow", "orbit", "pull_out"]},
                          trans={"section": ["dip", "light_leak"], "strong": ["dissolve", "light_leak"],
                                 "normal": ["dissolve", "dissolve", "cut"]}),
}
FRAMING_ORDER = {
    "intro": ["silhueta", "contemplativo", "medio", "aberto", "close"],
    "build": ["medio", "close", "acao", "aberto"],
    "climax": ["close", "acao", "medio", "clipe"],
    "final": ["silhueta", "contemplativo", "medio", "close"],
}


def _level(e):
    return "low" if e < 0.35 else ("mid" if e < 0.68 else "high")


def _phase(t, dur, sections=None):
    if sections:
        for s in sections:
            if s["start"] <= t < s["end"]:
                return {"intro": "intro", "verso": "build", "build": "build", "pausa": "intro",
                        "refrao": "climax", "climax": "climax", "final": "final", "unico": "build"}.get(s["label"], "build")
    u = t / max(dur, 1e-6)
    return "intro" if u < 0.18 else ("build" if u < 0.5 else ("climax" if u < 0.86 else "final"))


def virtual_energy(dur, rate=10):
    """Arco de energia para edit SEM música (só orienta o ritmo visual)."""
    u = np.linspace(0, 1, max(2, int(dur * rate)))
    e = np.interp(u, [0, 0.15, 0.45, 0.5, 0.56, 0.84, 0.92, 1.0], [0.25, 0.3, 0.62, 0.45, 0.95, 1.0, 0.55, 0.35])
    return e


def make_plan(proj, preset=None, duration=None, audio=None, audio_start=0.0, seed=7, bpm=None, assets=None,
              reference=None, manga=None, text=None, fps=None):
    rng = np.random.default_rng(seed)
    pj = project.load_project(proj)
    man = project.load_manifest(proj)
    subj = util.load_json(os.path.join(proj, "metadata", "subject.json"), {}) or {}
    preset = preset or (pj.get("preset") if pj.get("preset") not in (None, "auto") else None) or subj.get("preset", "rap")
    P = dict(PRESETS[preset])
    manga = subj.get("midia") == "manga" if manga is None else manga
    real_person = bool(subj.get("pessoa_real"))
    decisions = [f"preset de direção: {preset}" + (" · tratamento mangá (tinta P&B)" if manga else "")]

    # ---------------- áudio / grade de ritmo
    ana = None
    if audio:
        ap = audio if os.path.isabs(audio) else os.path.join(proj, audio)
        ana_path = os.path.join(proj, "audio", "analysis.json")
        ana = util.load_json(ana_path)
        if not ana or ana.get("file") != ap or float(ana.get("start", 0)) != float(audio_start):
            from . import audio as au
            ana = au.analyze(ap, start=audio_start, dur=duration)
            util.save_json(ana_path, ana)
        dur = min(duration or ana["duration"], ana["duration"])
        beats = [b for b in ana["beats"] if b < dur]
        if ana.get("tempo_confidence", 0) < 0.3 or len(beats) < 4:
            decisions.append(f"BPM pouco confiável ({ana.get('tempo_confidence')}) → cortes guiados pelos impactos/onsets")
            pts = sorted({round(o["t"], 3) for o in ana["onsets"] if o["strength"] > 0.3 and o["t"] < dur})
            beats = pts or list(np.arange(0.5, dur, 0.5))
        energy = np.array(ana["energy"])
        rate = ana.get("energy_rate", 10)
        sections = ana["sections"]
        impacts = [{"t": i["t"], "s": i["strength"]} for i in ana["impacts"] if i["t"] < dur]
        bpm_used = ana.get("tempo")
        decisions.append(f"áudio: {dur:.2f}s · BPM {bpm_used} · {len(impacts)} impactos · seções " +
                         ", ".join(f"{s['label']}({s['start']:.1f}s)" for s in sections))
    else:
        dur = float(duration or 20.0)
        bpm_used = bpm or P["bpm"]
        period = 60.0 / bpm_used
        beats = list(np.arange(period, dur, period))
        energy = virtual_energy(dur)
        rate = 10
        sections = None
        impacts = []
        for i, b in enumerate(beats):  # pulsos visuais (sem som) nos tempos fortes da parte intensa
            e = energy[min(len(energy) - 1, int(b * rate))]
            if e > 0.68 and i % 2 == 0:
                impacts.append({"t": round(float(b), 3), "s": 0.9 if i % 4 == 0 else 0.55})
            elif e > 0.5 and i % 4 == 0:
                impacts.append({"t": round(float(b), 3), "s": 0.6})
        decisions.append(f"sem música: grade de ritmo virtual {bpm_used} BPM com arco intro→clímax→final "
                         f"(nenhum áudio foi criado; vídeo sai mudo)")
    if reference:
        asl = reference.get("median_shot_len") or reference.get("avg_shot_len")
        if asl:
            decisions.append(f"referência: plano médio {asl:.2f}s → ajusta tamanhos dos planos")

    def e_at(t):
        return float(energy[min(len(energy) - 1, max(0, int(t * rate)))])

    # ---------------- pontos de corte
    beats = [b for b in beats if 0.2 < b < dur - 0.2]
    cuts = [0.0]
    i = 0
    downs = set(round(d, 3) for d in (ana.get("downbeats", []) if ana else beats[3::4]))
    climax_rise = None
    if ana and ana.get("rises"):
        climax_rise = max(ana["rises"], key=lambda r: e_at(r + 0.8) - e_at(r - 0.8))
    elif not ana:
        climax_rise = dur * 0.56
    if climax_rise and beats:  # o drop cai na batida mais próxima
        climax_rise = float(min(beats, key=lambda b: abs(b - climax_rise)))
    pause_done = False
    while True:
        t = cuts[-1]
        lvl = _level(e_at(t + 0.2))
        nb = P["beats"][lvl]
        if reference and (reference.get("median_shot_len") or reference.get("avg_shot_len")) and beats:
            per = np.median(np.diff(beats)) if len(beats) > 1 else 0.6
            nb = max(1, int(round(0.5 * nb + 0.5 * (reference.get("median_shot_len") or reference["avg_shot_len"]) / per)))
        if lvl == "high" and preset == "rap" and rng.random() < 0.25:
            nb = 2  # respiro dentro da parte intensa (ritmo variável)
        # pausa dramática logo antes do clímax: segura um plano lento até o 'drop'
        if climax_rise and not pause_done and t < climax_rise <= t + 2.6 and climax_rise - t > 1.0:
            nxt = climax_rise
            pause_done = True
            decisions.append(f"pausa dramática {t:.2f}–{nxt:.2f}s antes do clímax")
        else:
            fut = [b for b in beats if b > t + P["min_shot"] * 0.9]
            if not fut:
                break
            idx = min(len(fut) - 1, nb - 1)
            nxt = fut[idx]
            if nb >= 4:  # planos longos terminam preferencialmente num tempo forte
                cand = [b for b in fut[:nb + 2] if round(b, 3) in downs]
                if cand:
                    nxt = min(cand, key=lambda b: abs(b - fut[idx]))
        if dur - nxt < P["min_shot"] * 1.2:
            break
        cuts.append(float(nxt))
        i += 1
        if len(cuts) > 400:
            break
    cuts.append(dur)

    # ---------------- assets
    def _usable(a, r):
        if not r.get("approved", True):
            return False
        if r.get("kind") in ("video", "sequence"):
            return True
        return r.get("kind") == "image" and os.path.exists(os.path.join(proj, "assets", "processed", a, "prep.json"))
    aids = assets or [a for a, r in man["assets"].items() if _usable(a, r)]
    if not aids:
        util.die("nenhum asset aprovado/preparado (rode prep)")
    recs = {a: man["assets"][a] for a in aids}
    preps = {a: util.load_json(os.path.join(proj, "assets", "processed", a, "prep.json"), {}) or {} for a in aids}
    quality = {}
    from . import media
    for a in aids:
        q, _ = media.score_asset(recs[a], pj["format"])
        quality[a] = q + 0.2 * float(recs[a].get("relevance") or 0)
    used = {a: 0 for a in aids}
    used_cams = {a: set() for a in aids}

    def pick_asset(phase, last, prev2):
        order = FRAMING_ORDER[phase]
        best, bs = None, -1e9
        for a in aids:
            if a == last or a == prev2:
                continue
            fr = recs[a].get("framing") or ["medio"]
            fs = max([len(order) - order.index(f) for f in fr if f in order] or [0])
            s = fs * 0.6 + quality[a] * 2 - used[a] * 1.4 + rng.random() * 0.6
            if s > bs:
                best, bs = a, s
        return best or aids[0]

    W, H = pj["format"]["w"], pj["format"]["h"]
    shots = []
    last = prev2 = None
    last_zoom_dir = 0
    pan_dir = 1
    trans_counts = {}
    for k in range(len(cuts) - 1):
        st, en = cuts[k], cuts[k + 1]
        d = en - st
        e = e_at(st + d / 2)
        lvl = _level(e)
        phase = _phase(st, dur, sections)
        a = pick_asset(phase, last, prev2)
        prev2, last = last, a
        used[a] += 1
        rec, pr = recs[a], preps[a]
        is_clip = rec.get("kind") in ("video", "sequence")
        # câmera: evita repetir no mesmo asset e alterna zoom in/out
        pool = list(P["cams"][lvl])
        if d >= 1.6 and lvl != "low" and "reframe" not in pool:
            pool.append("reframe")
        if d < 0.9:
            pool = [c for c in pool if c not in ("reframe", "pan_lr", "tilt_down", "tilt_up")] or ["push_in_fast"]
        rng.shuffle(pool)
        pool.sort(key=lambda c: (c in used_cams[a]) * 2 + ((1 if c in ("push_in_slow", "push_in_fast", "zoom_accel",
                                                                          "dutch_push") else -1) == last_zoom_dir))
        # tilt/pan só onde a imagem tem folga naquele eixo (16:9 na vertical não tem folga vertical)
        if rec.get("w"):
            s_cov = max(W / rec["w"], H / rec["h"])
            room_y = 1 - (H / s_cov) / rec["h"] / 1.15
            room_x = 1 - (W / s_cov) / rec["w"] / 1.15
            pool = [c for c in pool if not ((c in ("tilt_up", "tilt_down") and room_y < 0.25) or
                                            (c in ("pan_lr", "pan_rl") and room_x < 0.25))] or ["push_in_slow"]
        cam = pool[0]
        if not pr.get("layers") or len(pr.get("layers", [])) < 2:
            cam = "push_in_slow" if cam == "orbit" else cam
        used_cams[a].add(cam)
        last_zoom_dir = 1 if cam in ("push_in_slow", "push_in_fast", "zoom_accel", "dutch_push") else -1
        if cam in ("pan_lr", "pan_rl"):
            cam = "pan_lr" if pan_dir > 0 else "pan_rl"
            pan_dir *= -1
        intensity = {"low": 0.8, "mid": 1.0, "high": 1.25}[lvl]
        if phase == "climax" and d < 0.8:
            intensity = 1.4
        sh = {"id": f"s{k:02d}", "asset": a, "start": round(st, 4), "dur": round(d, 4),
              "camera": {"preset": cam, "intensity": intensity}, "phase": phase, "energy": round(e, 2)}
        # enquadramento: personagem largo demais para o recorte vertical → plano aberto 'fit_blur'
        vis = (W / max(W / rec["w"], H / rec["h"])) / rec["w"] if rec.get("w") else 1
        bb = pr.get("subject_bbox")
        if not is_clip and d >= 1.5 and cam in ("pull_out", "drift") and (
                (bb and (bb[2] - bb[0]) > vis * 1.6) or ("aberto" in (rec.get("framing") or []) and pr.get("figures", 1) > 1)):
            sh["fill"] = "fit_blur"
        # zoom máximo útil pela resolução da fonte (evita ampliar 5x um 720p) e pelo quão fechado já é o quadro
        if rec.get("w") and not sh.get("fill"):
            s_cov = max(W / rec["w"], H / rec["h"])
            zcap = float(np.clip(3.4 / s_cov, 1.12, 2.2))
            if (pr.get("subject_coverage") or 0) > 0.5:
                zcap = min(zcap, 1.15)
            sh["zmax"] = round(zcap, 3)
        if is_clip:
            sh["technique"] = "clip"
            seg = (rec.get("segments") or [{"start": 0.0}])[used[a] % max(1, len(rec.get("segments") or [1]))]
            sh["clip"] = {"in": seg["start"], "speed": [[0, 1.4], [0.35, 0.45], [1, 1.0]] if lvl == "high" and d > 1.0
                          else 1.0}
            sh["camera"] = {"preset": "drift" if lvl == "low" else "push_in_slow", "intensity": 0.6}
        elif pr.get("technique") == "parallax" and (pr.get("parallax_max") or 0) >= 0.008:
            sh["technique"] = "parallax"
            sh["parallax"] = pr["parallax_max"]
            if not real_person and lvl != "high" and d > 1.0:
                sh["character"] = {"breathe": 1.0, "sway": 0.6 if lvl == "low" else 0.3,
                                   "flutter": 0.7 if preset != "rap" or lvl == "low" else 0.0}
        else:
            sh["technique"] = "camera"
        # transições
        if k > 0:
            sec_start = sections and any(abs(s["start"] - st) < 0.12 for s in sections[1:])
            strong = round(st, 3) in downs or any(abs(i_["t"] - st) < 0.08 and i_["s"] > 0.6 for i_ in impacts)
            key = "section" if (sec_start or (climax_rise and abs(st - climax_rise) < 0.05)) else (
                "strong" if strong else "normal")
            ty = P["trans"][key][int(rng.integers(0, len(P["trans"][key])))]
            if ty in ("dissolve", "wipe", "iris") and d < 0.9:
                ty = "cut"
            if trans_counts.get(ty, 0) > 0 and ty != "cut" and shots[-1].get("transition_in", {}).get("type") == ty:
                ty = "cut"
            trans_counts[ty] = trans_counts.get(ty, 0) + 1
            if ty != "cut":
                tr = {"type": ty, "dur": {"flash": 0.16, "whip": 0.22, "glitch": 0.12, "zoom_burst": 0.3,
                                          "dissolve": min(0.8, d * 0.4), "dip": 0.5, "light_leak": 0.7}.get(ty, 0.2)}
                if ty == "whip":
                    tr["dir"] = "left" if k % 2 else "right"
                if ty == "flash" and manga and phase == "climax":
                    tr["color"] = "#ff2a2a" if k % 3 == 0 else "#ffffff"
                sh["transition_in"] = tr
        # efeitos do plano (cada um com função clara, nunca todos juntos)
        fxl = []
        if phase in ("intro", "final") and d >= 1.5 and preset != "rap":
            fxl.append({"type": "light_sweep", "t0": st + d * 0.2, "t1": st + d * 0.9, "intensity": 0.45})
        if preset == "rap" and lvl == "high" and rng.random() < 0.3:
            b = next((x for x in beats if st + 0.1 < x < en - 0.1), None)
            if b:
                fxl.append({"type": "glitch", "t0": b - 0.03, "t1": b + 0.09, "strength": 0.8})
        if manga and phase == "climax" and any(st <= i_["t"] < en and i_["s"] > 0.85 for i_ in impacts):
            t_i = next(i_["t"] for i_ in impacts if st <= i_["t"] < en and i_["s"] > 0.85)
            fxl.append({"type": "invert", "t0": t_i, "t1": t_i + 2.0 / 30})
        if "silhueta" in (rec.get("framing") or []) or preset == "contemplativo":
            fxl.append({"type": "glow", "amount": 0.35 if preset == "contemplativo" else 0.25})
        if phase == "final" and k == len(cuts) - 2:
            sh["camera"] = {"preset": "pull_out" if last_zoom_dir > 0 else "push_in_slow", "intensity": 0.8}
        if fxl:
            sh["fx"] = fxl
        shots.append(sh)

    grade = "manga_tinta" if manga else (subj.get("grade") if subj.get("grade") and preset != "contemplativo"
                                          else P["grade"])
    edit = {
        "tool": "anime-motion-lab", "preset": preset, "format": dict(pj["format"]), "fps": fps or pj["format"]["fps"],
        "duration": round(dur, 3), "grade": grade, "grain": P["grain"], "vignette": P["vignette"],
        "impact_style": P["impact"], "impacts": impacts, "motion_blur": 1.0, "fade_out": 0.6 if not audio else 0.4,
        "shots": shots, "text": text or [],
    }
    if manga:
        edit["impact_style"] = dict(P["impact"], chroma=P["impact"]["chroma"] * 0.5)
    if audio:
        edit.update(audio=audio, audio_start=audio_start, audio_fade_out=0.8)
    if pj["format"]["w"] > pj["format"]["h"] and preset == "cinematico":
        edit["letterbox"] = 2.0
    util.save_json(os.path.join(proj, "edit.json"), edit)
    # relatório
    lines = [f"# Plano do edit — {pj.get('title')}", "", *[f"- {d}" for d in decisions], "",
             "| # | início | dur | fase | energia | asset | técnica | câmera | transição | efeitos |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for s in shots:
        lines.append(f"| {s['id']} | {s['start']:.2f} | {s['dur']:.2f} | {s['phase']} | {s['energy']} | {s['asset']} | "
                     f"{s['technique']}{'/fit' if s.get('fill') == 'fit_blur' else ''} | {s['camera']['preset']} | "
                     f"{(s.get('transition_in') or {}).get('type', 'cut')} | "
                     f"{', '.join(f['type'] for f in s.get('fx', [])) or '—'} |")
    with open(os.path.join(proj, "metadata", "plano.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    for d in decisions:
        project.add_decision(proj, d)
    util.log(f"plano: {len(shots)} planos em {dur:.2f}s · média {dur / max(1, len(shots)):.2f}s/plano · "
             f"{sum(1 for s in shots if s.get('transition_in'))} transições")
    return edit
