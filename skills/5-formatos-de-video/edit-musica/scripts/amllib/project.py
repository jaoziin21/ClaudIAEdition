"""Estrutura do projeto e manifesto de fontes.

projeto/
  assets/originals/   materiais originais (baixados ou do usuário) — NUNCA sobrescritos
  assets/processed/   recortes, máscaras, camadas, partes
  audio/              áudio + analysis.json
  work/               intermediários (segmentos, prévias) — pode apagar
  output/             vídeos finais
  metadata/           manifest.json, candidates.json, FONTES.md, qa_report.*
  edit.json           plano do edit (gerado por `plan`, editável à mão)
  project.json        formato/destino/preset
"""
import hashlib
import os
import shutil

from . import util

DIRS = ["assets/originals", "assets/processed", "audio", "work", "output", "metadata"]

FORMATS = {
    "vertical": {"w": 1080, "h": 1920, "fps": 30, "label": "9:16 TikTok/Reels/Shorts"},
    "horizontal": {"w": 1920, "h": 1080, "fps": 30, "label": "16:9 YouTube/videoclipe"},
    "quadrado": {"w": 1080, "h": 1080, "fps": 30, "label": "1:1"},
    "retrato": {"w": 1080, "h": 1350, "fps": 30, "label": "4:5 feed"},
}
FORMAT_ALIASES = {"9:16": "vertical", "16:9": "horizontal", "1:1": "quadrado", "4:5": "retrato",
                  "tiktok": "vertical", "reels": "vertical", "shorts": "vertical", "youtube": "horizontal",
                  "vertical": "vertical", "horizontal": "horizontal", "square": "quadrado", "quadrado": "quadrado"}


def resolve_format(name):
    key = FORMAT_ALIASES.get(str(name).lower(), str(name).lower())
    if key in FORMATS:
        return dict(FORMATS[key], name=key)
    if "x" in str(name):  # 1280x720
        w, h = str(name).lower().split("x")
        return {"w": int(w), "h": int(h), "fps": 30, "label": "custom", "name": "custom"}
    util.die(f"formato desconhecido: {name} (use vertical|horizontal|quadrado|retrato|LxA)")


