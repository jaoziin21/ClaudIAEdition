#!/usr/bin/env python3
"""Efeito PARALLAX CUTOUT / TEMPORAL COLLAGE — recorta o sujeito do próprio vídeo e monta uma colagem 2.5D em camadas.

Planos (de trás para a frente): FUNDO (a filmagem, sem o sujeito, com profundidade: desfoque, cor e deslocamento próprios)
→ PLACAS (recorte fotográfico do fundo em P&B com borda de papel + bloco de cor) → ECOS (o sujeito de quadros anteriores
e/ou posteriores, translúcidos, com outro tratamento de cor e borda recortada) → SOMBRA → SUJEITO (o quadro atual, colorido,
com escala e posição próprias). Cada plano anda numa velocidade diferente = paralaxe. Uma câmera 2.5D leve move tudo junto.

Em cada MOMENTO (padrão 4 s), com easing:
  1 separação   o sujeito ganha sombra e borda e o fundo escurece e perde cor
  2 profundidade o fundo desliza devagar para um lado e desfoca; o sujeito cresce e anda para o outro
  3 colagem      2-3 ecos do sujeito (atrasos configuráveis) saem de dentro dele, translúcidos e com outra cor
  4 composição   placas de papel e de cor entram atrás, marcas de corte em volta do sujeito
  5 retorno      tudo volta ao lugar e se funde de novo na filmagem original
Fora dos momentos os quadros passam intactos. Resolução, fps e áudio são mantidos; o original não é tocado.

RECORTE: automático com rembg (padrão `u2net_human_seg` = pessoas — funciona também com personagem humano de anime, testado;
`isnet-anime` = personagem de anime não humano; `isnet-general-use` = objetos). Se o modelo perde o sujeito num quadro,
segura a máscara anterior.
Mantém só o sujeito principal (o maior, ou o mais perto de `sujeito: "x,y"`) e segue ele quadro a quadro; suaviza no tempo
(média de 3 quadros), fecha furos, tira pedacinhos soltos. Ajustes: `borda_ajuste` (px, + encolhe / − engorda) e `suavidade`.
Sem modelo ou para corrigir: `--mascara video_mascara.mp4` (vídeo P&B do mesmo tamanho/duração: branco = sujeito; pode vir do
After Effects/DaVinci) — o efeito usa essa máscara no lugar do recorte automático.
Limites honestos: cabelo fino, objetos segurados e mãos rápidas podem sair cortados ou com borda; várias pessoas coladas
podem virar um sujeito só. Recorte automático ~0,75 s por quadro (CPU) — só nos quadros do efeito.

uso:  python3 parallax.py entrada.mp4 saida.mp4 [--momentos 1.0,9.5] [--opcoes '{"ecos": 2, "borda": "rasgada"}'] [--nome valor]
Controles: intensidade · duracao · curva (suave|forte|elastica) · paralaxe · profundidade · vel_fundo · vel_sujeito · vel_ecos ·
  vel_placas · ecos (0-3) · atraso (s) · eco_direcao (antes|depois|ambos) · eco_escala · eco_opacidade · eco_estilo
  (mix|mono|duotone|contraste|cor) · placas (0-2) · cor_placa (hex) · borda (papel|rasgada|suave|nenhuma) · sujeito_escala ·
  fundo_cor (saturação 0-1) · fundo_luz (0-1) · sujeito_contraste · sombra · graficos · camera · separacao (true/false) ·
  modelo · mascara · borda_ajuste · suavidade · sujeito (auto|"x,y") · lado (1|-1) · semente
"""
import argparse, collections, json, math, os, subprocess, sys
import numpy as np
import cv2

