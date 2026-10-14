"""Inspeção do ambiente real: sistema, Python, FFmpeg/encoders, GPU, bibliotecas, modelos de recorte e acesso às
fontes de pesquisa. Nada é presumido: cada item é testado."""
import importlib
import os
import platform
import subprocess

from . import util

LIBS = {"numpy": "obrigatória", "PIL": "obrigatória", "scipy": "obrigatória (recorte/partes/saliência)",
        "requests": "obrigatória (pesquisa/download)", "rembg": "opcional (recorte do personagem → parallax 2.5D)",
        "onnxruntime": "opcional (motor do rembg)", "librosa": "opcional (só conferência do BPM)",
        "cv2": "não usada", "moviepy": "não usada"}


def check(network=True):
    rep = {"sistema": f"{platform.system()} {platform.release()} · {platform.machine()}",
           "python": platform.python_version(), "cpus": os.cpu_count()}
    rep["ffmpeg"] = bool(util.which("ffmpeg"))
    rep["ffprobe"] = bool(util.which("ffprobe"))
    if rep["ffmpeg"]:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
        rep["ffmpeg_versao"] = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.split("\n")[0]
        rep["libx264"] = " libx264 " in out
        from .render import gpu_available
        rep["nvenc_compilado"] = "h264_nvenc" in out
        rep["gpu_nvenc_funciona"] = gpu_available() if rep["nvenc_compilado"] else False
    libs = {}
    for k, why in LIBS.items():
        try:
            m = importlib.import_module(k)
            libs[k] = {"ok": True, "versao": getattr(m, "__version__", "?"), "uso": why}
        except Exception:  # noqa
            libs[k] = {"ok": False, "uso": why}
    rep["bibliotecas"] = libs
    from .prep import local_models
    rep["modelos_recorte"] = local_models()
    rep["yt_dlp"] = bool(util.which("yt-dlp"))
    if network:
        from .search import net_status
        rep["fontes"] = net_status()
    return rep


def format_report(rep):
    L = [f"Sistema: {rep['sistema']} · Python {rep['python']} · {rep['cpus']} CPUs",
         f"FFmpeg: {'ok' if rep['ffmpeg'] else 'FALTANDO'} {rep.get('ffmpeg_versao', '')}",
         f"  libx264: {rep.get('libx264')} · NVENC compilado: {rep.get('nvenc_compilado')} · "
         f"GPU funcionando: {rep.get('gpu_nvenc_funciona')} (sem GPU → CPU/libx264)"]
    for k, v in rep["bibliotecas"].items():
        L.append(f"  {'✔' if v['ok'] else '✘'} {k:12s} {v.get('versao', ''):10s} {v['uso']}")
    L.append(f"Modelos de recorte locais: {', '.join(rep['modelos_recorte']) or 'nenhum (rembg baixa no 1º uso se a rede deixar)'}")
    L.append(f"yt-dlp: {rep['yt_dlp']} (download de vídeo do YouTube costuma exigir login → não contornado)")
    if "fontes" in rep:
        L.append("Fontes de pesquisa (teste de conexão real):")
        for s, v in rep["fontes"].items():
            L.append(f"  {'✔' if v['ok'] else '✘'} {s:11s} " + "; ".join(f"{h}: {d}" for h, d in v["hosts"].items()))
    return "\n".join(L)
