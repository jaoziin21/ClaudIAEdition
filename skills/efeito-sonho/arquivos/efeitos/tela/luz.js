// Vazamentos de luz: dois clarões suaves (quente e frio) que passeiam devagar + clarão lateral em cada corte. (Tirado do Sample Yellow.)
EFX.add('luz', { camada: 'baixo', draw(g, t, D, P, U) {
  const { W, BAND: B, rnd } = U, k0 = P.forca ?? 1; U.clip(g); g.globalCompositeOperation = 'screen';
  for (const [ph, cor, a] of [[0, '255,190,120', 0.16], [2.1, '140,220,255', 0.10]]) {
    const cx = W * (0.5 + 0.55 * Math.sin(t * 0.13 + ph)), cy = B.y + B.h * (0.35 + 0.3 * Math.cos(t * 0.09 + ph)), gr = g.createRadialGradient(cx, cy, 0, cx, cy, W * 0.6);
    gr.addColorStop(0, `rgba(${cor},${a * k0})`); gr.addColorStop(1, `rgba(${cor},0)`); g.fillStyle = gr; g.fillRect(0, B.y, W, B.h); }
  for (const c of U.cortes) { const k = (t - c + 0.08) / 0.5; if (k < 0 || k > 1) continue;
    const r = rnd(Math.floor(c * 100)), side = r() < .5 ? 0 : W, a = 0.45 * Math.sin(Math.PI * k) * k0, gr = g.createLinearGradient(side, 0, W - side, 0);
    gr.addColorStop(0, `rgba(255,236,200,${a})`); gr.addColorStop(0.6, `rgba(255,200,150,${a * 0.3})`); gr.addColorStop(1, 'rgba(255,200,150,0)'); g.fillStyle = gr; g.fillRect(0, B.y, W, B.h); }
} });
