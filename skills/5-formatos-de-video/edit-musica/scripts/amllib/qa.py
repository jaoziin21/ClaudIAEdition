"""Validação do vídeo final: integridade, formato, duração, sincronia A/V, quadros pretos inesperados, saltos de
movimento fora dos cortes, erros de decodificação, loudness, folha de quadros e checagem das fontes."""
import os
import re
import subprocess

import numpy as np

from . import project, util


def _ff(args):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin"] + args, capture_output=True, text=True)
    return p.returncode, p.stderr


def black_segments(path, min_d=0.12, pix_th=0.06):
    _, err = _ff(["-i", path, "-vf", f"blackdetect=d={min_d}:pix_th={pix_th}", "-an", "-f", "null", "-"])
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", err)]


def motion_series(path, fps, w=96):
    p = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vf", f"scale={w}:-2,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    info = util.video_info(path)
    h = int(round(info["h"] * w / info["w"] / 2) * 2)
    buf = np.frombuffer(p.stdout, np.uint8)
    n = len(buf) // (w * h)
    fr = buf[:n * w * h].reshape(n, h, w).astype(np.float32)
    return np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2)) if n > 1 else np.zeros(0)


def validate(proj, video=None, sheet=True, expect_scale=1.0):
    edit = util.load_json(os.path.join(proj, "edit.json"), {}) or {}
    video = video or os.path.join(proj, "output", "final.mp4")
    rep = {"video": video, "checks": [], "warnings": [], "errors": []}

    def check(name, ok, detail=""):
        rep["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            rep["errors"].append(f"{name}: {detail}")

    if not os.path.exists(video) or os.path.getsize(video) < 1000:
        check("arquivo existe", False, video)
        return rep
    check("arquivo existe", True, f"{os.path.getsize(video) / 1e6:.1f} MB")
    d = util.ffprobe(video)
    vs = [s for s in d["streams"] if s["codec_type"] == "video"]
    aus = [s for s in d["streams"] if s["codec_type"] == "audio"]
    v = vs[0] if vs else {}
    check("vídeo H.264 yuv420p", v.get("codec_name") == "h264" and v.get("pix_fmt") == "yuv420p",
          f"{v.get('codec_name')} {v.get('pix_fmt')}")
    fmt = edit.get("format") or project.load_project(proj)["format"]
    ew, eh = (int(round(fmt["w"] * expect_scale / 2) * 2), int(round(fmt["h"] * expect_scale / 2) * 2))
    check("resolução", (v.get("width"), v.get("height")) == (ew, eh),
          f"{v.get('width')}x{v.get('height')} (esperado {ew}x{eh}{' — prévia' if expect_scale != 1 else ''})")
    fps = edit.get("fps", fmt.get("fps", 30))
    vdur = float(v.get("duration") or d["format"]["duration"])
    exp = edit.get("duration") or sum(s["dur"] for s in edit.get("shots", []))
    check("duração", abs(vdur - exp) <= 1.5 / fps, f"{vdur:.3f}s (plano {exp:.3f}s)")
    if edit.get("audio"):
        check("tem áudio", bool(aus), f"{len(aus)} trilha(s)")
        if aus:
            adur = float(aus[0].get("duration") or 0)
            check("sincronia A/V (duração)", abs(adur - vdur) < 0.1, f"áudio {adur:.3f}s × vídeo {vdur:.3f}s")
            _, err = _ff(["-i", video, "-vn", "-af", "ebur128", "-f", "null", "-"])
            m = re.findall(r"I:\s+(-?[0-9.]+) LUFS", err)
            if m:
                rep["loudness_lufs"] = float(m[-1])
    else:
        rep["checks"].append({"check": "áudio", "ok": True, "detail": "sem música (vídeo mudo por decisão: nenhum "
                                                                       "áudio foi inventado)"})
    code, err = _ff(["-v", "error", "-i", video, "-f", "null", "-"])
    check("decodifica sem erro", code == 0 and not err.strip(), err.strip()[:300])
    # pretos esperados: dip/fades
    expected = []
    for s in edit.get("shots", []):
        tr = s.get("transition_in") or {}
        if tr.get("type") == "dip":
            expected.append((s["start"] - tr.get("dur", 0.5) / 2 - 0.1, s["start"] + tr.get("dur", 0.5) / 2 + 0.1))
    if edit.get("fade_out"):
        expected.append((exp - edit["fade_out"] - 0.1, exp + 0.1))
    if edit.get("fade_in"):
        expected.append((-0.1, edit["fade_in"] + 0.1))
    blacks = black_segments(video)
    bad = [b for b in blacks if not any(e0 <= b[0] and b[1] <= e1 for e0, e1 in expected)]
    check("sem quadro preto inesperado", not bad, f"{bad}" if bad else f"{len(blacks)} trecho(s) previsto(s)")
    # saltos de movimento fora de cortes/efeitos previstos
    mot = motion_series(video, fps)
    if len(mot) > 5:
        cuts = {int(round(s["start"] * fps)) for s in edit.get("shots", [])}
        hot = set()
        for s in edit.get("shots", []):
            tr = s.get("transition_in") or {}
            if tr.get("type", "cut") != "cut":
                a = int(round(s["start"] * fps))
                hot |= set(range(a - int(tr.get("dur", .2) * fps) - 1, a + int(tr.get("dur", .2) * fps) + 2))
            for f_ in s.get("fx", []):
                if "t0" in f_:
                    hot |= set(range(int(f_["t0"] * fps) - 1, int(f_.get("t1", f_["t0"]) * fps) + 2))
        for i_ in edit.get("impacts", []):
            hot |= set(range(int(i_["t"] * fps) - 2, int(i_["t"] * fps) + 4))
        for s in edit.get("shots", []):  # troca de enquadramento planejada (reframe) é um 'salto' de propósito
            if (s.get("camera") or {}).get("preset") == "reframe":
                a = s["start"] + s["dur"] * 0.45
                hot |= set(range(int(a * fps), int((s["start"] + s["dur"] * 0.62) * fps) + 2))
        med = float(np.median(mot)) + 1e-6
        # salto = descontinuidade isolada (pico muito maior que os vizinhos), não aceleração planejada
        spikes = []
        for i in range(2, len(mot) - 2):
            neigh = max(mot[i - 2], mot[i + 2])
            if mot[i] > max(12.0, med * 4, neigh * 2.5) and not any(abs(i + 1 - c) <= 1 for c in cuts) \
                    and (i + 1) not in hot:
                spikes.append(i + 1)
            # arranque brusco: imagem parada e, no quadro seguinte, movimento forte (câmera travada que dispara)
            elif mot[i - 1] < max(1.5, med * 0.4) and mot[i - 2] < max(1.5, med * 0.4) and \
                    mot[i] > max(8.0, med * 2.5) and not any(abs(i + 1 - c) <= 1 for c in cuts) and (i + 1) not in hot:
                spikes.append(i + 1)
        rep["motion_median"] = round(med, 2)
        ok = not spikes
        check("movimento suave (sem saltos fora dos cortes)", ok,
              f"{len(spikes)} salto(s): {[round(s_ / fps, 2) for s_ in spikes[:8]]}")
        # planos parados demais (parece slide)
        still = []
        for s in edit.get("shots", []):
            a, b = int(s["start"] * fps), int((s["start"] + s["dur"]) * fps) - 1
            seg = mot[a:b]
            if len(seg) > 6 and float(np.median(seg)) < 0.08:
                still.append(s["id"])
        if still:
            rep["warnings"].append(f"planos quase parados (cara de slide): {still}")
    # fontes
    _, warns = project.sources_report(proj)
    rep["warnings"] += [f"direitos: {w}" for w in warns]
    # folha de quadros (1 por plano)
    if sheet and edit.get("shots"):
        tdir = os.path.join(proj, "work", "qa_frames")
        os.makedirs(tdir, exist_ok=True)
        paths = []
        for s in edit["shots"]:
            t = s["start"] + s["dur"] / 2
            p = os.path.join(tdir, f"{s['id']}.jpg")
            util.run(["ffmpeg", "-v", "error", "-y", "-nostdin", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
                      "-vf", "scale=360:-2", p])
            paths.append(p)
        from .render import contact_sheet
        rep["sheet"] = contact_sheet(paths, os.path.join(proj, "output", "folha_qa.jpg"), cols=min(9, len(paths)),
                                     width=1800)
    rep["ok"] = not rep["errors"]
    util.save_json(os.path.join(proj, "metadata", "qa_report.json"), rep)
    lines = [f"# QA — {os.path.basename(video)}", "", f"**Resultado: {'APROVADO' if rep['ok'] else 'REPROVADO'}**", ""]
    lines += [f"- {'✔' if c['ok'] else '✘'} {c['check']} — {c['detail']}" for c in rep["checks"]]
    if rep["warnings"]:
        lines += ["", "## Avisos"] + [f"- {w}" for w in rep["warnings"]]
    with open(os.path.join(proj, "metadata", "qa.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return rep