PADRAO = dict(intensidade=1.0, duracao=4.0, curva='suave', paralaxe=1.0, profundidade=1.0,
              vel_fundo=1.0, vel_sujeito=1.0, vel_ecos=1.0, vel_placas=1.0,
              ecos=3, atraso=0.22, eco_direcao='antes', eco_escala=0.9, eco_opacidade=0.62, eco_estilo='mix',
              placas=2, cor_placa='2b5cff', borda='papel', sujeito_escala=1.0,
              fundo_cor=0.45, fundo_luz=0.72, sujeito_contraste=1.08,
              sombra=True, graficos=True, camera=True, separacao=True,
              modelo='u2net_human_seg', mascara='', borda_ajuste=0.0, suavidade=1.5, sujeito='auto', lado=1, semente=3)
LUM = np.array([.299, .587, .114], np.float32)


# ---------- curvas ----------
def clamp01(x):
    return min(1.0, max(0.0, x))


def curva(nome):
    if nome == 'forte':      # expo in-out
        return lambda t: 0.0 if t <= 0 else 1.0 if t >= 1 else (2 ** (20 * t - 10) / 2 if t < .5 else (2 - 2 ** (-20 * t + 10)) / 2)
    if nome == 'elastica':   # back out na entrada (passa um pouco e volta)
        def f(t):
            t = clamp01(t); c1 = 1.70158; c3 = c1 + 1
            return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
        return f
    return lambda t: (lambda x: 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2)(clamp01(t))   # cubic in-out


def janela(e, u, a, b, c, d):
    """sobe entre a-b, fica, desce entre c-d (u = 0..1 do momento)."""
    return e((u - a) / (b - a)) * (1 - e((u - c) / (d - c)))


def hexrgb(h):
    h = str(h).lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def sondar(arq):
    o = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                            'stream=width,height,r_frame_rate', '-of', 'json', arq]))['streams'][0]
    n, d = o['r_frame_rate'].split('/')
    return o['width'], o['height'], float(n) / float(d), o['r_frame_rate']


# ---------- recorte ----------
class Recorte:
    """máscara do sujeito principal por quadro (modelo rembg ou vídeo de máscara), seguindo o mesmo sujeito."""

    def __init__(self, o, W, H, arq_mascara):
        self.o, self.W, self.H = o, W, H
        self.ses = None
        self.mdec = None
        if arq_mascara:
            self.mdec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', arq_mascara, '-vf', f'scale={W}:{H}', '-f', 'rawvideo',
                                          '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
        else:
            from rembg import new_session
            self.ses = new_session(o['modelo'])
        self.alvo = None   # centro do sujeito no quadro anterior
        self.ultima = None  # última máscara boa (segura quando o modelo falha num quadro)

    def ler_mascara_externa(self):
        b = self.mdec.stdout.read(self.W * self.H)
        return np.frombuffer(b, np.uint8).reshape(self.H, self.W) if len(b) == self.W * self.H else np.zeros((self.H, self.W), np.uint8)

    def bruta(self, rgb8):
        from PIL import Image
        esc = 640 / max(self.W, self.H)
        im = Image.fromarray(rgb8).resize((max(8, int(self.W * esc)), max(8, int(self.H * esc))), Image.BILINEAR) if esc < 1 else Image.fromarray(rgb8)
        m = np.array(self.ses.predict(im)[0].resize((self.W, self.H), Image.BILINEAR))
        return m

    def principal(self, m, novo):
        """deixa só o sujeito principal (componente seguido de um quadro para o outro) e limpa a máscara."""
        o, sc = self.o, self.W / 1080
        bin_ = (m > 110).astype(np.uint8)
        k = max(3, int(9 * sc) | 1)
        bin_ = cv2.morphologyEx(bin_, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        n, lab, st, cen = cv2.connectedComponentsWithStats(bin_)
        if n <= 1:
            return np.zeros_like(m)
        area_min = 0.004 * self.W * self.H
        cand = [i for i in range(1, n) if st[i, 4] >= area_min] or [int(np.argmax(st[1:, 4])) + 1]
        if novo or self.alvo is None:
            if str(o['sujeito']) != 'auto':
                px, py = [float(v) for v in str(o['sujeito']).split(',')]
                alvo = np.array([px * self.W, py * self.H])
                esc = min(cand, key=lambda i: np.hypot(*(cen[i] - alvo)) / math.sqrt(st[i, 4]))
            else:
                esc = max(cand, key=lambda i: st[i, 4] * (1.4 - abs(cen[i][0] / self.W - .5)))
        else:
            esc = min(cand, key=lambda i: np.hypot(*(cen[i] - self.alvo)) / (self.W * .1) - st[i, 4] / (self.W * self.H * .05))
        self.alvo = cen[esc]
        # pedaços colados ao principal (mão, objeto) entram; o resto sai
        keep = (lab == esc).astype(np.uint8)
        perto = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(25 * sc) | 1,) * 2))
        for i in cand:
            if i != esc and st[i, 4] < .15 * st[esc, 4] and (perto[lab == i]).mean() > .3:   # só pedaço pequeno (mão, objeto), não outra pessoa
                keep[lab == i] = 1
        # preenche furos internos
        cont, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cheio = np.zeros_like(keep); cv2.drawContours(cheio, cont, -1, 1, -1)
        suave = cv2.dilate(cheio, np.ones((5, 5), np.uint8)).astype(np.float32)
        return (np.maximum(m.astype(np.float32) / 255 * suave, cheio * (m > 60)) * 255).astype(np.uint8)

    def mascara(self, rgb8, novo):
        if self.mdec:
            return self.ler_mascara_externa()
        m = self.principal(self.bruta(rgb8), novo)
        if novo:
            self.ultima = None
        area = (m > 128).mean()
        if self.ultima is not None and area < .35 * self.ultima[1]:
            return self.ultima[0]          # o modelo "perdeu" o sujeito neste quadro: segura a máscara anterior
        if area > .002:
            self.ultima = (m, area)
        return m


