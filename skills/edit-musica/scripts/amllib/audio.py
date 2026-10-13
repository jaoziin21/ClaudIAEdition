"""Análise de áudio para sincronizar o edit (NumPy puro; librosa é usado só como conferência se existir).

Saída (audio/analysis.json):
  duration, tempo (BPM) + alternativas, beats[], downbeats[], onsets[{t,strength}], impacts[{t,strength}],
  energy (curva 10 Hz, 0–1), sections[{start,end,label,energy}], rises[], quiet[]
Nada é inventado: se o BPM for instável, `tempo_confidence` fica baixo e o plano usa os impactos/energia.
"""
import subprocess

import numpy as np

from . import util

SR = 22050
HOP = 512
NFFT = 2048


def load_mono(path, sr=SR, start=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", path]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg não conseguiu ler o áudio: " + p.stderr.decode()[-400:])
    y = np.frombuffer(p.stdout, np.float32).copy()
    if y.size == 0:
        raise RuntimeError("áudio vazio (o arquivo tem trilha de áudio?)")
    return y


def stft_mag(y):
    pad = NFFT // 2
    y = np.pad(y, (pad, pad), mode="reflect")
    n = 1 + (len(y) - NFFT) // HOP
    idx = np.arange(NFFT)[None, :] + HOP * np.arange(n)[:, None]
    win = np.hanning(NFFT).astype(np.float32)
    frames = y[idx] * win
    return np.abs(np.fft.rfft(frames, axis=1)).astype(np.float32)  # (n, NFFT/2+1)


def _smooth(x, w):
    if w <= 1:
        return x
    k = np.hanning(w + 2)[1:-1]
    k /= k.sum()
    return np.convolve(x, k, mode="same")


def onset_envelopes(S):
    freqs = np.fft.rfftfreq(NFFT, 1.0 / SR)
    L = np.log1p(100.0 * S)
    d = np.maximum(0.0, np.diff(L, axis=0, prepend=L[:1]))
    broad = d[:, (freqs > 30) & (freqs < 8000)].mean(axis=1)
    low = d[:, (freqs > 30) & (freqs < 160)].mean(axis=1)
    high = d[:, (freqs > 2000) & (freqs < 10000)].mean(axis=1)

    def norm(x):
        x = x - _smooth(x, 31) * 0.5
        x = np.maximum(x, 0)
        p = np.percentile(x, 99.5) or 1.0
        return np.clip(x / p, 0, 1.5)
    return norm(broad), norm(low), norm(high)


def estimate_tempo(env, fps, lo=60, hi=200, prior=110.0):
    x = env - env.mean()
    n = len(x)
    if n < fps * 4:
        return None, 0.0, []
    f = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(f * np.conj(f))[:n]
    ac /= ac[0] + 1e-9
    lags = np.arange(int(fps * 60 / hi), int(fps * 60 / lo) + 1)
    bpms = 60.0 * fps / lags
    vals = ac[lags]
    # reforça com harmônicos (lag 2x) e prior log-normal
    vals2 = vals + 0.5 * np.interp(lags * 2, np.arange(n), ac)
    w = np.exp(-0.5 * (np.log2(bpms / prior) / 0.9) ** 2)
    score = vals2 * w
    order = np.argsort(-score)
    best = order[0]
    # refina com interpolação parabólica
    i = lags[best]
    if 1 <= i < n - 1:
        a, b, c = ac[i - 1], ac[i], ac[i + 1]
        off = 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
        i = i + float(np.clip(off, -0.5, 0.5))
    bpm = 60.0 * fps / i
    conf = float(np.clip((score[best] - np.median(score)) / (np.abs(score).max() + 1e-9), 0, 1))
    alts = []
    for j in order[1:40]:
        b2 = float(bpms[j])
        if all(abs(b2 - a) / a > 0.06 for a in [bpm] + alts):
            alts.append(round(b2, 1))
        if len(alts) == 3:
            break
    return float(bpm), conf, alts


def track_beats(env, fps, bpm, tightness=120.0):
    """Beat tracking por programação dinâmica (Ellis 2007)."""
    period = fps * 60.0 / bpm
    n = len(env)
    localscore = np.convolve(env, np.exp(-0.5 * ((np.arange(-period, period + 1) * 32.0 / period) ** 2)), "same")
    backlink = -np.ones(n, dtype=int)
    cumscore = localscore.copy()
    prange = np.arange(-int(round(2 * period)), -int(round(period / 2)) + 1)
    txwt = -tightness * np.log(-prange / period) ** 2
    for i in range(n):
        lo = i + prange
        valid = lo >= 0
        if not valid.any():
            continue
        cand = cumscore[lo[valid]] + txwt[valid]
        k = int(np.argmax(cand))
        cumscore[i] = localscore[i] + cand[k]
        backlink[i] = lo[valid][k]
    # último beat: máximo local perto do fim
    tail = cumscore[max(0, n - int(2 * period)):]
    med = np.median(cumscore[cumscore > 0]) if (cumscore > 0).any() else 0
    cands = np.where(tail > 0.5 * med)[0]
    b = (max(0, n - int(2 * period)) + (cands[-1] if len(cands) else int(np.argmax(tail))))
    beats = []
    while b >= 0:
        beats.append(b)
        b = backlink[b]
    beats = np.array(beats[::-1], dtype=float)
    # tira beats no silêncio do começo/fim
    if len(beats) > 4:
        strong = localscore[beats.astype(int)]
        thr = 0.15 * np.median(strong)
        keep = np.where(strong > thr)[0]
        if len(keep):
            beats = beats[keep[0]:keep[-1] + 1]
    return beats / fps


