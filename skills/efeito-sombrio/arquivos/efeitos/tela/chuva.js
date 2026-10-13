// Chuva: riscos finos inclinados caindo rápido (dramático), com leve escurecida. Novo.
EFX.add('chuva', { camada: 'baixo', draw(g, t, D, P, U) {
  const { W, BAND: B, rnd } = U, r = rnd(7), n = Math.round(160 * (P.forca ?? 1)); U.clip(g);
  g.fillStyle = 'rgba(10,14,22,.12)'; g.fillRect(0, B.y, W, B.h);
  g.strokeStyle = 'rgba(210,225,240,.28)'; g.lineWidth = 1.2; g.beginPath();
  for (let i = 0; i < n; i++) { const x0 = r() * W * 1.3, sp = 900 + r() * 700, L = 18 + r() * 34, ph = r() * B.h;
    const y = B.y + ((ph + sp * t) % (B.h + 60)) - 30, x = ((x0 - 0.28 * sp * t) % (W * 1.3) + W * 1.3) % (W * 1.3) - W * 0.15;
    g.moveTo(x, y); g.lineTo(x - L * 0.28, y + L); }
  g.stroke();
} });
