"""Sujeito → edit: interpreta o nome, monta buscas específicas por CATEGORIA DE PLANO e escolhe assets variados.

resolve("Goku")  → entidade (Son Goku, Dragon Ball), tipo, aliases, termos de cena, termos a evitar, direção visual.
Nomes fora da tabela viram entidade "aberta": o agente confirma quem é com WebSearch e completa com --franquia/--tipo.
Nada aqui inventa resultado: só organiza O QUE buscar e COMO filtrar o que foi realmente encontrado.
"""
import re
import unicodedata

from . import util

# tipo → direção visual padrão e categorias de plano
TYPES = {
    "anime": {"preset": "rap", "grade": "anime_rap",
              "categorias": ["close", "pose", "acao", "transformacao", "aberto", "silhueta", "contemplativo", "clipe"]},
    "heroi": {"preset": "cinematico", "grade": "epico",
              "categorias": ["close", "pose", "acao", "aberto", "silhueta", "contemplativo", "clipe"]},
    "atleta": {"preset": "rap", "grade": "epico",
               "categorias": ["close", "acao", "comemoracao", "aberto", "contemplativo", "clipe"]},
    "religioso": {"preset": "contemplativo", "grade": "dourado",
                  "categorias": ["close", "aberto", "contemplativo", "silhueta", "pose"]},
    "geral": {"preset": "cinematico", "grade": "epico", "categorias": ["close", "aberto", "acao", "contemplativo"]},
}

# termos de busca por categoria (inglês rende mais resultados; {n} = nome canônico, {f} = franquia)
CAT_QUERIES = {
    "anime": {
        "close": ["{n} close up face anime", "{n} eyes close up scene"],
        "pose": ["{n} official art high resolution", "{n} key visual {f}"],
        "acao": ["{n} fight scene {f}", "{n} best fight moments", "{n} attack scene 4k"],
        "transformacao": ["{n} transformation scene", "{n} powers up scene"],
        "aberto": ["{n} {f} wallpaper 4k", "{f} opening scene {n}"],
        "silhueta": ["{n} silhouette scene", "{n} dark scene"],
        "contemplativo": ["{n} sad scene", "{n} emotional scene {f}"],
        "clipe": ["{n} raw clips for editing", "{n} twixtor clips 4k", "{n} clip official {f}"],
    },
    "heroi": {
        "close": ["{n} close up scene", "{n} face close up {f}"], "pose": ["{n} official poster", "{n} key art"],
        "acao": ["{n} fight scene", "{n} action scene 4k"], "aberto": ["{n} wide shot scene", "{f} wallpaper"],
        "silhueta": ["{n} silhouette"], "contemplativo": ["{n} emotional scene"], "clipe": ["{n} scene clip official"],
    },
    "atleta": {
        "close": ["{n} close up portrait", "{n} face celebration"], "acao": ["{n} skills highlights", "{n} best goals"],
        "comemoracao": ["{n} celebration", "{n} trophy celebration"], "aberto": ["{n} stadium wide shot"],
        "contemplativo": ["{n} emotional moment"], "clipe": ["{n} highlights 4k"],
    },
    "religioso": {
        "close": ["{n} painting face detail public domain", "{n} icon"],
        "aberto": ["{n} classical painting public domain", "{n} painting museum high resolution"],
        "contemplativo": ["{n} prayer painting", "{n} gethsemane painting"],
        "silhueta": ["{n} cross silhouette", "{n} crucifixion painting"],
        "pose": ["{n} sermon on the mount painting", "{n} resurrection painting"],
    },
    "geral": {"close": ["{n} close up"], "aberto": ["{n} high resolution"], "acao": ["{n} action"],
              "contemplativo": ["{n} cinematic"]},
}

# modo "só mangá" (pedido comum: anime cai no Content ID; mangá tem bem menos chance — mas TAMBÉM tem direitos)
MANGA_QUERIES = {
    "close": ["{n} manga panels black and white", "{n} manga edit black and white"],
    "pose": ["{f} manga {n} best panels", "{n} manga panels compilation"],
    "acao": ["{f} manga {n} fight chapter", "{n} manga fight panels black and white"],
    "transformacao": ["{n} transformation manga chapter", "{f} super manga chapter {n}"],
    "aberto": ["{f} manga chapter reading {n}", "{f} manga double page {n}"],
    "silhueta": ["{n} manga motion comic black and white", "{n} motion manga"],
    "contemplativo": ["{f} manga {n} emotional chapter", "{n} manga edit sad"],
}