def refine_beats(beats, env, fps, radius=0.05):
    """Puxa cada batida para o pico de onset mais próximo (±50 ms), com interpolação parabólica."""
    out = []
    r = max(1, int(radius * fps))
    for b in beats:
        i = int(round(b * fps))
        a, z = max(1, i - r), min(len(env) - 1, i + r + 1)
        if z <= a:
            out.append(b)
            continue
        j = a + int(np.argmax(env[a:z]))
        if env[j] <= 0:
            out.append(b)
            continue
        if 1 <= j < len(env) - 1:
            y0, y1, y2 = env[j - 1], env[j], env[j + 1]
            off = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
            j = j + float(np.clip(off, -0.5, 0.5))
        out.append(j / fps)
    return np.array(out)


def pick_peaks(env, fps, min_gap=0.12, k=1.5, wait_win=0.6):
    """Picos acima de limiar adaptativo (mediana local + k*MAD)."""
    n = len(env)
    w = max(3, int(wait_win * fps))
    out = []
    last = -1e9
    for i in range(1, n - 1):
        if env[i] < env[i - 1] or env[i] < env[i + 1]:
            continue
        a, b = max(0, i - w), min(n, i + w)
        seg = env[a:b]
        med = np.median(seg)
        mad = np.median(np.abs(seg - med)) + 1e-6
        if env[i] > med + k * mad and env[i] > 0.12 and env[i] == seg.max():
            t = i / fps
            if t - last >= min_gap:
                out.append((t, float(env[i])))
                last = t
    return out


