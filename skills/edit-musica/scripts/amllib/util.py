"""Utilitários comuns: subprocess, JSON, ffprobe, log."""
import json
import os
import shutil
import subprocess
import sys
import time

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".gif"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


def log(*a):
    print("[aml]", *a, file=sys.stderr, flush=True)


def die(msg, code=1):
    print(f"[aml] ERRO: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def run(cmd, check=True, capture=True, input_bytes=None):
    """Roda um comando; devolve CompletedProcess. Levanta RuntimeError com stderr se falhar."""
    p = subprocess.run(cmd, input=input_bytes, capture_output=capture)
    if check and p.returncode != 0:
        err = (p.stderr or b"").decode("utf-8", "replace")[-2000:]
        raise RuntimeError(f"comando falhou ({p.returncode}): {' '.join(map(str, cmd))[:300]}\n{err}")
    return p


def which(name):
    return shutil.which(name)


def ffprobe(path):
    """Metadados de mídia via ffprobe (dict com format + streams)."""
    p = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    return json.loads(p.stdout.decode("utf-8"))


def media_kind(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    if os.path.isdir(path):
        return "sequence"
    return "unknown"


def video_info(path):
    """{w,h,fps,duration,nframes,has_audio} de um vídeo/GIF."""
    d = ffprobe(path)
    vs = [s for s in d["streams"] if s.get("codec_type") == "video"]
    if not vs:
        raise RuntimeError(f"sem stream de vídeo: {path}")
    v = vs[0]
    num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    if fps <= 0 or fps > 240:
        num, den = (v.get("r_frame_rate") or "30/1").split("/")
        fps = float(num) / float(den) if float(den) else 30.0
    dur = float(v.get("duration") or d["format"].get("duration") or 0)
    nb = int(v.get("nb_frames") or 0) or int(round(dur * fps))
    return {
        "w": int(v["width"]), "h": int(v["height"]), "fps": round(fps, 3), "duration": round(dur, 3),
        "nframes": nb, "codec": v.get("codec_name"),
        "has_audio": any(s.get("codec_type") == "audio" for s in d["streams"]),
    }


def audio_duration(path):
    d = ffprobe(path)
    return float(d["format"].get("duration") or 0)


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def slug(s, maxlen=48):
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:maxlen] or "asset"


def hex_color(c, default=(255, 255, 255)):
    if not c:
        return default
    if isinstance(c, (list, tuple)):
        return tuple(int(x) for x in c[:3])
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
