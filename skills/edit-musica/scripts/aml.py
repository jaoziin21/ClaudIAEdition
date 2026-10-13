#!/usr/bin/env python3
"""Anime Motion Lab — CLI.  python3 aml.py <comando> ...   (python3 aml.py -h para a lista)

Fluxo "digite o nome":  auto → (curadoria: revisar/aprovar/reprovar) → montar
Fluxo manual:           init → add/buscar/baixar → prep → audio → plano → previa → render → qa → fontes
Atalho:                 animar <imagem>  (anima UMA imagem existente e renderiza)
"""
import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amllib import util  # noqa: E402


def _floats(s):
    return [float(x) for x in str(s).replace(";", ",").split(",") if x.strip()]


# ------------------------------------------------------------------ comandos

def cmd_env(a):
    from amllib import envcheck
    rep = envcheck.check(network=not a.sem_rede)
    print(envcheck.format_report(rep))
    if a.json:
        util.save_json(a.json, rep)


def cmd_init(a):
    from amllib import project
    p = project.init_project(a.proj, a.titulo, a.formato, a.preset, a.fps)
    print(json.dumps(p, ensure_ascii=False, indent=2))


def cmd_add(a):
    from amllib import project
    for f in a.arquivos:
        aid = project.add_asset(a.proj, f, role=a.funcao, source_url=a.fonte, page_url=a.pagina, author=a.autor,
                                license=a.licenca, license_verified=a.licenca_verificada,
                                origin="download" if a.fonte else "user")
        print(aid)


def cmd_consultas(a):
    from amllib import subject
    ent = subject.resolve(a.nome, a.contexto or "", a.franquia, a.tipo, a.midia)
    print(json.dumps({"entidade": {k: ent[k] for k in ("nome", "franquia", "tipo", "preset", "confirmar")},
                      "consultas": subject.query_plan(ent)}, ensure_ascii=False, indent=2))


def cmd_buscar(a):
    from amllib import search
    rep, cands = search.run_search(a.proj, a.consulta, a.fontes.split(",") if a.fontes else None, a.limite)
    for r in rep:
        print(f"{r['source']:10s} {r['status']:8s} {r.get('n', 0):3d}  {r.get('detail', '')}")
    print(f"{len(cands)} candidatos em metadata/candidates.json")


def cmd_candidato(a):
    from amllib import search
    c = search.add_candidate(a.proj, a.url, a.pagina, a.fonte, a.titulo, a.autor, a.licenca, a.w, a.h)
    print(json.dumps(c, ensure_ascii=False, indent=2))


def cmd_baixar(a):
    from amllib import fetch
    if a.candidato is not None:
        aid, e = fetch.download_candidate(a.proj, a.candidato, role=a.funcao)
    else:
        aid, e = fetch.download(a.proj, a.url, page_url=a.pagina, author=a.autor, license=a.licenca, role=a.funcao)
    print(aid or "NÃO BAIXOU", json.dumps(e, ensure_ascii=False))
    if not aid:
        sys.exit(2)


def cmd_auto(a):
    from amllib import auto, project, subject
    project.init_project(a.proj, a.titulo or f"{a.nome} — edit", a.formato, a.preset or "auto")
    ent = auto.resolve(a.proj, a.nome, a.contexto or "", a.franquia, a.tipo, a.midia)
    print(f"sujeito: {ent['nome']} · {ent.get('franquia')} · {ent['tipo']} · preset {ent['preset']}"
          f"{' · SÓ MANGÁ' if ent.get('midia') == 'manga' else ''}"
          f"{'  (NÃO está na tabela: confirme quem é com WebSearch)' if ent['confirmar'] else ''}")
    if a.audio:
        _audio(a.proj, a.audio, a.inicio, a.dur)
    if a.referencia:
        _ref(a.proj, a.referencia)
    cands, live, blocked = auto.discover(a.proj, a.fontes.split(",") if a.fontes else None, a.por_busca,
                                         a.extra.split("|") if a.extra else None)
    print(f"fontes ativas: {live or 'nenhuma'} · bloqueadas pela rede: {list(blocked) or 'nenhuma'}")
    got = auto.download(a.proj, a.baixar, a.por_video)
    m = project.load_manifest(a.proj)
    ok = [g for g in got if m["assets"][g].get("approved")]
    sheet, idx = auto.review_sheet(a.proj, ok or got)
    print(f"baixados {len(got)} · passaram no filtro automático {len(ok)}")
    print(f"FOLHA DE REVISÃO: {sheet}  → abra, confira se é o sujeito certo e use `reprovar`/`aprovar` pelos números;"
          f" depois `montar`.")
    if a.sem_revisao:
        cmd_montar(argparse.Namespace(proj=a.proj, preset=a.preset, dur=a.dur, max_assets=a.max_assets, seed=7,
                                      bpm=None, gpu=False, previa=False, saida=None))


