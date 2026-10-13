// Flash: clarão branco de 3 quadros em cada corte de cena (e, se "chaves": true, em cada palavra-chave).
EFX.add('flash', { camada: 'cima', draw(g, t, D, P, U) {
  const { W, BAND: B } = U, f = Math.round(t * 30), tempos = [...U.cortes, ...(P.chaves ? U.chaves : [])];
  let a = 0; for (const c of tempos) { const k = f - Math.round(c * 30); if (k >= 0 && k < 3) a = Math.max(a, [0.75, 0.4, 0.15][k]); }
  if (!a) return; g.fillStyle = `rgba(255,252,245,${(a * (P.forca ?? 1)).toFixed(3)})`; g.fillRect(0, B.y, W, B.h);
} });