def refinar(ms, o, sc):
    """média de 3 quadros (sem tremer), ajuste da borda e suavização."""
    a = sum(w * m.astype(np.float32) for w, m in zip((.25, .5, .25), ms)) / 255.0
    aj = o['borda_ajuste'] * sc
    if abs(aj) >= .5:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(abs(aj)) * 2 + 1,) * 2)
        a = cv2.erode(a, k) if aj > 0 else cv2.dilate(a, k)
    if o['suavidade'] > 0:
        a = cv2.GaussianBlur(a, (0, 0), o['suavidade'] * sc + .3)
    return np.clip((a - .08) / .84, 0, 1)


# ---------- composição ----------
class Colagem:
    def __init__(self, W, H, fps, o):
        self.W, self.H, self.fps, self.o = W, H, fps, o
        self.sc = W / 1080
        self.e = curva(o['curva'])
        rng = np.random.default_rng(int(o['semente']))
        self.rasgo = cv2.GaussianBlur(rng.random((H // 4 + 1, W // 4 + 1)).astype(np.float32), (0, 0), 1.2)
        self.rasgo = cv2.resize((self.rasgo - self.rasgo.min()) / (np.ptp(self.rasgo) + 1e-6), (W, H))
        self.grao = rng.standard_normal((H, W)).astype(np.float32)
        self.cor = hexrgb(o['cor_placa'])

    # --- utilidades de camada ---
    def warp(self, img, M, borda=cv2.BORDER_CONSTANT):
        return cv2.warpAffine(img, M, (self.W, self.H), flags=cv2.INTER_LINEAR, borderMode=borda)

    @staticmethod
    def sobre(base, rgb, a):
        a = a[..., None]
        return base * (1 - a) + rgb * a

    def contorno(self, a, estilo, grossura):
        if estilo in ('nenhuma', 'suave') or grossura <= 0:
            return None
        r = max(1, int(grossura))
        d = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1,) * 2))
        if estilo == 'rasgada':   # espessura irregular, como papel rasgado
            d2 = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4 * r + 1,) * 2))
            d = np.maximum(d, d2 * (self.rasgo > .55))
            d = cv2.GaussianBlur(d, (0, 0), .8)
        return np.clip(d - a, 0, 1)

    def tratar(self, rgb, estilo, k):
        L = rgb @ LUM
        if estilo == 'mix':
            estilo = ['mono', 'duotone', 'contraste'][k % 3]
        if estilo == 'mono':
            g = np.clip((L - .5) * 1.5 + .55, 0, 1)
            return np.repeat(g[..., None], 3, 2)
        if estilo == 'duotone':
            g = np.clip((L - .5) * 1.3 + .5, 0, 1)[..., None]
            return np.array([.05, .08, .25], np.float32) * (1 - g) + self.cor * .35 + np.array([.55, .7, 1.0], np.float32) * g * .65
        if estilo == 'contraste':
            g = np.clip((L - .45) * 2.2 + .5, 0, 1)[..., None]
            return np.array([.08, .02, .03], np.float32) * (1 - g) + np.array([1.0, .32, .25], np.float32) * g
        return rgb   # 'cor'

    def quadro(self, F8, a, u, c, ecos):
        """F8 = quadro atual, a = máscara (0..1), u = 0..1 do momento, c = centro do sujeito, ecos = [(F8, a, centro), ...]."""
        o, W, H, sc, e = self.o, self.W, self.H, self.sc, self.e
        I = o['intensidade']
        g = janela(e, u, 0, .1, .88, 1.0) * min(1.0, I)          # mistura final com o original (entra e sai macio)
        if g <= .001 or a.max() < .2:
            return F8
        F = F8.astype(np.float32) / 255
        lado = 1 if int(o['lado']) >= 0 else -1
        e_sep = janela(e, u, 0, .16, .8, .97) if o['separacao'] else 0
        e_dep = janela(e, u, .08, .45, .76, .97)
        e_pla = janela(e, u, .38, .6, .74, .92) if o['placas'] > 0 else 0
        cam = (math.sin(math.pi * u) * .014 * W * o['paralaxe']) if o['camera'] else 0.0
        cx, cy = c

        # FUNDO: tira o sujeito (preenchimento rápido em 1/4) e dá profundidade
        q = 6
        buraco = cv2.dilate((a > .08).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(45 * sc) | 1,) * 2))
        pequeno = cv2.resize(F8, (W // q, H // q), interpolation=cv2.INTER_AREA)
        bq = cv2.dilate(cv2.resize(buraco, (W // q, H // q), interpolation=cv2.INTER_NEAREST), np.ones((3, 3), np.uint8))
        cheio = cv2.inpaint(pequeno, bq, 9, cv2.INPAINT_TELEA)
        cheio = cv2.GaussianBlur(cv2.resize(cheio, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255, (0, 0), 5 * sc)
        hb = cv2.GaussianBlur(buraco.astype(np.float32), (0, 0), 9 * sc)
        B = self.sobre(F, cheio, np.clip(hb * 1.6, 0, 1))   # sem o sujeito: o buraco vira fundo borrado (não aparece "fantasma")
        limpo = B
        sb = 1 + (.035 + .045 * o['profundidade']) * e_dep        # sempre >1 quando anda: não mostra borda
        pan = -lado * .045 * W * o['paralaxe'] * o['vel_fundo'] * e_dep + cam
        Mb = cv2.getRotationMatrix2D((W / 2, H / 2), 0, sb); Mb[0, 2] += pan; Mb[1, 2] += -.01 * H * e_dep
        B = self.warp(B, Mb, cv2.BORDER_REFLECT)
        des = 2.6 * sc * o['profundidade'] * e_dep
        if des > .3:
            B = cv2.GaussianBlur(B, (0, 0), des)
        cinza = (B @ LUM)[..., None]
        sat = 1 - (1 - o['fundo_cor']) * e_sep
        B = (cinza + (B - cinza) * sat) * (1 - (1 - o['fundo_luz']) * e_sep)
        C = B

        # PLACAS (plano do meio): foto P&B do entorno com borda de papel + bloco de cor
        if e_pla > .002:
            fat = .6 * cam
            if o['placas'] >= 2:   # bloco de cor atrás do sujeito, desce do alto
                pw, ph = .2 * W, .78 * H
                px, py = cx + lado * .07 * W + fat, H * .5 - (1 - e_pla) * H * .9 * o['vel_placas']
                bloco = np.zeros((H, W), np.float32)
                ret = cv2.boxPoints(((px, py), (pw, ph), 4 * lado))
                cv2.fillPoly(bloco, [ret.astype(np.int32)], 1.0)
                C = self.sobre(C, np.broadcast_to(self.cor, C.shape), cv2.GaussianBlur(bloco, (0, 0), .7) * .92 * e_pla)
            # recorte fotográfico do lugar (zoom do fundo SEM o sujeito, P&B contrastado), sobe de baixo
            pw, ph = int(.26 * W), int(.44 * H)
            zx = int(np.clip(cx - lado * .12 * W - pw * .4, 0, W - pw * .8)); zy = int(np.clip(cy - ph * .2, 0, H - ph * .8))
            foto = cv2.resize(limpo[zy:zy + int(ph * .8), zx:zx + int(pw * .8)], (pw, ph))
            foto = self.tratar(foto, 'mono', 0) * .92 + .04
            borda = int(7 * sc) + 2
            papel = np.ones((ph + 2 * borda, pw + 2 * borda, 3), np.float32) * np.array([.96, .95, .92], np.float32)
            papel[borda:-borda, borda:-borda] = foto
            ax = cx - lado * .19 * W + fat * 1.2
            ay = H * .6 + (1 - e_pla) * H * .95 * o['vel_placas']
            M = cv2.getRotationMatrix2D((papel.shape[1] / 2, papel.shape[0] / 2), -5 * lado, 1.0)
            M[0, 2] += ax - papel.shape[1] / 2; M[1, 2] += ay - papel.shape[0] / 2
            pa = self.warp(np.ones(papel.shape[:2], np.float32), M)
            sombra = self.warp(cv2.GaussianBlur(pa, (0, 0), 9 * sc), np.float32([[1, 0, 6 * sc], [0, 1, 10 * sc]]))
            C = C * (1 - (.45 * sombra * e_pla)[..., None])
            C = self.sobre(C, self.warp(papel, M), pa * e_pla)

        # ECOS (colagem temporal): o sujeito de outros quadros, translúcido, com outra cor, saindo de dentro dele
        lados = [lado * -1, lado, lado * -1]
        xs_ = np.nonzero(a.max(0) > .3)[0]
        larg = (xs_[-1] - xs_[0]) if len(xs_) else .2 * W          # largura do sujeito: ecos se afastam na proporção dele
        reduz = float(np.clip(.38 * W / max(larg, 1), .55, 1.0))
        for k, (E8, ea, ec) in enumerate(ecos):
            ek = janela(e, u, .26 + .06 * k, .52 + .06 * k, .7 - .03 * k, .88 - .02 * k)
            if ek <= .002 or ea.max() < .2:
                continue
            Ef = self.tratar(E8.astype(np.float32) / 255, o['eco_estilo'], k)
            s = o['eco_escala'] ** (1 + .35 * k) * (1 + .05 * (1 - ek)) * reduz
            sep = max((.15 + .1 * k) * W, larg * (.5 + .3 * k)) * o['vel_ecos'] * ek
            alvo = (cx + lados[k % 3] * sep + .4 * cam, cy + (.03 * k - .02) * H)
            M = cv2.getRotationMatrix2D((float(ec[0]), float(ec[1])), (3 - 2 * k) * lados[k % 3] * ek, s)
            M[0, 2] += alvo[0] - ec[0]; M[1, 2] += alvo[1] - ec[1]
            aw = self.warp(ea, M)
            ct = self.contorno(aw, o['borda'], 4 * sc)
            if ct is not None:
                C = self.sobre(C, np.float32([.97, .96, .93]), ct * ek * .9)
            C = self.sobre(C, self.warp(Ef, M), aw * ek * o['eco_opacidade'] * (1 - .12 * k))

        # SUJEITO (primeiro plano): escala e posição próprias, sombra, borda recortada
        ss = 1 + .075 * e_dep * o['sujeito_escala']
        tx = lado * .018 * W * o['vel_sujeito'] * e_dep - .25 * cam
        ty = -.015 * H * e_dep
        Ms = np.float32([[ss, 0, cx * (1 - ss) + tx], [0, ss, cy * (1 - ss) + ty]])
        Fs = F
        if o['sujeito_contraste'] != 1:
            Fs = np.clip((F - .5) * (1 + (o['sujeito_contraste'] - 1) * e_sep) + .5, 0, 1)
        aw = self.warp(a, Ms)
        if o['sombra']:
            so = cv2.GaussianBlur(aw, (0, 0), 10 * sc)
            so = self.warp(so, np.float32([[1, 0, 10 * sc * lado], [0, 1, 16 * sc]]))
            C = C * (1 - (.5 * so * max(e_sep, e_dep))[..., None])
        ct = self.contorno(aw, o['borda'], 5 * sc * e_sep)
        if ct is not None:
            C = self.sobre(C, np.float32([.98, .97, .95]), ct * e_sep)
        C = self.sobre(C, self.warp(Fs, Ms), aw)

        # GRÁFICOS: marcas de corte em volta do sujeito + linha de cor
        if o['graficos'] and e_pla > .05:
            ys, xs = np.nonzero(aw > .3)
            if len(xs):
                x0, x1, y0, y1 = xs.min() - 14 * sc, xs.max() + 14 * sc, ys.min() - 14 * sc, ys.max() + 14 * sc
                L_ = 34 * sc * e_pla; t = max(1, int(2.2 * sc))
                cor = (.97, .96, .93)
                for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
                    p = (int(x), int(y))
                    cv2.line(C, p, (int(x + dx * L_), int(y)), cor, t, cv2.LINE_AA)
                    cv2.line(C, p, (int(x), int(y + dy * L_)), cor, t, cv2.LINE_AA)
                yl = int(y1 + 10 * sc)
                cv2.line(C, (int(x0), yl), (int(x0 + (x1 - x0) * e_pla), yl), tuple(float(v) for v in self.cor), max(2, int(5 * sc)), cv2.LINE_AA)
        # grão leve para unir as camadas
        C = C + (self.grao * .012)[..., None] * e_sep
        out = F * (1 - g) + np.clip(C, 0, 1) * g
        return (out * 255 + .5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description='Parallax Cutout / Temporal Collage')
    ap.add_argument('arq_in', metavar='entrada.mp4'); ap.add_argument('arq_out', metavar='saida.mp4')
    ap.add_argument('--momentos', default='', help='segundos de início, separados por vírgula (padrão: 0.6)')
    ap.add_argument('--opcoes', default='{}', help='JSON com os controles')
    for k, v in PADRAO.items():
        if k != 'mascara':
            ap.add_argument('--' + k, default=None)
    ap.add_argument('--mascara', default=None, help='vídeo P&B com a máscara do sujeito (no lugar do recorte automático)')
    ap.add_argument('--crf', default='16')
    a = ap.parse_args()
    o = dict(PADRAO); o.update(json.loads(a.opcoes))
    for k in PADRAO:
        if getattr(a, k, None) is not None:
            o[k] = getattr(a, k)
    for k, v in PADRAO.items():   # tipos
        if isinstance(v, bool):
            o[k] = o[k] if isinstance(o[k], bool) else str(o[k]).lower() in ('1', 'true', 'sim', 'yes')
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            o[k] = type(v)(float(o[k]))
    mom = a.momentos or o.get('momentos') or '0.6'
    mom = sorted(float(x) for x in (mom if isinstance(mom, list) else str(mom).replace(' ', '').split(',')) if str(x) != '')
    W, H, fps, rfps = sondar(a.arq_in)
    sc = W / 1080
    D = o['duracao']; NF = int(round(D * fps))
    dk = max(1, int(round(o['atraso'] * fps)))
    nec = int(o['ecos'])
    offs = []
    for k in range(1, nec + 1):
        if o['eco_direcao'] == 'antes' or (o['eco_direcao'] == 'ambos' and k % 2):
            offs.append(-k * dk if o['eco_direcao'] == 'antes' else -((k + 1) // 2) * dk)
        else:
            offs.append(k * dk if o['eco_direcao'] == 'depois' else (k // 2) * dk)
    atras = max([0] + [-x for x in offs]); frente = max([0] + offs) + 1
    ini = [int(round(t * fps)) for t in mom]
    precisa = lambda n: any(f0 - atras - 1 <= n <= f0 + NF + frente for f0 in ini)
    dentro = lambda n: next((i for i, f0 in enumerate(ini) if f0 <= n < f0 + NF), None)
    print(f'parallax: {W}x{H} @ {fps:.3f} fps, momentos {mom}, {D} s, ecos {offs} quadros, recorte: '
          f'{"máscara " + o["mascara"] if o["mascara"] else o["modelo"]}', file=sys.stderr)

    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', a.arq_in, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', rfps, '-i', '-',
                            '-i', a.arq_in, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', a.crf,
                            '-pix_fmt', 'yuv420p', '-c:a', 'copy', a.arq_out], stdin=subprocess.PIPE)
    rec = Recorte(o, W, H, o['mascara'])
    col = Colagem(W, H, fps, o)
    tam = W * H * 3
    quadros, mascaras = {}, {}
    centros = {}           # centro suavizado por momento
    lido, escrito, ativos, fim = 0, 0, 0, False
    ultimo_mom = None

    def mascara_ref(n):
        return refinar([mascaras.get(max(n - 1, 0), mascaras[n]), mascaras[n], mascaras.get(n + 1, mascaras[n])], o, sc)

    def centro(am):
        ys, xs = np.nonzero(am > .3)
        if not len(xs):
            return None
        return np.array([xs.mean(), (ys.min() + ys.max()) / 2], np.float32)

    while True:
        # lê até ter o quadro (escrito + frente) na memória
        while not fim and lido <= escrito + frente:
            buf = dec.stdout.read(tam)
            if len(buf) < tam:
                fim = True; break
            img = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            if precisa(lido):
                quadros[lido] = img
                novo = ultimo_mom is None or lido - ultimo_mom > 1
                mascaras[lido] = rec.mascara(img, novo); ultimo_mom = lido
                if lido % 15 == 0:
                    print(f'  recorte quadro {lido}', file=sys.stderr)
            elif rec.mdec:
                rec.ler_mascara_externa()
            if not precisa(lido):
                quadros[lido] = img
            lido += 1
        if escrito >= lido:
            break
        n = escrito
        img = quadros[n]
        k = dentro(n)
        if k is None:
            enc.stdin.write(img.tobytes())
        else:
            u = (n - ini[k]) / NF
            am = mascara_ref(n)
            c = centro(am)
            if c is not None:
                cs = centros.get(k)
                centros[k] = c if cs is None else cs * .8 + c * .2      # centro sem tremer
            ecos = []
            for off in offs:
                m2 = n + off
                if m2 in mascaras and m2 in quadros:
                    ea = refinar([mascaras.get(m2 - 1, mascaras[m2]), mascaras[m2], mascaras.get(m2 + 1, mascaras[m2])], o, sc)
                    ce = centro(ea)
                    if ce is not None:
                        ecos.append((quadros[m2], ea, ce))
            if k in centros:
                enc.stdin.write(col.quadro(img, am, u, centros[k], ecos).tobytes()); ativos += 1
            else:
                enc.stdin.write(img.tobytes())
        escrito += 1
        for velho in [x for x in quadros if x < escrito - atras - 2]:
            quadros.pop(velho, None); mascaras.pop(velho, None)
    enc.stdin.close(); enc.wait(); dec.wait()
    if rec.mdec:
        rec.mdec.kill()
    print(f'PRONTO {a.arq_out} ({escrito} quadros, {ativos} com efeito)', file=sys.stderr)
    if enc.returncode:
        sys.exit(enc.returncode)


if __name__ == '__main__':
    main()
