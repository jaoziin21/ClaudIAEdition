// Vinheta vermelha: as bordas da imagem pulsam em vermelho quando uma palavra-chave é falada. (Tirado do Red Sharp.)
EFX.add('vinheta-vermelha', { camada: 'baixo', draw(g, t, D, P, U) {
  const { W, BAND: B } = U; let p = 0; for (const s of U.chaves) p = Math.max(p, Math.exp(-Math.pow((t - s - 0.1) / 0.28, 2)));
  if (p < 0.02) return; U.clip(g);
  const gr = g.createRadialGradient(W / 2, B.y + B.h / 2, B.h * 0.25, W / 2, B.y + B.h / 2, W * 0.75);
  gr.addColorStop(0, 'rgba(160,0,0,0)'); gr.addColorStop(1, `rgba(170,0,0,${(0.5 * p * (P.forca ?? 1)).toFixed(3)})`); g.fillStyle = gr; g.fillRect(0, B.y, W, B.h);
} });