KNOWN = {
    "goku": dict(nome="Son Goku", franquia="Dragon Ball", tipo="anime",
                 aliases=["goku", "son goku", "kakarot", "kakarotto", "ultra instinct goku", "goku ssj", "super saiyan goku"],
                 cenas=["ultra instinct", "super saiyan", "kamehameha", "spirit bomb", "vs jiren", "vs frieza", "vs vegeta"],
                 evitar=["goku black", "gohan", "goten", "vegito", "gogeta"]),
    "naruto": dict(nome="Naruto Uzumaki", franquia="Naruto", tipo="anime",
                   aliases=["naruto", "naruto uzumaki"], cenas=["sage mode", "nine tails", "rasengan", "vs sasuke", "vs pain"],
                   evitar=["boruto", "minato", "kurama only"]),
    "itachi": dict(nome="Itachi Uchiha", franquia="Naruto", tipo="anime", aliases=["itachi", "itachi uchiha"],
                   cenas=["susanoo", "tsukuyomi", "amaterasu", "vs sasuke", "crows"], evitar=["sasuke only", "shisui"]),
    "madara": dict(nome="Madara Uchiha", franquia="Naruto", tipo="anime", aliases=["madara", "madara uchiha"],
                   cenas=["vs shinobi alliance", "susanoo", "rinnegan", "wake up to reality"], evitar=["obito"]),
    "sasuke": dict(nome="Sasuke Uchiha", franquia="Naruto", tipo="anime", aliases=["sasuke", "sasuke uchiha"],
                   cenas=["chidori", "susanoo", "vs naruto", "vs itachi"], evitar=["itachi only", "sarada"]),
    "luffy": dict(nome="Monkey D. Luffy", franquia="One Piece", tipo="anime", aliases=["luffy", "monkey d luffy"],
                  cenas=["gear 5", "gear 4", "vs kaido", "haki"], evitar=[]),
    "vegeta": dict(nome="Vegeta", franquia="Dragon Ball", tipo="anime", aliases=["vegeta", "prince vegeta"],
                   cenas=["final flash", "ultra ego", "majin vegeta"], evitar=["goku only", "trunks"]),
    "thorfinn": dict(nome="Thorfinn", franquia="Vinland Saga", tipo="anime", aliases=["thorfinn"],
                     cenas=["i have no enemies", "vs askeladd", "farmland"], evitar=["thors", "canute"]),
    "gojo": dict(nome="Satoru Gojo", franquia="Jujutsu Kaisen", tipo="anime", aliases=["gojo", "satoru gojo"],
                 cenas=["domain expansion", "hollow purple", "infinity"], evitar=["geto"]),
    "jesus": dict(nome="Jesus Christ", franquia="Bible", tipo="religioso",
                  aliases=["jesus", "jesus cristo", "jesus christ", "cristo", "christ"],
                  cenas=["gethsemane", "sermon on the mount", "crucifixion", "resurrection", "last supper"],
                  evitar=["ai generated", "cartoon meme"]),
    "neymar": dict(nome="Neymar Jr", franquia="football", tipo="atleta", aliases=["neymar", "neymar jr"],
                   cenas=["skills", "goal celebration", "brazil national team"], evitar=["neymar sr"], pessoa_real=True),
    "cristiano ronaldo": dict(nome="Cristiano Ronaldo", franquia="football", tipo="atleta",
                              aliases=["cristiano ronaldo", "cr7", "ronaldo"], cenas=["siuu celebration", "bicycle kick"],
                              evitar=["ronaldo nazario", "ronaldinho"], pessoa_real=True),
    "thor": dict(nome="Thor", franquia="Marvel", tipo="heroi", aliases=["thor", "thor odinson"],
                 cenas=["stormbreaker", "bring me thanos", "lightning"], evitar=["loki", "thor god of war only"]),
    "batman": dict(nome="Batman", franquia="DC", tipo="heroi", aliases=["batman", "bruce wayne", "dark knight"],
                   cenas=["rooftop", "batsignal", "vs joker"], evitar=["robin", "batgirl"]),
}

