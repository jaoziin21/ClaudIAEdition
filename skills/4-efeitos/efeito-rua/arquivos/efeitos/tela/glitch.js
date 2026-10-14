// Glitch: nos cortes (um sim, um não) — 2 quadros de risco verde + blocos deslocados com separação RGB; em palavra-chave, 1 quadro de faixa ciano/magenta.
EFX.add('glitch', { camada: 'cima', draw(g, t, D, P, U) {
  const { W, BAND: B, rnd } = U, f = Math.round(t * 30);
  const fazer = (seed, forte) => { const r = rnd(seed);
    const y = B.y + B.h * (0.25 + r() * 0.45), x = W * (0.12 + r() * 0.3), w = W * (0.35 + r() * 0.3);
    g.fillStyle = 'rgba(80,255,110,.85)'; g.fillRect(x, y, w, 5); g.fillStyle = 'rgba(80,255,110,.25)'; g.fillRect(x - 20, y - 4, w + 40, 13);
    for (let i = 0; i < (forte ? 7 : 3); i++) { const by = B.y + r() * B.h, bh = 6 + r() * 26, bx = r() * W * 0.6, bw = W * (0.15 + r() * 0.4);
      g.fillStyle = `rgba(255,0,90,${0.18 + r() * 0.2})`; g.fillRect(bx + 8, by, bw, bh); g.fillStyle = `rgba(0,230,255,${0.18 + r() * 0.2})`; g.fillRect(bx - 8, by, bw, bh); } };
  U.clip(g);
  U.cortes.forEach((c, i) => { if (i % 2) return; const k = f - Math.round(c * 30); if (k >= 0 && k < 2) fazer(Math.floor(c * 1000) + 5 + k, true); });
  if (P.chaves !== false) U.chaves.forEach(s => { if (f === Math.round(s * 30)) fazer(Math.floor(s * 1000) + 11, false); });
} });
