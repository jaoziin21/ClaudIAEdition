// Super 8: poeira, fios e riscos de projetor, vazamento de luz laranja depois de cada corte, queimado de filme nos "burns",
// janela de projetor com cantos arredondados que respira. (Tirado da Legenda dinâmica.)
EFX.add('super8', { camada: 'cima', draw(g, t, D, P, U) {
  const { W, H, BAND: B, rnd } = U, f = Math.floor(t * 30), r = rnd(f * 7919 + 3), k0 = P.forca ?? 1;
  g.beginPath(); g.rect(0, B.y, W, B.h); g.clip();
  for (const c of U.cortes) { const k = (t - c) / 1.1; if (k < 0 || k > 1) continue;
    const rc = rnd(Math.floor(c * 100)), side = rc() < .5 ? -1 : 1, a = Math.sin(Math.PI * k) * (0.35 + rc() * 0.2) * k0;
    const cx = W * (0.5 + side * (0.75 - k * 0.6)), cy = B.y + B.h * (0.2 + rc() * 0.6), gr = g.createRadialGradient(cx, cy, 0, cx, cy, W * 0.7);
    gr.addColorStop(0, `rgba(255,150,60,${a})`); gr.addColorStop(0.35, `rgba(230,60,30,${a * 0.6})`); gr.addColorStop(1, 'rgba(120,0,0,0)');
    g.globalCompositeOperation = 'screen'; g.fillStyle = gr; g.fillRect(0, B.y, W, B.h); g.globalCompositeOperation = 'source-over'; }
  for (const b of D.burns || []) { const k = (t - b + 0.25) / 0.7; if (k < 0 || k > 1) continue;
    const rb = rnd(Math.floor(b * 77)), cx = W * (0.25 + rb() * 0.5), cy = B.y + B.h * (0.3 + rb() * 0.4), a = 0.8 * Math.sin(Math.PI * k);
    const gr = g.createRadialGradient(cx, cy, 0, cx, cy, W * (0.15 + 0.9 * (1 - Math.pow(1 - k, 4))));
    gr.addColorStop(0, `rgba(255,250,235,${a})`); gr.addColorStop(0.25, `rgba(255,190,90,${a * 0.9})`); gr.addColorStop(0.6, `rgba(200,60,10,${a * 0.6})`); gr.addColorStop(1, 'rgba(60,0,0,0)');
    g.globalCompositeOperation = 'screen'; g.fillStyle = gr; g.fillRect(0, B.y, W, B.h); g.globalCompositeOperation = 'source-over'; }
  const n = Math.floor(r() * 6 * k0);
  for (let i = 0; i < n; i++) { const x = r() * W, y = B.y + r() * B.h, rad = 1 + r() * 3, light = r() < 0.45;
    g.fillStyle = light ? `rgba(255,245,225,${0.2 + r() * 0.3})` : `rgba(0,0,0,${0.3 + r() * 0.35})`; g.beginPath(); g.ellipse(x, y, rad, rad * (0.5 + r()), r() * 3, 0, 7); g.fill(); }
  if (r() < 0.07) { const x = r() * W, y = B.y + r() * B.h; g.strokeStyle = 'rgba(0,0,0,.4)'; g.lineWidth = 1.4;
    g.beginPath(); g.moveTo(x, y); g.bezierCurveTo(x + 30 - r() * 60, y + 20, x - 20 + r() * 40, y + 40, x + 25 - r() * 50, y + 60); g.stroke(); }
  const rb2 = rnd(Math.floor(t / 1.9) * 104729 + 9);
  if ((t % 1.9) < 0.6 && rb2() < 0.7) { const x = rb2() * W + Math.sin(t * 50) * 2; g.fillStyle = `rgba(255,248,230,${0.12 + rb2() * 0.15})`; g.fillRect(x, B.y, 1.6, B.h); }
  if ((t % 1.9) < 0.6 && rb2() < 0.3) { const x = rb2() * W; g.fillStyle = 'rgba(0,0,0,.28)'; g.fillRect(x, B.y, 1.2, B.h); }
  if (P.janela !== false) { const rr = 70 + 6 * Math.sin(t * 9), e = 10;
    g.fillStyle = '#000'; g.beginPath(); g.rect(0, B.y, W, B.h); g.roundRect(e, B.y + e, W - 2 * e, B.h - 2 * e, rr); g.fill('evenodd');
    const vg = g.createRadialGradient(W / 2, B.y + B.h / 2, B.h * 0.35, W / 2, B.y + B.h / 2, W * 0.72);
    vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,.55)'); g.fillStyle = vg; g.fillRect(0, B.y, W, B.h); }
} });