def init_project(path, title=None, fmt="vertical", preset="auto", fps=None):
    os.makedirs(path, exist_ok=True)
    for d in DIRS:
        os.makedirs(os.path.join(path, d), exist_ok=True)
    pj = os.path.join(path, "project.json")
    proj = util.load_json(pj, None)
    if proj is None:
        f = resolve_format(fmt)
        if fps:
            f["fps"] = int(fps)
        proj = {"title": title or os.path.basename(os.path.abspath(path)), "format": f, "preset": preset,
                "created": util.now_iso(), "tool": "anime-motion-lab"}
        util.save_json(pj, proj)
    mf = manifest_path(path)
    if not os.path.exists(mf):
        util.save_json(mf, {"project": proj["title"], "created": util.now_iso(), "assets": {}, "decisions": [],
                            "search_log": []})
    gi = os.path.join(path, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w") as f:
            f.write("work/\n*.wav\n")
    return proj


def manifest_path(proj):
    return os.path.join(proj, "metadata", "manifest.json")


def load_manifest(proj):
    m = util.load_json(manifest_path(proj))
    if m is None:
        util.die(f"projeto sem manifesto: {proj} (rode `aml.py init {proj}`)")
    return m


def save_manifest(proj, m):
    util.save_json(manifest_path(proj), m)


def load_project(proj):
    p = util.load_json(os.path.join(proj, "project.json"))
    if p is None:
        util.die(f"não é um projeto anime-motion-lab: {proj}")
    return p


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


LICENSE_CLASSES = {
    "public_domain": ["public domain", "pd", "cc0", "pdm", "no known copyright", "cc-pd"],
    "cc_nc": ["by-nc", "nc-", "noncommercial", "cc-by-nc"],
    "cc": ["cc-by", "cc by", "by-sa", "cc-by-sa", "creative commons", "cc "],
    "user": ["user", "usuário", "usuario", "fornecido"],
    "licensed": ["licensed", "licenciado", "autorizado", "permission", "permissão"],
    "commercial": ["copyright", "©", "all rights reserved", "todos os direitos", "official", "oficial", "studio",
                   "estúdio", "commercial", "comercial", "fan art", "fanart"],
}


def classify_license(lic):
    """Classe de licença a partir do texto (sem inventar: texto vazio → unknown)."""
    if not lic:
        return "unknown"
    s = str(lic).lower()
    for cls in ["public_domain", "cc_nc", "cc", "user", "licensed", "commercial"]:
        if any(k in s for k in LICENSE_CLASSES[cls]):
            return cls
    return "unknown"


RISK = {"public_domain": "ok", "cc": "ok (creditar autor)", "cc_nc": "atenção: não comercial",
        "user": "fornecido pelo usuário (responsabilidade dele)", "licensed": "ok (licença registrada)",
        "commercial": "PROTEGIDO — publicação pode exigir autorização / Content ID", "unknown": "licença NÃO verificada"}


def add_asset(proj, src, *, role="", source_url="", page_url="", author="", license="", license_verified=False,
              origin="user", notes="", asset_id=None, copy=True, extra=None):
    """Registra um asset. O arquivo original é COPIADO para assets/originals (o do usuário fica intacto).
    Mesmo conteúdo (hash) já registrado → reaproveita o registro."""
    m = load_manifest(proj)
    if not os.path.exists(src):
        util.die(f"arquivo não existe: {src}")
    digest = sha256(src) if os.path.isfile(src) else None
    if digest:
        for aid, a in m["assets"].items():
            if a.get("sha256") == digest:
                util.log(f"já registrado como {aid} ({a['file']})")
                return aid
    base = os.path.basename(src.rstrip("/"))
    stem, ext = os.path.splitext(base)
    aid = asset_id or util.slug(stem, 32)
    k = 2
    while aid in m["assets"]:
        aid = f"{util.slug(stem, 28)}-{k}"
        k += 1
    dest_rel = os.path.join("assets", "originals", aid + ext.lower())
    dest = os.path.join(proj, dest_rel)
    if os.path.abspath(src) != os.path.abspath(dest):
        if os.path.exists(dest):
            util.die(f"destino já existe e não será sobrescrito: {dest}")
        if copy:
            if os.path.isdir(src):
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
        else:
            shutil.move(src, dest)
    kind = util.media_kind(dest)
    rec = {"id": aid, "file": dest_rel, "kind": kind, "origin": origin, "original_name": base,
           "source_url": source_url, "page_url": page_url, "author": author, "license": license,
           "license_class": "user" if (origin == "user" and not license) else classify_license(license),
           "license_verified": bool(license_verified), "role": role, "sha256": digest,
           "added": util.now_iso(), "transformations": [], "notes": notes}
    try:
        from . import media
        rec.update(media.describe(dest))
    except Exception as e:  # noqa
        rec["inspect_error"] = str(e)[:300]
    if extra:
        rec.update(extra)
    m["assets"][aid] = rec
    save_manifest(proj, m)
    return aid


def record_transform(proj, aid, desc):
    m = load_manifest(proj)
    if aid in m["assets"]:
        t = m["assets"][aid].setdefault("transformations", [])
        if desc not in t:
            t.append(desc)
        save_manifest(proj, m)


def update_asset(proj, aid, **fields):
    m = load_manifest(proj)
    if aid not in m["assets"]:
        util.die(f"asset não existe: {aid}")
    m["assets"][aid].update({k: v for k, v in fields.items() if v is not None})
    if "license" in fields:
        m["assets"][aid]["license_class"] = classify_license(fields["license"])
    save_manifest(proj, m)


def add_decision(proj, text):
    m = load_manifest(proj)
    m.setdefault("decisions", []).append({"t": util.now_iso(), "text": text})
    save_manifest(proj, m)


def sources_report(proj):
    """Gera metadata/FONTES.md e devolve (texto, avisos)."""
    m = load_manifest(proj)
    edit = util.load_json(os.path.join(proj, "edit.json"), {}) or {}
    used = {s.get("asset") for s in edit.get("shots", [])}
    lines = [f"# Fontes — {m.get('project')}", "",
             "| asset | arquivo | origem | autor | licença | status | resolução/duração | função | usado | transformações |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    warnings = []
    for aid, a in m["assets"].items():
        res = f"{a.get('w', '?')}x{a.get('h', '?')}"
        if a.get("duration"):
            res += f" · {a['duration']}s"
        src = a.get("page_url") or a.get("source_url") or ("(fornecido pelo usuário)" if a.get("origin") == "user" else "")
        cls = a.get("license_class", "unknown")
        risk = RISK.get(cls, cls)
        lic = a.get("license") or "—"
        if a.get("license") and not a.get("license_verified"):
            lic += " (não verificada)"
        lines.append(f"| {aid} | {a['file']} | {src} | {a.get('author') or '—'} | {lic} | {risk} | {res} | "
                     f"{a.get('role') or '—'} | {'sim' if aid in used else 'não'} | "
                     f"{'; '.join(a.get('transformations', [])) or '—'} |")
        if aid in used and cls in ("commercial", "unknown"):
            warnings.append(f"{aid}: {risk}")
        if aid in used and a.get("origin") == "download" and not (a.get("page_url") or a.get("source_url")):
            warnings.append(f"{aid}: baixado sem URL de origem registrada")
    if m.get("decisions"):
        lines += ["", "## Decisões registradas", ""] + [f"- {d['text']}" for d in m["decisions"]]
    if m.get("search_log"):
        lines += ["", "## Pesquisas executadas", ""]
        for s in m["search_log"]:
            lines.append(f"- {s.get('t', '')} · {s.get('source')} · \"{s.get('query')}\" → {s.get('status')}"
                         f" ({s.get('n', 0)} resultados)")
    if warnings:
        lines += ["", "## Avisos de direitos", ""] + [f"- {w}" for w in warnings]
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(proj, "metadata", "FONTES.md"), "w", encoding="utf-8") as f:
        f.write(txt)
    return txt, warnings
