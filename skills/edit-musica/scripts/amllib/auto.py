"""Orquestrador "digite o nome → edit".

Etapas (cada uma grava estado no projeto, dá para retomar de qualquer ponto):
  1. resolve      nome → entidade (metadata/subject.json)
  2. discover     consultas por categoria → buscas REAIS nas fontes acessíveis → metadata/candidates.json
  3. download     melhores candidatos (variedade de vídeos/categorias) → assets/originals + manifesto
  4. review       folha numerada (metadata/revisao.jpg) + filtro automático (mangá P&B, resolução, duplicatas);
                  o agente olha a folha e aprova/reprova (`approve`/`reject`) — evita outro personagem no quadro
  5. prep         recorte/camadas de cada asset aprovado
  6. plan/render/qa (plan.py, render.py, qa.py)
"""
import os

from PIL import Image, ImageDraw, ImageFont

from . import fetch, project, search, subject, util


def subject_path(proj):
    return os.path.join(proj, "metadata", "subject.json")


def resolve(proj, name, contexto="", franquia=None, tipo=None, midia=None):
    ent = subject.resolve(name, contexto, franquia, tipo, midia)
    ent["plano_busca"] = subject.query_plan(ent)
    util.save_json(subject_path(proj), ent)
    project.add_decision(proj, f"sujeito: '{name}' → {ent['nome']} ({ent.get('franquia')}, {ent['tipo']}"
                               f"{', só mangá' if ent.get('midia') == 'manga' else ''}); preset {ent['preset']}")
    return ent


def discover(proj, sources=None, per_query=6, extra_queries=None, only_extra=False):
    ent = util.load_json(subject_path(proj))
    if not ent:
        util.die("rode `auto resolve` antes")
    sources = sources or ["youtube", "commons", "openverse", "met", "aic"]
    if ent["tipo"] != "religioso":
        sources = [s for s in sources if s not in ("met", "aic")]  # museus só fazem sentido para arte clássica
    net = search.net_status(sources)
    live = [s for s in sources if net[s]["ok"]]
    blocked = {s: net[s]["hosts"] for s in sources if not net[s]["ok"]}
    m = project.load_manifest(proj)
    for s, h in blocked.items():
        m.setdefault("search_log", []).append({"t": util.now_iso(), "source": s, "query": "(todas)",
                                               "status": "blocked", "n": 0, "detail": str(h)})
    project.save_manifest(proj, m)
    prev = util.load_json(os.path.join(proj, "metadata", "candidates.json"), []) or []
    cands, seen = list(prev), {c.get("image_url") or c.get("page_url") for c in prev}
    s = search._session()
    plan = list(ent["plano_busca"]) + [{"categoria": "extra", "query": q} for q in (extra_queries or [])]
    if extra_queries and only_extra:
        plan = [{"categoria": "extra", "query": q} for q in extra_queries]
    for item in plan:
        for src in live:
            entry = {"t": util.now_iso(), "source": src, "query": item["query"]}
            try:
                res = search.SEARCHERS[src](item["query"], limit=per_query, s=s)
                entry.update(status="ok", n=len(res))
            except Exception as e:  # noqa
                res = []
                entry.update(status="error", n=0, detail=f"{type(e).__name__}: {str(e)[:160]}")
            m = project.load_manifest(proj)
            m.setdefault("search_log", []).append(entry)
            project.save_manifest(proj, m)
            for c in res:
                key = c.get("image_url") or c.get("page_url")
                if key in seen:
                    continue
                seen.add(key)
                c.update(categoria=item["categoria"], query=item["query"], found=util.now_iso(),
                         license_class=project.classify_license(c.get("license")))
                cands.append(c)
    cands = subject.score_candidates(ent, cands)
    util.save_json(os.path.join(proj, "metadata", "candidates.json"), cands)
    util.log(f"descoberta: {len(cands)} candidatos de {len(live)} fontes ativas ({', '.join(live) or 'nenhuma'}); "
             f"bloqueadas: {', '.join(blocked) or 'nenhuma'}")
    return cands, live, blocked


