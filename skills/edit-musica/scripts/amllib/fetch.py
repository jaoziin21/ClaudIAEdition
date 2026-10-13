"""Download legítimo de assets + registro no manifesto.
Não burla login/paywall/DRM: se a resposta for página HTML (login, bloqueio) ou erro, registra a limitação e para."""
import mimetypes
import os
import urllib.parse

from . import project, search, util

MAX_BYTES = 400 * 1024 * 1024


def _ext_from(url, ctype):
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    if ext in util.IMAGE_EXT | util.VIDEO_EXT:
        return ext
    guess = mimetypes.guess_extension((ctype or "").split(";")[0].strip()) or ""
    return {".jpe": ".jpg"}.get(guess, guess) or ".bin"


def _log(proj, entry):
    m = project.load_manifest(proj)
    m.setdefault("fetch_log", []).append(entry)
    project.save_manifest(proj, m)


def download(proj, url, *, page_url="", author="", license="", license_verified=False, role="", source="",
             asset_id=None, title=""):
    import requests
    entry = {"t": util.now_iso(), "url": url, "page_url": page_url}
    tmpdir = os.path.join(proj, "work", "downloads")
    os.makedirs(tmpdir, exist_ok=True)
    try:
        with requests.get(url, stream=True, timeout=40, headers={"User-Agent": search.UA,
                                                                  "Referer": page_url or url}) as r:
            entry["http"] = r.status_code
            if r.status_code in (401, 403):
                raise RuntimeError(f"acesso negado pelo site (HTTP {r.status_code}) — não será contornado")
            r.raise_for_status()
            ctype = r.headers.get("Content-Type", "")
            if "text/html" in ctype or "application/json" in ctype:
                raise RuntimeError(f"a URL devolveu {ctype.split(';')[0]} (página, login ou bloqueio), não um arquivo"
                                   " de mídia — abrir a página original e achar o link do arquivo")
            ext = _ext_from(url, ctype)
            name = (asset_id or util.slug(title or os.path.basename(urllib.parse.urlparse(url).path) or "asset", 40))
            tmp = os.path.join(tmpdir, name + ext)
            n = 0
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    n += len(chunk)
                    if n > MAX_BYTES:
                        raise RuntimeError("arquivo maior que 400 MB")
                    f.write(chunk)
    except requests.exceptions.ProxyError:
        host = urllib.parse.urlparse(url).hostname
        entry.update(status="blocked", detail=f"rede do ambiente bloqueou {host}")
        _log(proj, entry)
        return None, entry
    except Exception as e:  # noqa
        entry.update(status="error", detail=str(e)[:300])
        _log(proj, entry)
        return None, entry
    # valida que é mídia de verdade
    try:
        kind = util.media_kind(tmp)
        if kind == "image":
            from PIL import Image
            Image.open(tmp).verify()
        elif kind == "video":
            util.video_info(tmp)
        else:
            raise RuntimeError(f"tipo não suportado ({ext})")
    except Exception as e:  # noqa
        os.remove(tmp)
        entry.update(status="invalid", detail=f"arquivo baixado não é mídia válida: {str(e)[:200]}")
        _log(proj, entry)
        return None, entry
    aid = project.add_asset(proj, tmp, role=role, source_url=url, page_url=page_url, author=author, license=license,
                            license_verified=license_verified, origin="download", asset_id=asset_id,
                            copy=False, extra={"search_source": source, "title": title})
    entry.update(status="ok", asset=aid, bytes=n)
    _log(proj, entry)
    return aid, entry


def download_candidate(proj, index, role="", asset_id=None):
    cands = util.load_json(os.path.join(proj, "metadata", "candidates.json"), [])
    if not (0 <= index < len(cands)):
        util.die(f"candidato {index} não existe ({len(cands)} na lista)")
    c = cands[index]
    url = c.get("image_url")
    if not url and c.get("source") == "archive" and c.get("identifier"):
        files = search.archive_files(c["identifier"])
        if not files:
            util.die("item do Internet Archive sem arquivo de imagem/vídeo original")
        files.sort(key=lambda f: -int(f.get("size") or 0))
        url = files[0]["url"]
    if not url:
        util.die("candidato sem URL de arquivo — abrir page_url e achar o arquivo original")
    return download(proj, url, page_url=c.get("page_url", ""), author=c.get("author", ""),
                    license=c.get("license", ""), license_verified=c.get("license_verified", False), role=role,
                    source=c.get("source", ""), asset_id=asset_id, title=c.get("title", ""))