# sinais no título que indicam material ruim para edit (de outro editor, desenho de fã, IA, reação, gameplay)
TITLE_BAD = {
    "ai generated": -1.0, " ai ": -0.6, "(ai)": -0.8, "midjourney": -1.0, "stable diffusion": -1.0,
    "reaction": -0.6, "react": -0.4, "fan art": -0.4, "fanart": -0.4, "drawing": -0.5, "speed paint": -0.5,
    "how to draw": -0.8, "tutorial": -0.5, "lego": -0.8, "cosplay": -0.7, "gameplay": -0.4, "minecraft": -0.9,
    "roblox": -0.9, "edit": -0.25, "amv": -0.25, "explained": -0.4, "ranking": -0.3, "top 10": -0.3,
    "theory": -0.4, "toy": -0.7, "figure": -0.5, "unboxing": -0.8,
}
TITLE_GOOD = {"official": 0.3, "4k": 0.2, "raw": 0.25, "clips for editing": 0.35, "scene": 0.15, "episode": 0.15,
              "clip": 0.1, "hd": 0.1, "twixtor": 0.15, "trailer": 0.15, "remastered": 0.1}
OFFICIAL_CHANNELS = ["toei animation", "crunchyroll", "bandai namco", "viz media", "aniplex", "netflix anime",
                     "funimation", "shueisha", "marvel entertainment", "dc", "warner bros", "fifa", "uefa", "cbf"]


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def resolve(name, contexto="", franquia=None, tipo=None, midia=None):
    """Identifica a entidade. Devolve dict com nome canônico, franquia, tipo, aliases, cenas, evitar, preset, grade,
    categorias e 'confirmar' (True quando o nome não está na tabela → o agente confirma com WebSearch)."""
    key = _norm(name)
    ctx = _norm(contexto)
    ent = None
    if key in KNOWN:
        ent = dict(KNOWN[key])
    else:
        for k, v in KNOWN.items():
            if key in [_norm(a) for a in v["aliases"]]:
                ent = dict(v)
                break
    # desambiguação simples por contexto ("ronaldo" + "fenômeno"/"r9" → Nazário)
    if key == "ronaldo" and any(w in ctx for w in ["fenomeno", "r9", "nazario", "1998", "2002"]):
        ent = dict(nome="Ronaldo Nazário", franquia="football", tipo="atleta", aliases=["ronaldo nazario", "r9"],
                   cenas=["2002 world cup"], evitar=["cristiano"], pessoa_real=True)
    if key == "thor" and any(w in ctx for w in ["god of war", "videogame", "jogo"]):
        ent = dict(nome="Thor (God of War)", franquia="God of War", tipo="heroi", aliases=["thor god of war"],
                   cenas=["vs kratos"], evitar=["marvel"])
    confirmar = ent is None
    if ent is None:
        ent = dict(nome=name.strip(), franquia=franquia or "", tipo=tipo or "geral", aliases=[key], cenas=[],
                   evitar=[])
    if franquia:
        ent["franquia"] = franquia
    if tipo:
        ent["tipo"] = tipo
    t = TYPES.get(ent["tipo"], TYPES["geral"])
    ent.update(preset=t["preset"], grade=t["grade"], categorias=t["categorias"], confirmar=confirmar,
               entrada=name)
    # nome usado nas buscas: o que a pessoa digitou se for um alias conhecido ("Goku" rende mais que "Son Goku")
    ent["busca"] = name.strip() if key in [_norm(a) for a in ent.get("aliases", [])] else ent["nome"]
    # religioso: tom contemplativo por padrão, mas pedido explícito de "épico"/"rap" muda
    if ent["tipo"] == "religioso" and any(w in ctx for w in ["epico", "rap", "trap", "agressivo"]):
        ent["preset"] = "cinematico"
    if any(w in ctx for w in ["rap", "trap", "geek", "amv", "agressivo"]) and ent["tipo"] != "religioso":
        ent["preset"] = "rap"
    if any(w in ctx for w in ["cinemat", "epico", "filme", "trailer"]) and "rap" not in ctx:
        ent["preset"] = "cinematico"
    if any(w in ctx for w in ["calmo", "contemplativo", "triste", "emocionante", "lento"]):
        ent["preset"] = "contemplativo"
    if midia == "manga" or any(w in ctx for w in ["manga", "mangá", "quadrinho", "painel", "paineis"]):
        ent["midia"] = "manga"
        ent["categorias"] = [c for c in ent["categorias"] if c != "clipe"]
        ent["grade"] = "neutro"  # mangá P&B: cor neutra, contraste vem dos efeitos
        ent["evitar"] = list(ent.get("evitar", [])) + ["anime", "episode", "ai generated"]
    return ent


