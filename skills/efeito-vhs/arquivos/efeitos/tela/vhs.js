// VHS: linhas de varredura leves + faixa de "tracking" ruidosa que sobe pela imagem em cada corte. (Tirado do Rocks.)
EFX.add('vhs', { camada: 'cima', draw(g, t, D, P, U) {
  const { W, BAND: B, rnd } = U; U.clip(g);
  g.fillStyle = `rgba(0,0,0,${0.10 * (P.forca ?? 1)})`; for (let y = B.y; y < B.y + B.h; y += 4) g.fillRect(0, y, W, 1.4);
  for (const c of U.cortes) { const k = (t - c + 0.05) / 0.35; if (k < 0 || k > 1) continue;
    const y = B.y + B.h * (1.1 - k * 1.3), h = 26 + 30 * Math.sin(Math.PI * k), r = rnd(Math.floor(t * 30) * 13 + 7);
    for (let i = 0; i < 70; i++) { g.fillStyle = `rgba(255,255,255,${(0.15 + r() * 0.45).toFixed(2)})`; g.fillRect(r() * W, y + r() * h, 20 + r() * 140, 1 + r() * 2); }
    g.fillStyle = 'rgba(255,255,255,.08)'; g.fillRect(0, y, W, h); }
} });
