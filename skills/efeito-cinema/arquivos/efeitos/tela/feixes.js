// Feixes de luz: raios quentes diagonais que atravessam a imagem bem devagar + respiro de luz no alto. (Tirado do 3D invisível.)
EFX.add('feixes', { camada: 'baixo', draw(g, t, D, P, U) {
  const { W, BAND: B } = U, k0 = P.forca ?? 1; U.clip(g);
  const a0 = (0.10 + 0.04 * Math.sin(t * 0.5)) * k0, rg = g.createRadialGradient(W * 0.78, B.y - 40, 0, W * 0.78, B.y - 40, W * 0.95);
  rg.addColorStop(0, `rgba(255,214,160,${a0})`); rg.addColorStop(1, 'rgba(255,200,140,0)'); g.fillStyle = rg; g.fillRect(0, B.y, W, B.h);
  for (const [sp, off, wid, al] of [[0.035, 0.0, 120, 0.075], [0.022, 0.45, 200, 0.055], [0.05, 0.75, 70, 0.06]]) {
    const ph = ((t * sp + off) % 1.4) - 0.2, x = W * (1.15 - ph * 1.1);
    g.save(); g.translate(x, B.y + B.h / 2); g.rotate(-0.42); const lg = g.createLinearGradient(-wid, 0, wid, 0);
    lg.addColorStop(0, 'rgba(255,225,180,0)'); lg.addColorStop(0.5, `rgba(255,225,180,${al * k0})`); lg.addColorStop(1, 'rgba(255,225,180,0)');
    g.fillStyle = lg; g.fillRect(-wid, -B.h * 1.5, wid * 2, B.h * 3); g.restore(); }
} });