def query_plan(ent, per_cat=2):
    """Consultas específicas por categoria de plano + cenas famosas (várias buscas, não uma genérica)."""
    n = ent.get("busca") or ent["nome"]
    f = ent.get("franquia") or ""
    manga = ent.get("midia") == "manga"
    tab = MANGA_QUERIES if manga else CAT_QUERIES.get(ent["tipo"], CAT_QUERIES["geral"])
    plan = []
    if manga:
        for c in ent.get("cenas", [])[:4]:
            plan.append({"categoria": "cena_famosa", "query": f"{n} {c} manga panel"})
        return [{"categoria": cat, "query": re.sub(r"\s+", " ", q.format(n=n, f=f)).strip()}
                for cat in ent["categorias"] if cat in tab for q in tab[cat][:per_cat]] + plan
    for cat in ent["categorias"]:
        for q in tab.get(cat, [])[:per_cat]:
            plan.append({"categoria": cat, "query": re.sub(r"\s+", " ", q.format(n=n, f=f)).strip()})
    for c in ent.get("cenas", [])[:4]:
        plan.append({"categoria": "cena_famosa", "query": f"{n} {c} scene"})
    if ent["tipo"] == "religioso":
        plan += [{"categoria": "dominio_publico", "query": f"{n} painting Wikimedia Commons"},
                 {"categoria": "dominio_publico", "query": f"{n} painting public domain museum"}]
    return plan


def relevance(ent, title, channel=""):
    """Pontua −1…1 se o título/canal indicam o sujeito certo e material útil. Rejeita confusões (evitar)."""
    t = " " + _norm(title) + " "
    ch = _norm(channel)
    score = 0.0
    names = [_norm(a) for a in ent.get("aliases", [])] + [_norm(ent["nome"])]
    if any(a and a in t for a in names):
        score += 0.5
    elif ent.get("franquia") and _norm(ent["franquia"]) in t:
        score += 0.15
    else:
        score -= 0.5
    for bad in ent.get("evitar", []):
        b = _norm(bad)
        if b and b in t and not any(a in t for a in names if a not in b):
            score -= 0.6
    for k, v in TITLE_BAD.items():
        if k in t:
            score += v
    for k, v in TITLE_GOOD.items():
        if k in t:
            score += v
    if any(o in ch for o in OFFICIAL_CHANNELS):
        score += 0.4
    if ent.get("midia") == "manga":
        score += 0.3 if ("manga" in t or "panel" in t or "chapter" in t) else -0.4
    return max(-1.0, min(1.0, score))


def manga_check(rec):
    """Página de mangá? Medido na imagem: pouca cor (P&B) ou cor de UM matiz só (mangá tingido/duotone)."""
    if rec.get("chroma_frac") is None:
        return None
    if rec["chroma_frac"] < 0.12:
        return "manga_pb"
    if rec.get("hue_spread", 1) < 0.18:
        return "manga_tingido"
    return "colorido"


