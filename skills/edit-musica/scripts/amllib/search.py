"""Pesquisa REAL de assets existentes.

Dois caminhos, ambos honestos:
 1. APIs abertas chamadas daqui (dependem da rede do ambiente liberar o host):
    Wikimedia Commons, Openverse (CC/domínio público), Internet Archive, The Met (Open Access), Art Institute of Chicago.
    Host bloqueado → status "blocked" no log; NUNCA se inventa resultado.
 2. Descoberta pelo agente (Claude) com as ferramentas WebSearch/WebFetch — Google Images, Pinterest, Bing, ArtStation,
    Pixiv, DeviantArt, sites oficiais. `queries` gera as buscas; o que for achado entra com `candidate add`
    (só com dados vistos de fato: URL, página, autor e licença quando aparecem na página).
"""
import html
import json
import os
import re
import urllib.parse

from . import project, util

UA = "anime-motion-lab/1.0 (Claude Code skill; asset research for video editing)"
TIMEOUT = 20

SOURCE_HOSTS = {
    "commons": ["commons.wikimedia.org", "upload.wikimedia.org"],
    "openverse": ["api.openverse.org"],
    "archive": ["archive.org"],
    "met": ["collectionapi.metmuseum.org", "images.metmuseum.org"],
    "aic": ["api.artic.edu", "www.artic.edu"],
    "google": ["www.google.com"], "pinterest": ["www.pinterest.com", "i.pinimg.com"],
    "bing": ["www.bing.com"], "artstation": ["www.artstation.com", "cdna.artstation.com"],
    "pixiv": ["www.pixiv.net", "i.pximg.net"], "deviantart": ["www.deviantart.com", "images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com"],
    "youtube": ["www.youtube.com", "i.ytimg.com"],
}
API_SOURCES = ["youtube", "commons", "openverse", "archive", "met", "aic"]


def _session():
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = UA
    return s


def host_reachable(host, timeout=8):
    """True/False + detalhe. Testa conexão HTTPS real (não supõe nada)."""
    import requests
    try:
        r = requests.head(f"https://{host}/", timeout=timeout, allow_redirects=False, headers={"User-Agent": UA})
        return True, f"HTTP {r.status_code}"
    except requests.exceptions.ProxyError as e:
        return False, "bloqueado pela rede do ambiente (proxy 403)" if "403" in str(e) else f"proxy: {str(e)[:120]}"
    except Exception as e:  # noqa
        return False, f"{type(e).__name__}: {str(e)[:120]}"


def net_status(sources=None):
    out = {}
    for src in sources or SOURCE_HOSTS:
        res = {h: host_reachable(h) for h in SOURCE_HOSTS[src]}
        out[src] = {"ok": all(v[0] for v in res.values()), "hosts": {h: v[1] for h, v in res.items()}}
    return out


def _strip(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(s))
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


# ---------------------------------------------------------------- APIs

