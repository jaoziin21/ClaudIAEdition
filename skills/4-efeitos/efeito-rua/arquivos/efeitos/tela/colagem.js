// Colagem: nos cortes (um sim, um não) e nas palavras-chave, 1–3 painéis com OUTROS MOMENTOS do próprio vídeo pipocam por cima
// da imagem (atrás da legenda), com 1 quadro de clarão e empurrão lento. (Tirado do Street; o motor tira os quadros sozinho.)
(() => { const imgs = new Map(); let EV = null;
EFX.add('colagem', { camada: 'baixo', async prepara(D, P, U) {
  const { rnd } = U, st = D.stills || []; EV = [];
    const ev = (tt, seed) => { const r = rnd(Math.floor(tt * 1000) + seed), pool = st.filter(s => Math.abs(s.t - tt) > 4); if (!pool.length) return;
      const n = 1 + Math.floor(r() * 3), slots = [[0, 0], [1, 0], [0, 1], [1, 1], [.5, .5]].sort(() => r() - .5), ps = [];
      for (let k = 0; k < n; k++) { const wv = .36 + r() * .2, hv = wv * (0.7 + r() * .25), [sx, sy] = slots[k];
        ps.push({ src: pool[Math.floor(r() * pool.length)].src, x: sx * (1 - wv) + (r() - .5) * .08, y: sy * (1 - hv) + (r() - .5) * .08, w: wv, h: hv, t0: tt + k * 0.08 }); }
      EV.push({ t: tt, dur: 0.75 + r() * 0.5, ps }); };
    U.cortes.forEach((c, i) => { if (i % 2 === 0) ev(c + 0.05, 11); });
    let last = -9; U.chaves.forEach(s => { if (s - last > 3) { ev(s + 0.15, 29); last = s; } });
    for (const e of EV) for (const p of e.ps) if (!imgs.has(p.src)) { const im = new Image(); im.src = p.src; imgs.set(p.src, im); try { await im.decode(); } catch {} }
  }, draw(g, t, D, P, U) {
  const { W, BAND: B } = U;
  const e = EV.find(e => t >= e.t && t < e.t + e.dur); if (!e) return; U.clip(g);
  for (const p of e.ps) { const dt = t - p.t0, im = imgs.get(p.src); if (dt < 0 || !im || !im.complete) continue;
    const x = p.x * W, y = B.y + p.y * B.h, w = p.w * W, h = p.h * B.h, z = 1.06 + 0.06 * Math.min(1, dt / e.dur);
    g.save(); g.shadowColor = 'rgba(0,0,0,.55)'; g.shadowBlur = 30; g.shadowOffsetY = 10; g.fillStyle = '#000'; g.fillRect(x, y, w, h); g.restore();
    g.save(); g.beginPath(); g.rect(x, y, w, h); g.clip(); const iw = w * z, ih = iw * im.height / im.width;
    g.drawImage(im, x + (w - iw) / 2, y + (h - ih) / 2, iw, ih); if (dt < 1 / 30) { g.fillStyle = 'rgba(255,255,255,.55)'; g.fillRect(x, y, w, h); } g.restore(); }
} }); })();
