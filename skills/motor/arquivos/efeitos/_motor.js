// Motor dos EFEITOS DE TELA: injetado pelo render_lado.mjs em qualquer cena de legenda (depois de carregar a cena).
// Cria 2 canvas — "baixo" (atrás da legenda) e "cima" (na frente) — e embrulha window.render: a cada quadro a legenda
// é desenhada e depois cada efeito da lista desenha no seu canvas. Os efeitos se registram com EFX.add(nome, {camada, draw}).
// draw(g, t, D, P, U): g = contexto 2D do canvas, t = tempo (s), D = LADO (dados da legenda: blocks, cuts, band...),
// P = parâmetros do efeito no lado.json ({"nome":"particulas","forca":0.6}), U = utilidades (rnd, banda, chaves, clip).
(() => {
  const D = typeof LADO !== "undefined" ? LADO : window.LADO, W = innerWidth, H = innerHeight;   // LADO é "const" global (não fica em window)
  const BAND = (H >= 1900 && D.band) ? D.band : { y: 0, h: H };
  const mk = (z, primeiro) => { const c = document.createElement('canvas'); c.width = W; c.height = H;
    c.style.cssText = `position:absolute;left:0;top:0;width:${W}px;height:${H}px;pointer-events:none;z-index:${z}`;
    if (primeiro) document.body.insertBefore(c, document.body.firstChild); else document.body.appendChild(c); return c.getContext('2d'); };
  const ctx = { baixo: mk(0, true), cima: mk(9999, false) };
  const rnd = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let x = Math.imul(seed ^ seed >>> 15, 1 | seed); x = x + Math.imul(x ^ x >>> 7, 61 | x) ^ x; return ((x ^ x >>> 14) >>> 0) / 4294967296; };
  // palavras-chave (tempo em que são faladas) e todas as palavras, de todos os blocos desta legenda
  const palavras = []; for (const b of D.blocks || []) for (const l of b.lines || []) for (const w of l) palavras.push(w);
  const U = { rnd, W, H, BAND, cortes: D.cuts || [], chaves: palavras.filter(w => w.k).map(w => w.s), palavras,
    clip: g => { g.beginPath(); g.rect(0, BAND.y, W, BAND.h); g.clip(); } };
  const lista = [];
  window.EFX = {
    add(nome, ef) { const cfg = (D.efeitos || []).find(e => e.nome === nome); if (cfg) lista.push({ ...ef, P: cfg, nome }); },
    async liga() {
      for (const ef of lista) if (ef.prepara) await ef.prepara(D, ef.P, U);   // ex.: colagem carrega as imagens antes do 1º quadro
      lista.sort((a, b) => (D.efeitos.findIndex(e => e.nome === a.nome)) - (D.efeitos.findIndex(e => e.nome === b.nome)));
      const r0 = window.render;
      window.render = async t => {
        await r0(t);
        ctx.baixo.clearRect(0, 0, W, H); ctx.cima.clearRect(0, 0, W, H);
        for (const ef of lista) { const g = ctx[ef.camada || 'baixo']; g.save(); ef.draw(g, t, D, ef.P, U); g.restore(); }
      };
      return lista.map(e => e.nome).join(',');
    }
  };
})();