def search_commons(q, limit=20, s=None):
    s = s or _session()
    r = s.get("https://commons.wikimedia.org/w/api.php", timeout=TIMEOUT, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {q}",
        "gsrnamespace": 6, "gsrlimit": limit, "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 640})
    r.raise_for_status()
    pages = (r.json().get("query") or {}).get("pages") or {}
    out = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata") or {}
        g = lambda k: _strip((em.get(k) or {}).get("value"))  # noqa
        out.append({"source": "commons", "title": p.get("title", "").replace("File:", ""),
                    "image_url": ii.get("url"), "thumb_url": ii.get("thumburl"),
                    "page_url": ii.get("descriptionurl"), "w": ii.get("width"), "h": ii.get("height"),
                    "mime": ii.get("mime"), "author": g("Artist"), "license": g("LicenseShortName") or g("UsageTerms"),
                    "license_url": g("LicenseUrl"), "license_verified": bool(g("LicenseShortName")),
                    "credit": g("Credit"), "date": g("DateTimeOriginal")})
    return out


def search_openverse(q, limit=20, s=None):
    s = s or _session()
    r = s.get("https://api.openverse.org/v1/images/", timeout=TIMEOUT, params={"q": q, "page_size": min(limit, 20)})
    r.raise_for_status()
    out = []
    for it in r.json().get("results", []):
        lic = f"CC {str(it.get('license', '')).upper()} {it.get('license_version') or ''}".strip()
        if str(it.get("license", "")).lower() in ("cc0", "pdm"):
            lic = "Public Domain (" + str(it.get("license")).upper() + ")"
        out.append({"source": "openverse", "title": it.get("title"), "image_url": it.get("url"),
                    "thumb_url": it.get("thumbnail"), "page_url": it.get("foreign_landing_url"),
                    "w": it.get("width"), "h": it.get("height"), "author": it.get("creator"), "license": lic,
                    "license_url": it.get("license_url"), "license_verified": True,
                    "provider": it.get("source") or it.get("provider")})
    return out


def search_archive(q, limit=20, s=None, mediatype="image"):
    s = s or _session()
    params = [("q", f"({q}) AND mediatype:({mediatype})"), ("rows", limit), ("output", "json")]
    for f in ["identifier", "title", "creator", "licenseurl", "mediatype", "rights"]:
        params.append(("fl[]", f))
    r = s.get("https://archive.org/advancedsearch.php", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for d in r.json().get("response", {}).get("docs", []):
        ident = d.get("identifier")
        creator = d.get("creator")
        out.append({"source": "archive", "title": d.get("title"), "identifier": ident,
                    "page_url": f"https://archive.org/details/{ident}", "image_url": None,
                    "author": ", ".join(creator) if isinstance(creator, list) else creator,
                    "license": d.get("licenseurl") or d.get("rights") or "",
                    "license_verified": bool(d.get("licenseurl")), "mediatype": d.get("mediatype"),
                    "note": "arquivos: archive_files(identifier)"})
    return out


def archive_files(identifier, s=None):
    """Lista os arquivos originais de um item do Internet Archive (para escolher o de maior resolução)."""
    s = s or _session()
    r = s.get(f"https://archive.org/metadata/{identifier}", timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for f in r.json().get("files", []):
        if f.get("source") == "original" and os.path.splitext(f.get("name", ""))[1].lower() in (
                util.IMAGE_EXT | util.VIDEO_EXT):
            out.append({"name": f["name"], "url": f"https://archive.org/download/{identifier}/"
                        + urllib.parse.quote(f["name"]), "size": f.get("size"), "w": f.get("width"),
                        "h": f.get("height"), "format": f.get("format")})
    return out


def search_met(q, limit=15, s=None):
    s = s or _session()
    r = s.get("https://collectionapi.metmuseum.org/public/collection/v1/search", timeout=TIMEOUT,
              params={"q": q, "hasImages": "true"})
    r.raise_for_status()
    ids = (r.json().get("objectIDs") or [])[:limit * 2]
    out = []
    for oid in ids:
        o = s.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}", timeout=TIMEOUT)
        if o.status_code != 200:
            continue
        o = o.json()
        if not o.get("primaryImage"):
            continue
        out.append({"source": "met", "title": o.get("title"), "image_url": o.get("primaryImage"),
                    "thumb_url": o.get("primaryImageSmall"), "page_url": o.get("objectURL"),
                    "author": o.get("artistDisplayName"), "date": o.get("objectDate"),
                    "license": "Public Domain (Met Open Access)" if o.get("isPublicDomain") else "© (não é Open Access)",
                    "license_verified": True})
        if len(out) >= limit:
            break
    return out


def search_aic(q, limit=20, s=None):
    s = s or _session()
    r = s.get("https://api.artic.edu/api/v1/artworks/search", timeout=TIMEOUT, params={
        "q": q, "limit": limit, "fields": "id,title,image_id,artist_display,is_public_domain,date_display,thumbnail"})
    r.raise_for_status()
    js = r.json()
    iiif = (js.get("config") or {}).get("iiif_url", "https://www.artic.edu/iiif/2")
    out = []
    for d in js.get("data", []):
        if not d.get("image_id"):
            continue
        th = d.get("thumbnail") or {}
        out.append({"source": "aic", "title": d.get("title"),
                    "image_url": f"{iiif}/{d['image_id']}/full/1686,/0/default.jpg",
                    "page_url": f"https://www.artic.edu/artworks/{d['id']}", "author": d.get("artist_display"),
                    "date": d.get("date_display"), "w": th.get("width"), "h": th.get("height"),
                    "license": "Public Domain (CC0, AIC)" if d.get("is_public_domain") else "© (não é domínio público)",
                    "license_verified": True})
    return out


# ---------------------------------------------------------------- YouTube (descoberta de cenas + quadros publicados)

YT_FRAMES = ["maxresdefault", "maxres1", "maxres2", "maxres3"]  # capa + quadros automáticos (~25/50/75% do vídeo)


def _walk_videos(o, out):
    if isinstance(o, dict):
        v = o.get("videoRenderer")
        if v:
            runs = lambda k: "".join(r.get("text", "") for r in (v.get(k) or {}).get("runs", []))  # noqa
            out.append({"video_id": v.get("videoId"), "title": runs("title"), "channel": runs("ownerText"),
                        "length": (v.get("lengthText") or {}).get("simpleText"),
                        "views": (v.get("viewCountText") or {}).get("simpleText"),
                        "verified": any("VERIFIED" in json.dumps(b) for b in v.get("ownerBadges", []))})
        for x in o.values():
            _walk_videos(x, out)
    elif isinstance(o, list):
        for x in o:
            _walk_videos(x, out)


def search_youtube(q, limit=20, s=None):
    """Busca REAL na página de resultados do YouTube. Cada vídeo vira candidatos de imagem: capa (maxresdefault)
    e quadros automáticos maxres1..3 (1280x720, publicados pelo próprio YouTube em i.ytimg.com).
    O vídeo em si costuma exigir login ("not a bot") para baixar — não é contornado."""
    s = s or _session()
    r = s.get("https://www.youtube.com/results", params={"search_query": q}, timeout=TIMEOUT,
              headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.8"})
    r.raise_for_status()
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", r.text)
    if not m:
        raise RuntimeError("página do YouTube sem ytInitialData (formato mudou ou bloqueio)")
    vids = []
    _walk_videos(json.loads(m.group(1)), vids)
    out = []
    for v in vids[:limit]:
        for fr in YT_FRAMES:
            out.append({"source": "youtube", "title": v["title"], "channel": v["channel"],
                        "video_id": v["video_id"], "frame": fr, "length": v["length"],
                        "image_url": f"https://i.ytimg.com/vi/{v['video_id']}/{fr}.jpg",
                        "page_url": f"https://www.youtube.com/watch?v={v['video_id']}",
                        "author": v["channel"], "w": 1280, "h": 720,
                        "license": "© detentores da obra (quadro de vídeo do YouTube)", "license_verified": False,
                        "channel_verified": v["verified"]})
    return out


SEARCHERS = {"youtube": search_youtube, "commons": search_commons, "openverse": search_openverse, "archive": search_archive,
             "met": search_met, "aic": search_aic}


def run_search(proj, q, sources=None, limit=20):
    """Executa as buscas de API. Resultados → metadata/candidates.json. Bloqueios/erros → search_log."""
    import requests
    sources = sources or API_SOURCES
    s = _session()
    m = project.load_manifest(proj) if proj else None
    cands_path = os.path.join(proj, "metadata", "candidates.json") if proj else None
    cands = util.load_json(cands_path, []) if cands_path else []
    seen = {c.get("image_url") or c.get("page_url") for c in cands}
    report = []
    for src in sources:
        entry = {"t": util.now_iso(), "source": src, "query": q}
        try:
            res = SEARCHERS[src](q, limit=limit, s=s)
            entry.update(status="ok", n=len(res))
            for c in res:
                key = c.get("image_url") or c.get("page_url")
                if key in seen:
                    continue
                seen.add(key)
                c["query"] = q
                c["found"] = util.now_iso()
                c["license_class"] = project.classify_license(c.get("license"))
                cands.append(c)
        except requests.exceptions.ProxyError as e:
            entry.update(status="blocked", n=0, detail="rede do ambiente bloqueou " + ",".join(SOURCE_HOSTS[src]))
        except Exception as e:  # noqa
            entry.update(status="error", n=0, detail=f"{type(e).__name__}: {str(e)[:200]}")
        report.append(entry)
        if m is not None:
            m.setdefault("search_log", []).append(entry)
    if m is not None:
        project.save_manifest(proj, m)
        util.save_json(cands_path, rank(cands, q))
    return report, cands


def rank(cands, q=""):
    toks = [t for t in re.split(r"\W+", (q or "").lower()) if len(t) > 2]
    lic_w = {"public_domain": 1.0, "cc": 0.85, "user": 0.8, "licensed": 0.8, "cc_nc": 0.5, "unknown": 0.35,
             "commercial": 0.3}

    def score(c):
        px = (c.get("w") or 0) * (c.get("h") or 0)
        res = min(1.0, px / (2000 * 2000)) if px else 0.3
        title = (c.get("title") or "").lower()
        rel = (sum(t in title for t in toks) / len(toks)) if toks else 0.5
        lic = lic_w.get(c.get("license_class") or project.classify_license(c.get("license")), 0.35)
        return round(0.4 * res + 0.35 * rel + 0.25 * lic, 3)

    for c in cands:
        c["score"] = score(c)
    return sorted(cands, key=lambda c: -c["score"])


def add_candidate(proj, url, page_url="", source="web", title="", author="", license="", w=None, h=None,
                  kind="image", note=""):
    """Registra um candidato achado com WebSearch/WebFetch (dados só do que foi visto)."""
    path = os.path.join(proj, "metadata", "candidates.json")
    cands = util.load_json(path, [])
    c = {"source": source, "title": title, "image_url": url, "page_url": page_url, "author": author,
         "license": license, "license_verified": False, "license_class": project.classify_license(license),
         "w": w, "h": h, "kind": kind, "note": note, "found": util.now_iso(), "via": "agent-websearch"}
    cands.append(c)
    util.save_json(path, rank(cands, title))
    return c


# ---------------------------------------------------------------- consultas para descoberta (WebSearch)

ANIME_TEMPLATES = [
    "{q} official art", "{q} official art high resolution", "{q} key visual", "{q} transparent PNG",
    "{q} render PNG", "{q} manga panel", "{q} anime scene screenshot", "{q} animation sequence",
    "{q} sakuga", "{q} high resolution wallpaper 4k", "{q} gif", "{q} sprite sheet",
]
JESUS_TEMPLATES = [
    "{q} classical painting public domain", "{q} painting high resolution Wikimedia Commons",
    "{q} icon Wikimedia Commons", "{q} painting museum open access", "{q} engraving public domain",
    "{q} illustration licensed", "{q} cinematic artwork original source",
]
SITE_FILTERS = {
    "google": "", "pinterest": "site:pinterest.com", "bing": "", "artstation": "site:artstation.com",
    "pixiv": "site:pixiv.net", "deviantart": "site:deviantart.com", "commons": "site:commons.wikimedia.org",
    "archive": "site:archive.org", "official": "official site",
}


def build_queries(topic, mode="anime", extra=None):
    """Lista de consultas por fonte. mode: anime | jesus | geral."""
    q = topic.strip()
    tmpl = JESUS_TEMPLATES if mode == "jesus" else ANIME_TEMPLATES
    if mode == "geral":
        tmpl = ["{q} high resolution", "{q} public domain", "{q} transparent PNG", "{q} gif"]
    base = [t.format(q=q) for t in tmpl] + [e for e in (extra or [])]
    out = {"descoberta_web": base[:8]}
    if mode == "jesus":
        out["commons"] = [f"site:commons.wikimedia.org {q} painting", f"{q} oil painting 19th century"]
        out["museus"] = [f"{q} metmuseum open access", f"{q} artic.edu public domain", f"{q} rijksmuseum"]
        out["api_aml"] = [q, f"{q} painting", "Christ " + q if "christ" not in q.lower() else q]
    else:
        for site in ("pinterest", "artstation", "pixiv", "deviantart"):
            out[site] = [f"{SITE_FILTERS[site]} {q} art", f"{SITE_FILTERS[site]} {q}"]
        out["oficial"] = [f"{q} official website character", f"{q} anime official site gallery"]
        out["clipes"] = [f"{q} anime clip", f"{q} fight scene", f"{q} gif"]
        out["api_aml"] = [q]
    return out
