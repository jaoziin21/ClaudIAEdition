#!/usr/bin/env python3
"""Aesthetic — prepara o plano da edição de quadrinhos (imagens paradas que "ganham vida").
uso (dentro de motor/):  python3 -I aesthetic/prepara.py <projeto_dir>
Lê projeto/aesthetic.json:
  {"audio": "audio.wav",            # música/narração (cortes na batida)
   "duracao": 25,                   # opcional (padrão = duração do áudio)
   "imagens": "imagens",            # pasta com JPG/PNG (ordem = nome do arquivo). PNG com fundo transparente = personagem recortado
   "de_video": "../entrada/x.mp4",  # opcional: tira quadros do vídeo para a pasta de imagens (se a pasta estiver vazia)
   "recorte": true,                 # tenta recortar o personagem de cada imagem (rembg isnet-anime) para o movimento em camadas
   "keywords": ["mundo"],           # palavras vermelhas (texto vem de words.json, se existir)
   "fps": 60,
   "corte_min": 0.7, "corte_max": 1.6}
Gera engine/aesthetic_data.js (const AE = {...}) para scene_aesthetic.html.
"""
import json, os, sys, glob, subprocess, random
import numpy as np

proj = sys.argv[1]
cfg = json.load(open(os.path.join(proj, 'aesthetic.json')))
audio = os.path.join(proj, cfg.get('audio', 'audio.wav'))
FPS = cfg.get('fps', 60)

def dur_de(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).decode())
DUR = float(cfg.get('duracao') or dur_de(audio))