def score_candidates(ent, cands):
    """Ordena candidatos de busca (antes de baixar): relevância do sujeito + resolução + licença + quadro."""
    lic_w = {"public_domain": 0.25, "cc": 0.2, "cc_nc": 0.1, "licensed": 0.2, "commercial": 0.0, "unknown": 0.0}
    for c in cands:
        rel = relevance(ent, c.get("title", ""), c.get("channel", "") or c.get("author", ""))
        px = (c.get("w") or 0) * (c.get("h") or 0)
        res = min(1.0, px / (1280 * 720)) if px else 0.4
        fr = {"maxresdefault": 0.1, "maxres2": 0.05}.get(c.get("frame"), 0.0)  # capa costuma ser o melhor quadro
        c["relevance"] = round(rel, 3)
        c["score_subject"] = round(0.6 * rel + 0.25 * res + lic_w.get(c.get("license_class"), 0.0) + fr, 3)
    return sorted(cands, key=lambda c: -c["score_subject"])


def pick_downloads(ent, cands, n=32, per_video=3):
    """Escolhe o que baixar: melhores por pontuação, no máx. `per_video` quadros por vídeo, cobrindo categorias."""
    chosen, per_vid, per_cat = [], {}, {}
    cands = [c for c in cands if c.get("relevance", 0) > 0]
    # 1ª passada: garante cada categoria; 2ª: completa por pontuação
    for pass_ in (0, 1):
        for c in cands:
            if len(chosen) >= n:
                break
            if c in chosen:
                continue
            vid = c.get("video_id") or c.get("page_url")
            if per_vid.get(vid, 0) >= per_video:
                continue
            cat = c.get("categoria", "?")
            if pass_ == 0 and per_cat.get(cat, 0) >= max(2, n // max(1, len(ent["categorias"]))):
                continue
            chosen.append(c)
            per_vid[vid] = per_vid.get(vid, 0) + 1
            per_cat[cat] = per_cat.get(cat, 0) + 1
    return chosen


def near_duplicates(proj, aids, thresh=6):
    """Hash perceptual (dHash 8x8) → grupos de imagens quase iguais (mesma imagem com outro zoom/corte leve)."""
    import os
    from PIL import Image
    from . import project
    m = project.load_manifest(proj)
    hashes = {}
    for a in aids:
        p = os.path.join(proj, m["assets"][a]["file"])
        if m["assets"][a].get("kind") != "image":
            continue
        g = Image.open(p).convert("L").resize((9, 8), Image.BILINEAR)
        import numpy as np
        arr = np.asarray(g, np.int16)
        hashes[a] = (arr[:, 1:] > arr[:, :-1]).flatten()
    dup = {}
    keys = list(hashes)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if b in dup:
                continue
            if int((hashes[a] != hashes[b]).sum()) <= thresh:
                dup[b] = a
    return dup  # b é duplicata de a


def select_assets(proj, ent, max_n=16, exclude=None):
    """Seleção final variada entre assets aprovados: tira duplicatas, equilibra enquadramentos
    (close/médio/aberto/silhueta/ação/clipe) e privilegia qualidade."""
    from . import media, project
    m = project.load_manifest(proj)
    pj = project.load_project(proj)
    exclude = set(exclude or [])
    pool = [a for a, r in m["assets"].items() if r.get("approved", True) and a not in exclude
            and r.get("kind") in ("image", "video", "sequence")]
    dups = near_duplicates(proj, pool)
    pool = [a for a in pool if a not in dups]
    scored = []
    for a in pool:
        r = m["assets"][a]
        s, why = media.score_asset(r, pj["format"])
        s += 0.3 * float(r.get("relevance", 0.3))
        scored.append((s, a, r.get("framing") or ["?"]))
    scored.sort(reverse=True)
    chosen, count = [], {}
    for s, a, fr in scored:
        main = fr[0]
        if count.get(main, 0) >= max(2, int(max_n * 0.4)):
            continue
        chosen.append(a)
        count[main] = count.get(main, 0) + 1
        if len(chosen) >= max_n:
            break
    for s, a, fr in scored:  # sobrou vaga (pool pequeno): completa sem limite de enquadramento
        if len(chosen) >= max_n:
            break
        if a not in chosen:
            chosen.append(a)
            count[fr[0]] = count.get(fr[0], 0) + 1
    util.log(f"seleção: {len(chosen)} assets · enquadramentos {count} · {len(dups)} duplicatas removidas")
    return chosen, dups
