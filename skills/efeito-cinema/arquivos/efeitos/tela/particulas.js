// Partículas: poeira de luz / bokeh quente flutuando devagar na frente da imagem (atrás da legenda). Novo.
EFX.add('particulas', { camada: 'baixo', draw(g, t, D, P, U) {
  const { W, BAND: B, rnd } = U, r = rnd(42), n = Math.round(46 * (P.forca ?? 1)), cor = P.cor || '255,226,170'; U.clip(g);
  g.globalCompositeOperation = 'screen';
  for (let i = 0; i < n; i++) {
    const x0 = r() * W, y0 = r() * B.h, vx = (r() - 0.5) * 14, vy = -(6 + r() * 18), z = r(), rad = 1.5 + z * z * 9, fase = r() * 6.28;
    const x = ((x0 + vx * t + Math.sin(t * 0.7 + fase) * 12) % W + W) % W, y = B.y + ((y0 + vy * t) % B.h + B.h) % B.h;
    const a = (0.12 + 0.35 * (1 - z)) * (0.6 + 0.4 * Math.sin(t * 1.3 + fase));
    const gr = g.createRadialGradient(x, y, 0, x, y, rad * 2.2); gr.addColorStop(0, `rgba(${cor},${a.toFixed(3)})`); gr.addColorStop(1, `rgba(${cor},0)`);
    g.fillStyle = gr; g.beginPath(); g.arc(x, y, rad * 2.2, 0, 7); g.fill(); }
} });