# ---- imagens ----
pasta = os.path.join(proj, cfg.get('imagens', 'imagens')); os.makedirs(pasta, exist_ok=True)
imgs = sorted(f for f in glob.glob(os.path.join(pasta, '*')) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')))
if not imgs and cfg.get('de_video'):
    v = os.path.join(proj, cfg['de_video']) if not os.path.isabs(cfg['de_video']) else cfg['de_video']
    # quadros nas trocas de cena (os momentos mais diferentes do vídeo); se vier pouco, completa com 1 a cada 2 s
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', v, '-vf', "select='gt(scene,0.2)',scale=1600:-2", '-vsync', 'vfr', '-q:v', '3', os.path.join(pasta, 'c_%03d.jpg')], check=True)
    if len(glob.glob(os.path.join(pasta, 'c_*.jpg'))) < 12:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', v, '-vf', 'fps=1/2,scale=1600:-2', '-q:v', '3', os.path.join(pasta, 'f_%03d.jpg')], check=True)
    imgs = sorted(f for f in glob.glob(os.path.join(pasta, '*')) if f.lower().endswith('.jpg'))
if not imgs: sys.exit('sem imagens: ponha JPG/PNG em ' + pasta + ' ou use "de_video"')

# recorte do personagem (para o movimento em camadas): rembg isnet-anime; se não der, segue sem
recortes = {}
if cfg.get('recorte'):
    try:
        from rembg import remove, new_session
        from PIL import Image
        ses = new_session('isnet-anime'); rdir = os.path.join(pasta, '_recorte'); os.makedirs(rdir, exist_ok=True)
        for f in imgs:
            out = os.path.join(rdir, os.path.splitext(os.path.basename(f))[0] + '.png')
            if not os.path.exists(out):
                im = Image.open(f).convert('RGB'); im.thumbnail((1600, 1600)); remove(im, session=ses).save(out)
            a = np.array(Image.open(out))[:, :, 3]
            cob = (a > 128).mean()
            if 0.04 < cob < 0.7: recortes[f] = out   # recorte útil: nem vazio, nem a imagem inteira
        print(f'recortes úteis: {len(recortes)}/{len(imgs)}')
    except Exception as e:
        print('recorte indisponível:', e)

# ---- batidas (fluxo espectral simples) ----
pcm = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', audio, '-t', str(DUR), '-ac', '1', '-ar', '22050', '-f', 'f32le', '-'])
x = np.frombuffer(pcm, np.float32); SR, HOP, N = 22050, 512, 2048
fr = np.lib.stride_tricks.sliding_window_view(np.pad(x, (0, N)), N)[::HOP] * np.hanning(N)
S = np.log1p(np.abs(np.fft.rfft(fr, axis=1))[:, :400])
flux = np.maximum(0, np.diff(S, axis=0)).sum(1); flux = (flux - flux.mean()) / (flux.std() + 1e-9)
tt = (np.arange(len(flux)) + 1) * HOP / SR
w = int(0.12 * SR / HOP)
pk = [i for i in range(w, len(flux) - w) if flux[i] == flux[i - w:i + w + 1].max() and flux[i] > 0.6]
beats = [(float(tt[i]), float(flux[i])) for i in pk]
forte = np.percentile([b[1] for b in beats], 80) if beats else 9

# palavras (texto palavra por palavra) — words.json do projeto, se existir
words = json.load(open(os.path.join(proj, 'words.json'))) if os.path.exists(os.path.join(proj, 'words.json')) else []
words = [w for w in words if w['s'] < DUR]
KW = {k.lower() for k in cfg.get('keywords', [])}

# ---- cortes: próxima batida forte entre corte_min e corte_max; sem batida → corte_max ----
cmin, cmax = cfg.get('corte_min', 0.7), cfg.get('corte_max', 1.6)
cand = beats + [(w['s'], 0.8) for w in words if w['w'].strip('.,!?').lower() in KW]
cuts, t = [0.0], 0.0
while t < DUR - cmin:
    c = [b for b in cand if t + cmin <= b[0] <= t + cmax]
    t = max(c, key=lambda b: b[1])[0] if c else t + (cmin + cmax) / 2
    if t < DUR - 0.35: cuts.append(round(t, 3))
cuts.append(DUR)

# ---- planos: imagem + movimento (sem repetir em seguida) ----
rnd = random.Random(7)
MOV = ['zoom', 'card', 'pan', 'gira', 'card', 'zoom', 'voa', 'tremor']
shots, prev = [], None
for i in range(len(cuts) - 1):
    f = imgs[i % len(imgs)]
    ops = [m for m in MOV if m != prev] + (['camadas', 'camadas'] if f in recortes else [])
    m = 'camadas' if f in recortes and prev != 'camadas' and rnd.random() < 0.65 else rnd.choice(ops); prev = m   # recorte útil → prefere camadas
    s, e = cuts[i], cuts[i + 1]
    bt = max([b[1] for b in beats if abs(b[0] - s) < 0.06] or [0])
    shots.append({'s': s, 'e': e, 'img': 'file://' + os.path.abspath(f), 'rec': ('file://' + os.path.abspath(recortes[f])) if f in recortes else None,
                  'mov': m, 'forte': bool(bt >= forte), 'seed': rnd.randint(1, 10**6)})
# texto em pedaços de até 3 palavras (quebra em pontuação)
chunks, cur = [], []
for w in words:
    cur.append({'w': w['w'].strip('.,;:"“”').upper(), 's': w['s'], 'k': w['w'].strip('.,!?').lower() in KW})
    if len(cur) >= 3 or w['w'][-1:] in '.,!?;:':
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
for i, c in enumerate(chunks):
    c_end = chunks[i + 1][0]['s'] - 0.02 if i + 1 < len(chunks) else DUR
    chunks[i] = {'s': c[0]['s'] - 0.03, 'e': min(c_end, c[-1]['s'] + 1.6), 'ws': c}

AE = {'fps': FPS, 'dur': DUR, 'shots': shots, 'texto': chunks, 'beats': [b[0] for b in beats if b[1] >= forte]}
open('aesthetic_data.js', 'w').write('const AE=' + json.dumps(AE, ensure_ascii=False) + ';')
print(f'{len(imgs)} imagens, {len(beats)} batidas ({len(AE["beats"])} fortes), {len(shots)} planos, {len(chunks)} trechos de texto, {DUR:.1f} s')
for s in shots: print(f"  {s['s']:6.2f}-{s['e']:6.2f} {s['mov']:8s} {'FORTE ' if s['forte'] else ''}{os.path.basename(s['img'])}{' +recorte' if s['rec'] else ''}")
