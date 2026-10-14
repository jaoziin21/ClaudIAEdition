#!/usr/bin/env python3
"""Vitrine: o mesmo trecho de Vinland Saga, trocando a legenda (ou o efeito) a cada ~5 s.
uso: python3 monta.py legendas|efeitos   (roda os renders em paralelo, dentro do engine do canal)"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ENG = '/home/user/getsemani---canal-/getsemani-videos/engine'
PROJ = '/home/user/getsemani---canal-/getsemani-videos/projetos/2026-10-09-inimigos'
SRC = '/home/user/getsemani---canal-/getsemani-videos/entrada/eu-nao-tenho-inimigos-2s.mp4'
OUT = os.path.dirname(os.path.abspath(__file__))
modo = sys.argv[1]
words = json.load(open(f'{PROJ}/words.json'))
cortes = sorted({c['t'] for c in json.load(open(f'{PROJ}/lado.json'))['cenas']})

JAN = [(5.2, 10.4), (10.4, 14.6), (14.6, 21.8), (23.0, 26.4), (26.4, 31.4), (31.4, 35.6), (35.6, 39.5), (39.5, 45.4), (45.4, 51.0),
       (51.6, 56.4), (57.0, 62.5), (67.0, 71.0), (72.3, 75.6)]
POS = {'street': (0.5, 0.5), 'sample-yellow': (0.5, 0.86), 'rocks': (0.32, 0.76), 'samplerocks': (0.33, 0.76), 'mistury': (0.36, 0.42),
       'dinamica': (0.3, 0.3), 'invisible': (0.5, 0.5), '3d-invisivel': (0.5, 0.5), 'red-sharp': (0.5, 0.55),
       'black-sample': (0.5, 0.88), 'black-point': (0.5, 0.9), 'bruce': (0.87, 0.3), 'basic-on': (0.5, 0.72)}
if modo == 'legendas':
    SEG = [('street', 'Street', '/street', None, {'gritos': ['pequeno', 'Thors'], 'keywords': ['Thorfinn', 'treinado']}),
           ('sample-yellow', 'Sample Yellow', '/sample-yellow', None, {'keywords': ['volta?']}),
           ('rocks', 'Rocks', '/rocks', None, {'keywords': ['Drott', 'real.']}),
           ('samplerocks', 'Samplerocks', '/samplerocks', None, {'keywords': ['pergunta']}),
           ('mistury', 'Mistury', '/mistury', None, {'keywords': ['bater', 'paz.']}),
           ('dinamica', 'Legenda Dinâmica', '/legenda-dinamica', None, {'keywords': ['conhecer']}),
           ('invisible', 'Invisible', '/invisible', None, {'keywords': ['outro.']}),
           ('3d-invisivel', '3D Invisível', '/legenda-3d-invisivel', None, {'keywords': ['ódio.', 'bater']}),
           ('red-sharp', 'Red Sharp', '/red-sharp', None, {'keywords': ['idiotice.']}),
           ('black-sample', 'Black Sample', '/black-sample', None, {'keywords': []}),
           ('black-point', 'Black Point', '/black-point', None, {'keywords': ['sangue.']}),
           ('bruce', 'Bruce', '/bruce', None, {'keywords': []}),
           ('basic-on', 'Basic On', '/basic-on', None, {'keywords': [], 'credito': {'titulo': 'Nome do Filme (2019)', 'sub': '@seucanal'}})]
else:
    PAC = [('filme-antigo', 'Filme antigo'), ('manga', 'Mangá'), ('sonho', 'Sonho'), ('vhs', 'VHS'), ('sombrio', 'Sombrio'), ('cinema', 'Cinema'), ('rua', 'Rua'),
           ('xerox', 'Xerox'), ('parallax', 'Parallax'), ('black-and-white', 'Black and White')]
    MOM = {'xerox': [{'nome': 'xerox', 'momentos': [0.6]}], 'parallax': [{'nome': 'parallax', 'momentos': [0.5]}]}   # efeitos de processo: quando entram
    SEG = [('sample-yellow', f'Efeito {n}', f'/efeito-{p}', p, {'keywords': [], **({'efeitos': MOM[p]} if p in MOM else {})}) for p, n in PAC]

def seg(i):
    est, titulo, cmd, pac, extra = SEG[i]
    t0, t1 = JAN[i]; dur = round(t1 - t0, 2)
    d = f'{OUT}/{modo}/s{i}'; os.makedirs(d, exist_ok=True)
    ws = [{**w, 's': round(w['s'] - t0, 2), 'e': round(w['e'] - t0, 2)} for w in words if t0 <= w['s'] < t1 - 0.15]
    json.dump(ws, open(f'{d}/words.json', 'w'), ensure_ascii=False)
    x, y = POS[est]
    cen = [{'t': 0, 'x': x, 'y': y}] + [{'t': round(c - t0, 2), 'x': x, 'y': y} for c in cortes if t0 + 0.3 < c < t1 - 0.3]
    cfg = {'estilo': est, 'referencia': titulo, 'nomes': ['Thorfinn', 'Thors', 'Drott', 'Canuto', 'Ketil'], 'cenas': cen, **extra}
    if pac: cfg['pacote'] = pac
    json.dump(cfg, open(f'{d}/lado.json', 'w'), ensure_ascii=False)
    run = lambda *a: subprocess.run(a, cwd=ENG, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    run('ffmpeg', '-v', 'error', '-y', '-ss', str(t0), '-t', str(dur), '-i', f'{PROJ}/audio.wav', '-af', 'loudnorm=I=-20:TP=-2', '-ar', '48000', f'{d}/audio.wav')
    run('node', 'faixa.mjs', SRC, d, f'{d}/faixa.mp4', str(t0), str(dur))
    run('node', 'render_lado.mjs', d, f'{d}/faixa.mp4', f'{d}/audio.wav', f'{d}/clip.mp4', str(dur))
    # comando da skill embaixo, na faixa preta
    run('ffmpeg', '-v', 'error', '-y', '-i', f'{d}/clip.mp4', '-vf',
        f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf:text='{cmd}':fontcolor=0xF0CF4A:fontsize=44:x=(w-tw)/2:y=1500:box=1:boxcolor=black@0.0",
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', f'{d}/final.mp4')
    return d

if __name__ == '__main__':
    so = [int(a) for a in sys.argv[2:]] or range(len(SEG))
    with ThreadPoolExecutor(1) as ex:
        for r in ex.map(seg, so): print('pronto', r, flush=True)
