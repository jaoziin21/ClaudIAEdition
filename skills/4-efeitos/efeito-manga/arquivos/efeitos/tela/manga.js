// Linhas de impacto de mangá: quando entra uma palavra-chave, traços finos convergem para o centro e somem em 0,6 s. (Tirado do 3D invisível.)
EFX.add('manga', { camada: 'baixo', draw(g, t, D, P, U) {
  const { W, BAND: B } = U, k = U.chaves.find(s => t >= s && t < s + 0.6); if (k === undefined) return;
  const p = (t - k) / 0.6, a = Math.sin(Math.PI * Math.min(1, p * 1.6)) * (1 - p) * (P.forca ?? 1);
  let x0 = Math.floor(k * 1000); const r = () => (x0 = (x0 * 16807) % 2147483647) / 2147483647;
  const cx = W / 2, cy = B.y + B.h / 2, R = Math.hypot(W, B.h) * 0.6; U.clip(g);
  for (let i = 0; i < 70; i++) { const ang = r() * Math.PI * 2, r0 = R * (0.55 + r() * 0.25 - p * 0.12);
    g.strokeStyle = `rgba(15,18,24,${(0.55 * a).toFixed(3)})`; g.lineWidth = 1 + r() * 2.5;
    g.beginPath(); g.moveTo(cx + Math.cos(ang) * r0, cy + Math.sin(ang) * r0); g.lineTo(cx + Math.cos(ang) * R * 1.2, cy + Math.sin(ang) * R * 1.2); g.stroke(); }
} });
