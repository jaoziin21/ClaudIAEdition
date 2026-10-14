#!/usr/bin/env python3
"""Efeito XEROX HALFTONE / PIXEL SORT — processa a própria imagem do vídeo, quadro a quadro (não é camada por cima).

Em cada MOMENTO escolhido, durante `duracao` segundos:
  início   imagem original
  entrada  a textura xerográfica (retícula de pontos + papel + toner + contraste agressivo) invade uma região e se espalha
  pico     pixel sort (rastros geométricos de pixels ordenados por brilho), glitch direcional em faixas e separação RGB
  saída    a distorção se desfaz pelas bordas e a filmagem original volta
Fora das janelas os quadros passam intactos. Resolução, fps e áudio do arquivo de entrada são mantidos; o original não é tocado.

uso:  python3 xerox.py entrada.mp4 saida.mp4 [--momentos 1.2,6.5] [--opcoes '{"reticula": 10, "sort_dir": "v"}'] [--controle]
      (no motor, o faixa.mjs chama sozinho quando o lado.json tem o efeito "xerox"; momentos padrão = cortes das cenas)
Controles (todos opcionais, em --opcoes ou como --nome valor):
  intensidade 0..1.5   força geral                      mistura 0..1      original x processado no pico
  reticula px          tamanho da célula (em 1080 px)   densidade 0.5..2  tamanho dos pontos (mais = mais tinta)
  angulo graus         ângulo da retícula               contraste 0.5..2  contraste xerox    grao 0..2  granulação/toner
  sort_dir h|v         direção do pixel sort            sort_comp 0..1    comprimento máx. do rastro (fração da largura)
  sort_limiar 0..1     brilho mínimo que entra no rastro
  frag 0..2            quantidade de fragmentação       rgb px            deslocamento máx. dos canais (em 1080 px)
  regiao auto|tudo|"x,y"   onde começa (auto = parte com mais detalhe)   raio 0.2..1.2  até onde se espalha
  duracao s  entrada s  saida s    tempo total, de invasão e de dissolução    semente  n   (mesma semente = mesmo resultado)
Desempenho (4 núcleos): ~0,14 s por quadro na faixa do motor (1080x760), ~0,2 s em 1080x1080 e ~0,45 s em 1920x1080 —
só nos quadros com efeito; o resto é só copiado (mas o vídeo inteiro é recodificado em H.264, crf 16). Limitação: o pixel sort
é feito em faixas (não no quadro todo) para ficar rápido e geométrico; precisa de numpy + opencv (o setup.sh instala).
"""
import argparse, json, math, subprocess, sys
import numpy as np
import cv2

PADRAO = dict(intensidade=1.0, mistura=1.0, reticula=9.0, densidade=1.0, angulo=45.0, contraste=1.0, grao=0.6,
              sort_dir='h', sort_comp=0.5, sort_limiar=0.38, frag=0.7, rgb=7.0, regiao='auto', raio=0.55,
              duracao=3.0, entrada=0.9, saida=0.8, semente=7)
PAPEL = np.array([0.94, 0.92, 0.87], np.float32)
TINTA = np.array([0.06, 0.06, 0.075], np.float32)


def ss(a, b, x):  # smoothstep
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def sondar(arq):
    o = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                            'stream=width,height,r_frame_rate', '-of', 'json', arq]))['streams'][0]
    n, d = o['r_frame_rate'].split('/')
    return o['width'], o['height'], float(n) / float(d), o['r_frame_rate']