def cmd_revisar(a):
    from amllib import auto, project
    m = project.load_manifest(a.proj)
    aids = [k for k, r in m["assets"].items() if r.get("kind") == "image" and (a.todos or r.get("approved", True))]
    out, idx = auto.review_sheet(a.proj, aids)
    print(out)
    for i, k in idx.items():
        r = m["assets"][k]
        print(f"#{i:<3} {k:40s} {','.join(r.get('framing') or [])} {r.get('manga_check') or ''} {r.get('categoria') or ''}")


def cmd_aprovar(a, ok=True):
    from amllib import auto
    auto.set_approval(a.proj, [int(x) if str(x).isdigit() else x for x in a.itens], ok, a.nota or "")
    print("ok")


def cmd_prep(a):
    from amllib import prep, project
    m = project.load_manifest(a.proj)
    ids = a.ids or [k for k, r in m["assets"].items() if r.get("kind") == "image" and r.get("approved", True)]
    for k in ids:
        if m["assets"][k].get("kind") != "image":
            continue
        i = prep.prep_image(a.proj, k, model=a.modelo, force=a.forcar, no_segment=a.sem_recorte, mask_path=a.mascara)
        print(f"{k:40s} {i['technique']:9s} {i.get('method') or '-':22s} cobertura={i.get('subject_coverage')} "
              f"parallax_max={i.get('parallax_max')}")


def cmd_parte(a):
    from amllib import prep
    print(prep.make_part(a.proj, a.id, a.nome, a.y0, a.y1, a.pivo))


def cmd_spritesheet(a):
    from amllib import prep, project
    tmp, n = prep.spritesheet_to_sequence(a.proj, a.arquivo, a.cols, a.rows, a.fps, a.qtd)
    aid = project.add_asset(a.proj, tmp, role="sprite", origin="user", notes=f"{n} quadros de {a.arquivo}",
                            extra={"fps": a.fps})
    print(aid, n, "quadros")


def cmd_clipes(a):
    from amllib import prep, project
    m = project.load_manifest(a.proj)
    path = os.path.join(a.proj, m["assets"][a.id]["file"])
    segs = prep.pick_clip_segments(path, a.n, prefer="acao" if a.modo == "acao" else "calmo")
    project.update_asset(a.proj, a.id, segments=segs)
    for s in segs:
        print(s)


def cmd_quadros(a):
    from amllib import prep
    print(prep.extract_stills(a.proj, a.id, _floats(a.tempos)))


def _audio(proj, src, start=0.0, dur=None):
    from amllib import audio, project
    os.makedirs(os.path.join(proj, "audio"), exist_ok=True)
    dest = os.path.join(proj, "audio", "original" + os.path.splitext(src)[1].lower())
    if not os.path.exists(dest):
        shutil.copy2(src, dest)
    wav = os.path.join(proj, "audio", "trilha.wav")
    audio.prepare_audio(dest, wav, start or 0.0, dur)
    ana = audio.analyze(wav)
    util.save_json(os.path.join(proj, "audio", "analysis.json"), ana)
    pj = project.load_project(proj)
    pj["audio"] = "audio/trilha.wav"
    util.save_json(os.path.join(proj, "project.json"), pj)
    print(audio.summary(ana))
    return wav


def cmd_audio(a):
    _audio(a.proj, a.arquivo, a.inicio, a.dur)