def download(proj, n=32, per_video=2):
    ent = util.load_json(subject_path(proj))
    cands = util.load_json(os.path.join(proj, "metadata", "candidates.json"), [])
    pick = subject.pick_downloads(ent, cands, n=n, per_video=per_video)
    got = []
    m0 = project.load_manifest(proj)
    have = {r.get("source_url") for r in m0["assets"].values()}
    pick = [c for c in pick if c["image_url"] not in have]
    for c in pick:
        aid_hint = f"{(c.get('video_id') or util.slug(c.get('title', 'img'), 20))}_{c.get('frame', '')}".strip("_")
        aid, entry = fetch.download(proj, c["image_url"], page_url=c.get("page_url", ""), author=c.get("author", ""),
                                    license=c.get("license", ""), license_verified=c.get("license_verified", False),
                                    role=c.get("categoria", ""), source=c.get("source", ""),
                                    asset_id=util.slug(aid_hint, 40), title=c.get("title", ""))
        if aid:
            project.update_asset(proj, aid, relevance=c.get("relevance"), categoria=c.get("categoria"),
                                 query=c.get("query"), channel=c.get("channel"))
            got.append(aid)
        else:
            util.log(f"  não baixou {c['image_url']}: {entry.get('status')} {entry.get('detail', '')}")
    # filtro automático medido na imagem
    m = project.load_manifest(proj)
    for aid in got:
        r = m["assets"][aid]
        r["manga_check"] = subject.manga_check(r)
        if not r.get("relevance") or r.get("relevance") <= 0:
            pass
        reasons = []
        if ent.get("midia") == "manga" and r["manga_check"] == "colorido":
            reasons.append("não parece página de mangá (colorido)")
        if (r.get("sharpness") or 0) < 25:
            reasons.append("muito borrada")
        if (r.get("brightness") or 0.5) < 0.04:
            reasons.append("quase preta")
        r["auto_reject"] = reasons
        r["approved"] = not reasons
    project.save_manifest(proj, m)
    util.log(f"download: {len(got)}/{len(pick)} arquivos; reprovados automaticamente: "
             f"{sum(1 for a in got if m['assets'][a]['auto_reject'])}")
    return got


def review_sheet(proj, aids=None, out=None, cols=6, cell=300):
    """Folha numerada para curadoria visual (o agente abre a imagem e aprova/reprova pelo número)."""
    m = project.load_manifest(proj)
    aids = aids or [a for a, r in m["assets"].items() if r.get("kind") == "image"]
    rows = (len(aids) + cols - 1) // cols
    ch = int(cell * 9 / 16)
    sheet = Image.new("RGB", (cols * cell, rows * (ch + 22)), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:  # noqa
        fnt = ImageFont.load_default()
    index = {}
    for i, a in enumerate(aids):
        r = m["assets"][a]
        im = Image.open(os.path.join(proj, r["file"])).convert("RGB")
        im.thumbnail((cell, ch))
        x, y = (i % cols) * cell, (i // cols) * (ch + 22)
        sheet.paste(im, (x + (cell - im.width) // 2, y))
        flag = "X " if r.get("auto_reject") else ""
        d.text((x + 4, y + ch + 3), f"{flag}#{i} {a[:26]}", fill=(255, 80, 80) if flag else (230, 230, 230), font=fnt)
        index[i] = a
    out = out or os.path.join(proj, "metadata", "revisao.jpg")
    sheet.save(out, quality=85)
    util.save_json(os.path.join(proj, "metadata", "revisao_index.json"), index)
    return out, index


def set_approval(proj, numbers, approved, note=""):
    index = util.load_json(os.path.join(proj, "metadata", "revisao_index.json"), {})
    m = project.load_manifest(proj)
    for n in numbers:
        a = index.get(str(n), n)
        if a in m["assets"]:
            m["assets"][a]["approved"] = approved
            if note:
                m["assets"][a]["review_note"] = note
    project.save_manifest(proj, m)