def ruido_suave(h, w, escala, rng):
    """ruído de baixa frequência em -1..1 (estável: calculado uma vez por momento)."""
    a = rng.standard_normal((max(2, h // escala), max(2, w // escala))).astype(np.float32)
    a = cv2.resize(cv2.GaussianBlur(a, (0, 0), 1.2), (w, h), interpolation=cv2.INTER_CUBIC)
    return a / (np.abs(a).max() + 1e-6)


class Momento:
    """tudo o que é fixo durante uma aparição do efeito (região, faixas, rajadas) — evita flicker aleatório."""

    def __init__(self, t0, quadro, o, W, H, fps, k):
        self.t0, self.o = t0, o
        rng = np.random.default_rng(int(o['semente']) * 1000 + k)
        sc = W / 1080.0
        # região: auto = ponto com mais detalhe (bordas) do primeiro quadro, puxado para o centro
        if o['regiao'] == 'tudo':
            cx, cy = 0.5, 0.5
        elif o['regiao'] == 'auto':
            g = cv2.cvtColor(cv2.resize(quadro, (W // 8, H // 8)), cv2.COLOR_RGB2GRAY).astype(np.float32)
            det = cv2.GaussianBlur(np.abs(cv2.Laplacian(g, cv2.CV_32F)), (0, 0), 3)
            yy, xx = np.mgrid[0:det.shape[0], 0:det.shape[1]]
            det *= np.exp(-(((xx / det.shape[1] - .5) / .35) ** 2 + ((yy / det.shape[0] - .5) / .35) ** 2))
            iy, ix = np.unravel_index(np.argmax(det), det.shape)
            cx, cy = (ix + .5) / det.shape[1], (iy + .5) / det.shape[0]
        else:
            cx, cy = [float(v) for v in str(o['regiao']).split(',')]
        self.c = (cx, cy)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        nx, ny = xx / W - cx, (yy / H - cy) * (H / W)          # distância em proporção da largura
        d = np.sqrt((nx / 1.35) ** 2 + ny ** 2)                # espalha mais na horizontal (como varredura de copiadora)
        self.dist = d / max(d.max(), 1e-6)
        self.borda1, self.borda2 = ruido_suave(H, W, int(70 * sc) or 8, rng), ruido_suave(H, W, int(40 * sc) or 8, rng)
        self.rasgo = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 0.8 * sc + .3)  # borda que "pega" como toner
        # faixas do pixel sort (fixas no momento): dentro da região
        L = (H if o['sort_dir'] == 'h' else W)
        centro = cy if o['sort_dir'] == 'h' else cx
        self.faixas = []
        for _ in range(int(5 + 5 * min(o['frag'], 1.5))):
            meio = np.clip(centro + rng.normal(0, .17), .03, .97) * L
            alt = rng.integers(int(6 * sc) + 2, int(64 * sc) + 4)
            self.faixas.append((int(max(0, meio - alt / 2)), int(min(L, meio + alt / 2)), rng.uniform(.75, 1.0), rng.uniform(0, 1)))
        # rajadas de glitch direcional e chutes de RGB (instantes fixos perto do pico, 2-3 quadros cada)
        D = o['duracao']
        self.rajadas = []
        for _ in range(int(round(2 + 3 * min(o['frag'], 1.5)))):
            ini = rng.uniform(.33, .78) * D
            fatias = [(rng.uniform(-.25, .25), rng.integers(int(4 * sc) + 2, int(46 * sc) + 4),
                       rng.choice([-1, 1]) * rng.uniform(18, 170) * sc, rng.random() < .45) for _ in range(rng.integers(3, 8))]
            self.rajadas.append((ini, ini + rng.integers(2, 4) / fps, fatias))
        self.chutes = sorted(rng.uniform(.38, .72, 3) * D)
        self.fps = fps

    def curvas(self, t):
        o, u, D = self.o, t - self.t0, self.o['duracao']
        ent, sai = min(o['entrada'], D * .45), min(o['saida'], D * .45)
        esp = ss(0, ent, u) * (1 - ss(D - sai, D, u))                           # invasão / dissolução
        srt = ss(ent * .55, D * .5, u) * (1 - ss(D * .55, D - sai * .5, u))     # pixel sort: cresce até o pico e recolhe
        chute = max([math.exp(-((u - c) * self.fps / 1.6) ** 2) for c in self.chutes] + [0])
        rgb = .22 * srt + .78 * chute * esp
        return esp, srt, rgb, u


class Xerox:
    def __init__(self, W, H, fps, o):
        self.W, self.H, self.fps, self.o = W, H, fps, o
        self.sc = sc = W / 1080.0
        s = max(3.0, o['reticula'] * sc)
        self.cel = s
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        a = math.radians(o['angulo'])
        ru, rv = (xx * math.cos(a) + yy * math.sin(a)) / s, (-xx * math.sin(a) + yy * math.cos(a)) / s
        fu, fv = ru - np.floor(ru) - .5, rv - np.floor(rv) - .5
        self.dd = np.sqrt(fu * fu + fv * fv)                                     # distância ao centro do ponto (0..0.707)
        self.aa = 0.9 / s
        rng = np.random.default_rng(int(o['semente']))
        manchas = 1 + .05 * ruido_suave(H, W, int(90 * sc) or 8, rng) + .025 * ruido_suave(H, W, int(14 * sc) or 4, rng)
        fibra = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), sigmaX=6 * sc, sigmaY=.6)
        self.papel = (PAPEL[None, None, :] * (manchas + .05 * fibra / (np.abs(fibra).max() + 1e-6))[..., None]).astype(np.float32)
        # listras do cilindro da copiadora (fixas, bem fracas)
        lis = cv2.resize(rng.random((1, max(2, W // 3))).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
        self.listra = (lis - .5) * .10
        self.graos = [rng.standard_normal((H, W)).astype(np.float32) for _ in range(4)]
        self.pintas = [(rng.random((H, W)) < .0009).astype(np.float32) for _ in range(4)]

    def ruido(self, f, lista, sl, periodo=6):
        """granulação que muda devagar: passa de uma textura para a outra em `periodo` quadros (sem piscar)."""
        p = f / periodo; i = int(p) % len(lista); w = p - int(p)
        return (lista[i][sl] * (1 - w) + lista[(i + 1) % len(lista)][sl] * w) / math.sqrt((1 - w) ** 2 + w * w)

    def textura(self, rgb, f, sl):
        """imagem xerografada: preto chapado nas sombras, retícula nos meios-tons, papel nas luzes (só na janela `sl`)."""
        o = self.o
        L = (rgb @ np.array([.299, .587, .114], np.float32))
        k = 1.7 * o['contraste']
        Lc = np.clip((L - .5) * k + .55, 0, 1)
        Lb = cv2.blur(Lc, (int(self.cel) | 1, int(self.cel) | 1))               # média da célula (desliza suave entre quadros)
        escuro = np.clip(1 - Lb, 0, 1)
        r = .707 * np.sqrt(np.clip(escuro * o['densidade'], 0, 1.4))
        tinta = ss(r + self.aa, r - self.aa, self.dd[sl])
        tinta = np.maximum(tinta, ss(.26, .14, Lc))                               # sombras viram preto chapado (cara de xerox)
        tinta = np.minimum(tinta, ss(.97, .88, Lc))                             # luzes estouram para o papel
        gr, pin = self.ruido(f, self.graos, sl), self.ruido(f, self.pintas, sl, 9) * .7   # toner orgânico, muda devagar
        tinta = np.clip(tinta * (1 - .16 * o['grao'] * np.abs(gr)) + pin * o['grao'] + self.listra[sl] * o['grao'], 0, 1)
        return self.papel[sl] * (1 - tinta[..., None]) + TINTA * tinta[..., None]

    def ordenar(self, C, src8, m, srt, mom, y0):
        """pixel sort: em faixas fixas, ordena por brilho os trechos acima do limiar (comprimento máx. cresce até o pico).
        Faixas alternam rastro colorido (pixels da filmagem) e rastro cinza (tinta/papel). Escreve direto em C (só onde há rastro)."""
        o = self.o
        vert = o['sort_dir'] == 'v'
        if vert:   # vistas transpostas: escrever nelas escreve em C
            C, src8, m = C.transpose(1, 0, 2), src8.transpose(1, 0, 2), m.T
        n, linhas = C.shape[1], C.shape[0]
        cap = max(2, int(o['sort_comp'] * n * srt))
        lim = .9 - (.9 - o['sort_limiar']) * srt
        alcance = cv2.dilate(np.ascontiguousarray(m), np.ones((1, cap // 2 * 2 + 1), np.uint8)) if cap > 2 else m   # rastro sai da região
        lum = np.array([.299, .587, .114], np.float32)
        for a, b, forca, fase in mom.faixas:
            if not vert:   # faixas em coordenadas do quadro; a janela começa na linha y0
                a, b = max(0, a - y0), min(linhas, b - y0)
            if b - a < 2:
                continue
            R = np.clip((src8[a:b].astype(np.float32) / 255.0 - .5) * 1.3 + .52, 0, 1)
            LL = R @ lum
            if fase < .45:   # faixa cinza: mesma paleta do xerox
                R = TINTA + (PAPEL - TINTA) * LL[..., None]
            eleg = (LL > lim + (fase - .5) * .14) & (alcance[a:b] > 0)
            if not eleg.any():
                continue
            idx = np.broadcast_to(np.arange(n), eleg.shape)
            ini = eleg & ~np.concatenate([np.zeros((eleg.shape[0], 1), bool), eleg[:, :-1]], 1)
            pos = idx - np.maximum.accumulate(np.where(ini, idx, 0), axis=1)
            capf = max(2, int(cap * forca))
            novo = ~eleg | ini | (pos % capf == 0)
            seg = np.cumsum(novo, axis=1).astype(np.float64)
            chave = LL if fase < .8 else -LL      # algumas faixas ordenam ao contrário
            ordem = np.argsort(seg * 4.0 + chave + 1.5, axis=1, kind='stable')
            S = np.take_along_axis(R, ordem[..., None], axis=1)
            onde = eleg & ~((pos < 3) & ini)      # trechos de 1-2 px não contam
            faixa = C[a:b]
            faixa[onde] = S[onde]

    def quadro(self, rgb8, t, f, m):
        o, H, W = self.o, self.H, self.W
        esp, srt, kr, u = m.curvas(t)
        I = o['intensidade']
        if esp * I <= .002:
            return rgb8
        # máscara da região: cresce a partir do ponto, borda orgânica que se mexe devagar, e "rasgada" como toner
        mov = .5 + .5 * math.sin(u * 1.7)
        R = esp * o['raio'] * 1.25 if o['regiao'] != 'tudo' else esp * 2
        # janela de trabalho = retângulo onde a máscara existe (achado em 1/4 da resolução) → só ela é processada
        q = 4
        perto = (R - m.dist[::q, ::q] + .16 * (m.borda1[::q, ::q] * (1 - mov) + m.borda2[::q, ::q] * mov)) > -.02
        if not perto.any():
            return rgb8
        ys, xs = np.nonzero(perto.any(1))[0], np.nonzero(perto.any(0))[0]
        pad = int(self.cel * 2 + o['rgb'] * self.sc * 1.5 + 8)
        y0, y1 = max(0, ys[0] * q - pad), min(H, (ys[-1] + 1) * q + pad)
        x0, x1 = max(0, xs[0] * q - pad), min(W, (xs[-1] + 1) * q + pad)
        if o['sort_dir'] == 'v':
            y0, y1 = 0, H
        sy, sx = slice(y0, y1), slice(x0, x1)
        C = rgb8[sy].astype(np.float32) / 255.0          # linhas da janela, largura inteira (o rastro sai da região)
        Fr = C[:, sx]
        ruido = m.borda1[sy, sx] * (1 - mov) + m.borda2[sy, sx] * mov
        base = np.clip((R - m.dist[sy, sx] + .16 * ruido) / .10, 0, 1)
        mxc = ss(m.rasgo[sy, sx] - .22, m.rasgo[sy, sx] + .22, base) * min(1.0, I) * o['mistura']
        X = self.textura(Fr, f, (sy, sx))
        C[:, sx] = Fr * (1 - mxc[..., None]) + X * mxc[..., None]
        # pixel sort no meio da invasão
        if srt * I > .03:
            m8 = np.zeros(C.shape[:2], np.uint8); m8[:, sx] = mxc > .02
            self.ordenar(C, rgb8[sy], m8, min(1.0, srt * I), m, y0)
        # glitch direcional: rajadas de 2-3 quadros com as mesmas fatias (sem tremer à toa)
        for ini, fim, fatias in m.rajadas:
            if ini <= u < fim:
                for dy, alt, dx, cor in fatias:
                    a = int(np.clip(m.c[1] + dy, 0, 1) * H) - y0; b = min(y1 - y0, a + int(alt)); a = max(0, a)
                    desl = int(dx * min(o['frag'], 2) * I)
                    if b > a and desl:
                        C[a:b] = np.roll(C[a:b], desl, axis=1)
                        if cor:
                            C[a:b, :, 0] = np.roll(C[a:b, :, 0], int(desl * .25), axis=1)
        # separação cromática (falha de registro de impressão): forte nos chutes, leve no pico
        d = int(round(o['rgb'] * self.sc * kr * I))
        if d:
            sub = C[:, sx]
            peso = np.clip(mxc * 1.4, 0, 1)[..., None]
            sep = sub.copy()
            sep[..., 0] = np.roll(np.roll(sub[..., 0], d, axis=1), d // 3, axis=0)
            sep[..., 2] = np.roll(sub[..., 2], -d, axis=1)
            C[:, sx] = sub * (1 - peso) + sep * peso
        # granulação só onde há efeito
        if o['grao'] > 0:
            C[:, sx] += (self.ruido(f + 3, self.graos, (sy, sx)) * .03 * o['grao'] * mxc)[..., None]
        out = rgb8.copy()
        out[sy] = (np.clip(C, 0, 1) * 255 + .5).astype(np.uint8)
        return out


def main():
    ap = argparse.ArgumentParser(description='Xerox Halftone / Pixel Sort')
    ap.add_argument('arq_in', metavar='entrada.mp4'); ap.add_argument('arq_out', metavar='saida.mp4')
    ap.add_argument('--momentos', default='', help='segundos de início, separados por vírgula (padrão: 0.6)')
    ap.add_argument('--opcoes', default='{}', help='JSON com os controles')
    for k, v in PADRAO.items():
        ap.add_argument('--' + k, type=type(v) if not isinstance(v, str) else str, default=None)
    ap.add_argument('--crf', default='16')
    a = ap.parse_args()
    o = dict(PADRAO); o.update(json.loads(a.opcoes))
    for k in PADRAO:
        if getattr(a, k) is not None:
            o[k] = getattr(a, k)
    for k, v in PADRAO.items():
        if isinstance(v, float):
            o[k] = float(o[k])
    mom = a.momentos or o.get('momentos') or '0.6'
    mom = sorted(float(x) for x in (mom if isinstance(mom, list) else str(mom).replace(' ', '').split(',')) if str(x) != '')
    W, H, fps, rfps = sondar(a.arq_in)
    print(f'xerox: {W}x{H} @ {fps:.3f} fps, momentos {mom}, duração {o["duracao"]} s', file=sys.stderr)
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', a.arq_in, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', rfps, '-i', '-',
                            '-i', a.arq_in, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', a.crf,
                            '-pix_fmt', 'yuv420p', '-c:a', 'copy', a.arq_out], stdin=subprocess.PIPE)
    X = Xerox(W, H, fps, o)
    n, tam, ativos, cache = 0, W * H * 3, 0, {}
    while True:
        buf = dec.stdout.read(tam)
        if len(buf) < tam:
            break
        t = n / fps
        k = next((i for i, t0 in enumerate(mom) if t0 <= t < t0 + o['duracao']), None)
        if k is None:
            enc.stdin.write(buf)
        else:
            img = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            if k not in cache:
                cache = {k: Momento(mom[k], img, o, W, H, fps, k)}
            enc.stdin.write(X.quadro(img, t, n, cache[k]).tobytes()); ativos += 1
        n += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print(f'PRONTO {a.arq_out} ({n} quadros, {ativos} com efeito)', file=sys.stderr)
    if enc.returncode:
        sys.exit(enc.returncode)


if __name__ == '__main__':
    main()