def _ref(proj, path):
    from amllib import reference
    out = os.path.join(proj, "metadata", "referencia")
    prof = reference.analyze(path, out)
    print(json.dumps({k: prof[k] for k in ("avg_shot_len", "median_shot_len", "cuts_per_min", "bw_ratio",
                                          "flash_rate_per_min", "silhouette_ratio", "move_mix", "sugestao")
                      if k in prof}, ensure_ascii=False, indent=2))
    print(f"folha: {prof.get('sheet')}")
    return prof


def cmd_referencia(a):
    if a.proj:
        _ref(a.proj, a.video)
    else:
        from amllib import reference
        prof = reference.analyze(a.video, a.saida)
        print(json.dumps(prof, ensure_ascii=False, indent=2)[:4000])


def cmd_plano(a):
    from amllib import plan, project, subject
    pj = project.load_project(a.proj)
    ref = util.load_json(os.path.join(a.proj, "metadata", "referencia", "perfil_referencia.json"))
    ent = util.load_json(os.path.join(a.proj, "metadata", "subject.json"))
    assets = None
    if ent and a.max_assets:
        assets, _ = subject.select_assets(a.proj, ent, a.max_assets)
    preset = a.preset or ((ref or {}).get("sugestao") or {}).get("preset")
    plan.make_plan(a.proj, preset=preset, duration=a.dur, audio=a.audio or pj.get("audio"), seed=a.seed, bpm=a.bpm,
                   assets=assets, reference=ref)
    print(open(os.path.join(a.proj, "metadata", "plano.md"), encoding="utf-8").read())


def cmd_previa(a):
    from amllib import render
    edit = util.load_json(os.path.join(a.proj, "edit.json"))
    if a.video:
        rng = (a.inicio or 0.0, a.fim or edit["duration"])
        print(render.render(a.proj, out=os.path.join(a.proj, "output", "previa.mp4"), preview=True, t_range=rng))
        return
    ts = _floats(a.tempos) if a.tempos else [s["start"] + s["dur"] / 2 for s in edit["shots"]]
    ps = render.stills(a.proj, ts, scale=0.4)
    out = render.contact_sheet(ps, os.path.join(a.proj, "output", "previa_quadros.jpg"), cols=min(9, len(ps)),
                               width=1800)
    print(out)


def cmd_render(a):
    from amllib import render
    out = render.render(a.proj, out=a.saida, gpu=a.gpu, workers=a.workers)
    print(out)


def cmd_qa(a):
    from amllib import qa
    rep = qa.validate(a.proj, a.video)
    print(open(os.path.join(a.proj, "metadata", "qa.md"), encoding="utf-8").read())
    sys.exit(0 if rep.get("ok") else 3)


def cmd_fontes(a):
    from amllib import project
    txt, w = project.sources_report(a.proj)
    print(txt)


def cmd_montar(a):
    """Depois da curadoria: seleção variada → plano → quadros de prévia → render → QA → fontes."""
    from amllib import plan, prep, project, qa, render, subject
    m = project.load_manifest(a.proj)
    for k, r in m["assets"].items():
        if r.get("kind") == "image" and r.get("approved", True):
            prep.prep_image(a.proj, k)
    ent = util.load_json(os.path.join(a.proj, "metadata", "subject.json")) or {"nome": "", "categorias": []}
    sel, _ = subject.select_assets(a.proj, ent, a.max_assets or 14)
    pj = project.load_project(a.proj)
    ref = util.load_json(os.path.join(a.proj, "metadata", "referencia", "perfil_referencia.json"))
    edit = plan.make_plan(a.proj, preset=a.preset, duration=a.dur, audio=pj.get("audio"), seed=a.seed or 7,
                          bpm=a.bpm, assets=sel, reference=ref)
    ts = [s["start"] + s["dur"] / 2 for s in edit["shots"]]
    sheet = render.contact_sheet(render.stills(a.proj, ts, scale=0.35),
                                 os.path.join(a.proj, "output", "previa_quadros.jpg"), cols=min(9, len(ts)), width=1800)
    print(f"prévia de quadros: {sheet}")
    if a.previa:
        return
    out = render.render(a.proj, out=a.saida, gpu=a.gpu)
    rep = qa.validate(a.proj, out)
    print(open(os.path.join(a.proj, "metadata", "qa.md"), encoding="utf-8").read())
    project.sources_report(a.proj)
    print(f"VÍDEO: {out}\nFONTES: {os.path.join(a.proj, 'metadata', 'FONTES.md')}")
    if not rep.get("ok"):
        sys.exit(3)


