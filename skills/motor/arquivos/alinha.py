# Junta janelas de transcrição (cw_N = início N, dw_N = início N; janelas de 9 s a cada 4 s) e alinha com roteiro.txt.
# uso: python3 alinha.py <projeto_dir> [clips_words.json ...]  → words.json [{w,s,e}] (texto do roteiro, tempos da transcrição)
# MELHOR: passar a saída de transcribe_clips.mjs (trechos curtos cortados nas pausas = tempos certos). Sem isso usa as janelas cw_/dw_.
# Cada janela só contribui com as palavras do "miolo" dela (de s+2.5 a s+6.5), para não duplicar nem pegar bordas cortadas.
import json, re, sys, glob, os, difflib, unicodedata
P = sys.argv[1]
wins = {}
for f in glob.glob(os.path.join(P, '[cd]w_*.json')):
    s = float(re.search(r'w_([\d.]+)\.json', f).group(1)); wins[s] = json.load(open(f))
starts = sorted(wins)
raw = []
for i, s in enumerate(starts):
    lo = 0 if i == 0 else s + 2.5
    hi = 1e9 if i == len(starts) - 1 else starts[i + 1] + 2.5
    for w in wins[s]:
        a = w['s'] + s
        if lo <= a < hi and 'amara' not in w['w'].lower() and 'legendas' not in w['w'].lower():
            raw.append({'w': w['w'], 's': round(a, 2), 'e': round(w['e'] + s, 2)})
if len(sys.argv) > 2:   # trechos curtos (transcribe_clips.mjs): usa só eles
    raw = [w for f in sys.argv[2:] for c in json.load(open(f)) for w in c['words']
           if 'amara' not in c['text'].lower() and re.search(r'\w', w['w'])]
raw.sort(key=lambda w: w['s'])
norm = lambda t: re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFD', t.lower()))
rot = open(os.path.join(P, 'roteiro.txt')).read().split()
A, B = [norm(w) for w in rot], [norm(w['w']) for w in raw]
out = [None] * len(rot)
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
    if tag == 'equal':
        for k in range(i2 - i1): out[i1 + k] = {'w': rot[i1 + k], 's': raw[j1 + k]['s'], 'e': raw[j1 + k]['e']}
    elif tag == 'replace' and j2 > j1:   # divide o trecho da transcrição entre as palavras do roteiro
        s0, e0 = raw[j1]['s'], raw[j2 - 1]['e']; n = i2 - i1
        for k in range(n): out[i1 + k] = {'w': rot[i1 + k], 's': round(s0 + (e0 - s0) * k / n, 2), 'e': round(s0 + (e0 - s0) * (k + 1) / n, 2)}
# palavras sem tempo: interpola entre vizinhas
for i, o in enumerate(out):
    if o: continue
    prv = next((out[k] for k in range(i - 1, -1, -1) if out[k]), None); nxt = next((out[k] for k in range(i + 1, len(out)) if out[k]), None)
    s = prv['e'] if prv else (nxt['s'] - 0.3 if nxt else 0); e = nxt['s'] if nxt else s + 0.3
    out[i] = {'w': rot[i], 's': round(s, 2), 'e': round(max(e, s + 0.15), 2)}
for i in range(1, len(out)):   # garante ordem
    if out[i]['s'] < out[i - 1]['s']: out[i]['s'] = out[i - 1]['s'] + 0.02
json.dump(out, open(os.path.join(P, 'words.json'), 'w'), ensure_ascii=False)
miss = sum(1 for t, *_ in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes() if t != 'equal')
print(f'{len(out)} palavras, {len(raw)} da transcrição, {miss} trechos diferentes')
for o in out: print(f"{o['s']:6.2f} {o['w']}")