def energy_curve(y, rate=10):
    hop = SR // rate
    n = len(y) // hop
    if n == 0:
        return np.zeros(1)
    r = np.sqrt((y[:n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(r + 1e-9)
    lo, hi = np.percentile(db, 5), np.percentile(db, 98)
    e = np.clip((db - lo) / max(hi - lo, 1e-6), 0, 1)
    return _smooth(e, rate)  # ~1 s


def sections_from_energy(e, rate, beats, duration, min_len=3.0):
    """Segmenta em seções por níveis de energia; rotula intro/verso/build/refrão/clímax/pausa/final."""
    if len(e) < rate * 2:
        return [{"start": 0.0, "end": round(duration, 3), "label": "unico", "energy": float(e.mean())}]
    es = _smooth(e, rate * 2)
    q = np.percentile(es, [33, 66])
    lvl = np.digitize(es, q)  # 0,1,2
    segs = []
    s = 0
    for i in range(1, len(lvl) + 1):
        if i == len(lvl) or lvl[i] != lvl[s]:
            segs.append([s / rate, i / rate, int(lvl[s])])
            s = i
    # funde segmentos curtos no vizinho
    changed = True
    while changed and len(segs) > 1:
        changed = False
        for j, sg in enumerate(segs):
            if sg[1] - sg[0] < min_len:
                k = j - 1 if j > 0 and (j == len(segs) - 1 or segs[j - 1][1] - segs[j - 1][0] >=
                                        segs[j + 1][1] - segs[j + 1][0]) else j + 1
                k = max(0, min(len(segs) - 1, k))
                if k == j:
                    continue
                a, b = sorted([j, k])
                segs[a] = [segs[a][0], segs[b][1], segs[k][2]]
                del segs[b]
                changed = True
                break
    # encaixa as fronteiras no beat mais próximo
    bt = np.asarray(beats) if len(beats) else None
    out = []
    for sg in segs:
        st, en = sg[0], min(sg[1], duration)
        if bt is not None and st > 0:
            st = float(bt[np.argmin(np.abs(bt - st))]) if np.min(np.abs(bt - st)) < 0.6 else st
        i0, i1 = int(sg[0] * rate), max(int(sg[0] * rate) + 1, int(sg[1] * rate))
        out.append({"start": round(st, 3), "end": round(en, 3), "level": sg[2], "energy": round(float(e[i0:i1].mean()), 3)})
    for a, b in zip(out, out[1:]):
        a["end"] = b["start"]
    out[0]["start"] = 0.0
    out[-1]["end"] = round(duration, 3)
    # rótulos
    peak = max(range(len(out)), key=lambda i: out[i]["energy"])
    for i, sg in enumerate(out):
        if i == peak and sg["level"] == 2:
            lab = "climax"
        elif sg["level"] == 2:
            lab = "refrao"
        elif sg["level"] == 1:
            lab = "build" if (i + 1 < len(out) and out[i + 1]["level"] == 2) else "verso"
        else:
            lab = "intro" if i == 0 else ("final" if i == len(out) - 1 else "pausa")
        sg["label"] = lab
    return out


def analyze(path, start=0.0, dur=None):
    y = load_mono(path, start=start, dur=dur)
    duration = len(y) / SR
    S = stft_mag(y)
    fps = SR / HOP
    broad, low, high = onset_envelopes(S)
    env = 0.6 * broad + 0.4 * low
    bpm, conf, alts = estimate_tempo(env, fps)
    beats = track_beats(env, fps, bpm) if bpm else np.array([])
    if len(beats) > 2:
        beats = refine_beats(beats, env, fps)
        bpm = 60.0 / float(np.polyfit(np.arange(len(beats)), beats, 1)[0])  # inclinação = período médio
    # downbeats: fase de 4 com mais grave
    downbeats = []
    if len(beats) >= 8:
        lowv = np.array([low[min(len(low) - 1, int(b * fps))] for b in beats])
        phase = int(np.argmax([lowv[p::4].mean() for p in range(4)]))
        downbeats = beats[phase::4]
    # regularidade dos beats → confiança
    if len(beats) > 4:
        ibi = np.diff(beats)
        reg = float(1.0 - min(1.0, ibi.std() / (ibi.mean() + 1e-9) * 4))
        conf = round(0.5 * conf + 0.5 * reg, 3)
    onsets = pick_peaks(env, fps, min_gap=0.08, k=1.5, wait_win=0.3)
    # impactos: subida de energia no grave (bumbo/porrada/boom) + fluxo grave + banda larga, espaçados
    freqs = np.fft.rfftfreq(NFFT, 1.0 / SR)
    lowE = np.log1p(100.0 * S[:, (freqs > 30) & (freqs < 130)].sum(axis=1))
    dl = np.maximum(0.0, np.convolve(np.diff(lowE, prepend=lowE[:1]), np.ones(3) / 3, "same"))
    dl /= (np.percentile(dl, 99.5) or 1.0)
    imp_env = np.pad(0.5 * dl + 0.3 * low + 0.2 * broad, (1, 0))
    impacts = [(t - 1.0 / fps, s) for t, s in pick_peaks(imp_env, fps, min_gap=0.25, k=2.5, wait_win=0.5)]
    if impacts:
        mx = max(s for _, s in impacts)
        impacts = [(max(0.0, t), s / mx) for t, s in impacts if s / mx >= 0.25]
    e = energy_curve(y)
    secs = sections_from_energy(e, 10, beats, duration)
    de = np.diff(_smooth(e, 10)) * 10
    rises = [round(i / 10, 2) for i in range(1, len(de) - 1)
             if de[i] > 0.6 and de[i] >= de[i - 1] and de[i] >= de[i + 1]]
    quiet = []
    qmask = e < 0.12
    i = 0
    while i < len(qmask):
        if qmask[i]:
            j = i
            while j < len(qmask) and qmask[j]:
                j += 1
            if (j - i) / 10 >= 0.4:
                quiet.append([round(i / 10, 2), round(j / 10, 2)])
            i = j
        else:
            i += 1
    res = {
        "file": path, "start": start, "duration": round(duration, 3),
        "tempo": round(bpm, 2) if bpm else None, "tempo_confidence": round(conf, 3), "tempo_alternatives": alts,
        "beats": [round(float(b), 3) for b in beats], "downbeats": [round(float(b), 3) for b in downbeats],
        "onsets": [{"t": round(t, 3), "strength": round(s, 3)} for t, s in onsets],
        "impacts": [{"t": round(t, 3), "strength": round(s, 3)} for t, s in impacts],
        "energy_rate": 10, "energy": [round(float(v), 3) for v in e],
        "sections": secs, "rises": rises, "quiet": quiet, "engine": "numpy",
    }
    try:  # conferência opcional
        import librosa  # noqa
        t2, _ = librosa.beat.beat_track(y=y, sr=SR)
        res["librosa_tempo"] = round(float(np.atleast_1d(t2)[0]), 2)
    except Exception:  # noqa
        pass
    return res


def summary(a):
    secs = ", ".join(f"{s['label']} {s['start']:.1f}–{s['end']:.1f}s" for s in a["sections"])
    return (f"duração {a['duration']:.2f}s · BPM {a['tempo']} (confiança {a['tempo_confidence']}, alternativas "
            f"{a['tempo_alternatives']}) · {len(a['beats'])} batidas · {len(a['impacts'])} impactos · seções: {secs}")


def prepare_audio(src, dest, start=0.0, dur=None, loudnorm=False):
    """Extrai/normaliza a trilha (MP3/WAV/MP4…) para WAV 48 kHz estéreo. O arquivo original não é alterado."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-nostdin"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", src]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-vn", "-ac", "2", "-ar", "48000"]
    if loudnorm:
        cmd += ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    cmd += [dest]
    util.run(cmd)
    return dest