def cmd_animar(a):
    """Anima UMA imagem existente (sem gerar nada novo): recorte → parallax/câmera → efeitos → MP4."""
    from amllib import plan, prep, project, qa, render  # noqa
    src = os.path.abspath(a.imagem)
    base = os.path.splitext(os.path.basename(src))[0]
    proj = a.proj or os.path.join(os.path.dirname(src), f"animar-{util.slug(base, 30)}")
    project.init_project(proj, f"animar {base}", a.formato, a.preset or "cinematico")
    aid = project.add_asset(proj, src, role="imagem principal", origin="user")
    info = prep.prep_image(proj, aid, no_segment=a.sem_recorte)
    pj = project.load_project(proj)
    cam = a.camera or ("orbit" if info["technique"] == "parallax" else "push_in_slow")
    shot = {"id": "s00", "asset": aid, "start": 0.0, "dur": float(a.dur), "technique": info["technique"],
            "camera": {"preset": cam, "intensity": a.intensidade}, "parallax": info.get("parallax_max", 0.0)}
    if info["technique"] == "parallax" and not a.sem_personagem:
        shot["character"] = {"breathe": 1.0, "sway": 0.5, "flutter": 0.5}
    if a.efeitos:
        shot["fx"] = [{"type": e} for e in a.efeitos.split(",") if e]
    edit = {"format": pj["format"], "fps": pj["format"]["fps"], "duration": float(a.dur), "grade": a.cor,
            "grain": 0.04, "vignette": 0.3, "impacts": [{"t": t, "s": 1.0} for t in _floats(a.impactos or "")],
            "shots": [shot], "fade_in": 0.3, "fade_out": 0.5}
    util.save_json(os.path.join(proj, "edit.json"), edit)
    out = render.render(proj, out=a.saida or os.path.join(proj, "output", f"{util.slug(base, 30)}_animado.mp4"),
                        preview=a.previa)
    rep = qa.validate(proj, out, sheet=False, expect_scale=0.5 if a.previa else 1.0)
    print(f"{out}\nQA: {'ok' if rep['ok'] else rep['errors']}")


# ------------------------------------------------------------------ parser

def main():
    ap = argparse.ArgumentParser(prog="aml.py", description="Anime Motion Lab — edits com material EXISTENTE")
    sp = ap.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("env", help="verifica dependências, encoders, GPU, modelos e acesso às fontes")
    s.add_argument("--sem-rede", action="store_true")
    s.add_argument("--json")
    s.set_defaults(f=cmd_env)

    s = sp.add_parser("init", help="cria a estrutura do projeto")
    s.add_argument("proj")
    s.add_argument("--titulo")
    s.add_argument("--formato", default="vertical")
    s.add_argument("--preset", default="auto")
    s.add_argument("--fps", type=int)
    s.set_defaults(f=cmd_init)

    s = sp.add_parser("add", help="registra arquivos do usuário (copia; o original fica intacto)")
    s.add_argument("proj")
    s.add_argument("arquivos", nargs="+")
    for o in ("--funcao", "--fonte", "--pagina", "--autor", "--licenca"):
        s.add_argument(o, default="")
    s.add_argument("--licenca-verificada", action="store_true")
    s.set_defaults(f=cmd_add)

    s = sp.add_parser("consultas", help="interpreta o nome e lista as buscas por categoria (p/ WebSearch)")
    s.add_argument("nome")
    s.add_argument("--contexto")
    s.add_argument("--franquia")
    s.add_argument("--tipo", choices=["anime", "heroi", "atleta", "religioso", "geral"])
    s.add_argument("--midia", choices=["manga"])
    s.set_defaults(f=cmd_consultas)

    s = sp.add_parser("buscar", help="busca real nas APIs acessíveis (youtube, commons, openverse, archive, met, aic)")
    s.add_argument("proj")
    s.add_argument("consulta")
    s.add_argument("--fontes")
    s.add_argument("--limite", type=int, default=20)
    s.set_defaults(f=cmd_buscar)

    s = sp.add_parser("candidato", help="registra um achado do WebSearch/WebFetch (só dados vistos)")
    s.add_argument("proj")
    s.add_argument("--url", required=True)
    for o in ("--pagina", "--titulo", "--autor", "--licenca"):
        s.add_argument(o, default="")
    s.add_argument("--fonte", default="web")
    s.add_argument("--w", type=int)
    s.add_argument("--h", type=int)
    s.set_defaults(f=cmd_candidato)

    s = sp.add_parser("baixar", help="baixa um candidato (índice) ou URL e registra no manifesto")
    s.add_argument("proj")
    s.add_argument("--candidato", type=int)
    s.add_argument("--url")
    for o in ("--pagina", "--autor", "--licenca", "--funcao"):
        s.add_argument(o, default="")
    s.set_defaults(f=cmd_baixar)

    s = sp.add_parser("auto", help="NOME → entidade → buscas → download → folha de revisão (→ montar)")
    s.add_argument("proj")
    s.add_argument("nome")
    s.add_argument("--contexto", help="o pedido em texto livre (ex.: 'edit rap geek só mangá')")
    s.add_argument("--franquia")
    s.add_argument("--tipo", choices=["anime", "heroi", "atleta", "religioso", "geral"])
    s.add_argument("--midia", choices=["manga"])
    s.add_argument("--titulo")
    s.add_argument("--formato", default="vertical")
    s.add_argument("--preset", choices=["rap", "cinematico", "contemplativo"])
    s.add_argument("--audio")
    s.add_argument("--inicio", type=float, default=0.0)
    s.add_argument("--dur", type=float)
    s.add_argument("--referencia")
    s.add_argument("--fontes")
    s.add_argument("--extra", help="buscas extras separadas por |")
    s.add_argument("--por-busca", type=int, default=8)
    s.add_argument("--baixar", type=int, default=48)
    s.add_argument("--por-video", type=int, default=3)
    s.add_argument("--max-assets", type=int, default=14)
    s.add_argument("--sem-revisao", action="store_true", help="pula a curadoria visual (não recomendado)")
    s.set_defaults(f=cmd_auto)

    s = sp.add_parser("revisar", help="folha numerada dos assets para curadoria visual")
    s.add_argument("proj")
    s.add_argument("--todos", action="store_true")
    s.set_defaults(f=cmd_revisar)
    for nm, ok in (("aprovar", True), ("reprovar", False)):
        s = sp.add_parser(nm, help=f"{nm} itens pelo número da folha ou id")
        s.add_argument("proj")
        s.add_argument("itens", nargs="+")
        s.add_argument("--nota")
        s.set_defaults(f=(lambda a, ok=ok: cmd_aprovar(a, ok)))

    s = sp.add_parser("prep", help="recorte + camadas 2.5D (rembg) dos assets aprovados")
    s.add_argument("proj")
    s.add_argument("ids", nargs="*")
    s.add_argument("--modelo")
    s.add_argument("--forcar", action="store_true")
    s.add_argument("--sem-recorte", action="store_true")
    s.add_argument("--mascara")
    s.set_defaults(f=cmd_prep)

    s = sp.add_parser("parte", help="parte para puppet (faixa do recorte), ex.: cabeca 0 0.28")
    s.add_argument("proj")
    s.add_argument("id")
    s.add_argument("nome")
    s.add_argument("y0", type=float)
    s.add_argument("y1", type=float)
    s.add_argument("--pivo", type=float)
    s.set_defaults(f=cmd_parte)

    s = sp.add_parser("spritesheet", help="corta um spritesheet existente em sequência de quadros")
    s.add_argument("proj")
    s.add_argument("arquivo")
    s.add_argument("cols", type=int)
    s.add_argument("rows", type=int)
    s.add_argument("--fps", type=int, default=12)
    s.add_argument("--qtd", type=int)
    s.set_defaults(f=cmd_spritesheet)

    s = sp.add_parser("clipes", help="acha trechos de ação/calmos num vídeo existente (sem corte no meio)")
    s.add_argument("proj")
    s.add_argument("id")
    s.add_argument("--n", type=int, default=6)
    s.add_argument("--modo", choices=["acao", "calmo"], default="acao")
    s.set_defaults(f=cmd_clipes)

    s = sp.add_parser("quadros", help="extrai quadros de um vídeo registrado como novos assets")
    s.add_argument("proj")
    s.add_argument("id")
    s.add_argument("tempos")
    s.set_defaults(f=cmd_quadros)

    s = sp.add_parser("audio", help="registra a música e analisa BPM/batidas/impactos/seções")
    s.add_argument("proj")
    s.add_argument("arquivo")
    s.add_argument("--inicio", type=float, default=0.0)
    s.add_argument("--dur", type=float)
    s.set_defaults(f=cmd_audio)

    s = sp.add_parser("referencia", help="analisa um vídeo de referência → parâmetros de edição")
    s.add_argument("video")
    s.add_argument("--proj")
    s.add_argument("--saida")
    s.set_defaults(f=cmd_referencia)

    s = sp.add_parser("plano", help="gera edit.json + metadata/plano.md")
    s.add_argument("proj")
    s.add_argument("--preset", choices=["rap", "cinematico", "contemplativo"])
    s.add_argument("--dur", type=float)
    s.add_argument("--audio")
    s.add_argument("--seed", type=int, default=7)
    s.add_argument("--bpm", type=float)
    s.add_argument("--max-assets", type=int)
    s.set_defaults(f=cmd_plano)

    s = sp.add_parser("previa", help="folha de quadros (rápida) ou vídeo em baixa resolução (--video)")
    s.add_argument("proj")
    s.add_argument("--tempos")
    s.add_argument("--video", action="store_true")
    s.add_argument("--inicio", type=float)
    s.add_argument("--fim", type=float)
    s.set_defaults(f=cmd_previa)

    s = sp.add_parser("render", help="renderiza o edit.json (H.264 MP4)")
    s.add_argument("proj")
    s.add_argument("--saida")
    s.add_argument("--gpu", action="store_true")
    s.add_argument("--workers", type=int)
    s.set_defaults(f=cmd_render)

    s = sp.add_parser("qa", help="valida o vídeo final e as fontes")
    s.add_argument("proj")
    s.add_argument("--video")
    s.set_defaults(f=cmd_qa)

    s = sp.add_parser("fontes", help="gera metadata/FONTES.md (origem, autor, licença, transformações)")
    s.add_argument("proj")
    s.set_defaults(f=cmd_fontes)

    s = sp.add_parser("montar", help="depois da curadoria: seleção → plano → prévia → render → QA")
    s.add_argument("proj")
    s.add_argument("--preset", choices=["rap", "cinematico", "contemplativo"])
    s.add_argument("--dur", type=float)
    s.add_argument("--max-assets", type=int, default=14)
    s.add_argument("--seed", type=int, default=7)
    s.add_argument("--bpm", type=float)
    s.add_argument("--gpu", action="store_true")
    s.add_argument("--previa", action="store_true", help="para na folha de prévia")
    s.add_argument("--saida")
    s.set_defaults(f=cmd_montar)

    s = sp.add_parser("animar", help="anima UMA imagem existente e renderiza")
    s.add_argument("imagem")
    s.add_argument("--proj")
    s.add_argument("--saida")
    s.add_argument("--dur", type=float, default=6.0)
    s.add_argument("--formato", default="vertical")
    s.add_argument("--preset", default="cinematico")
    s.add_argument("--camera")
    s.add_argument("--intensidade", type=float, default=1.0)
    s.add_argument("--cor", default="epico")
    s.add_argument("--efeitos", help="glow,light_sweep,light_leak,glitch,...")
    s.add_argument("--impactos", help="tempos de impacto, ex.: 1.5,3.0")
    s.add_argument("--sem-recorte", action="store_true")
    s.add_argument("--sem-personagem", action="store_true")
    s.add_argument("--previa", action="store_true")
    s.set_defaults(f=cmd_animar)

    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
