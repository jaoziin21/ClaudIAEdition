// Gera as capas (PNG) das pastas de skills: skills/capa.png e skills/<grupo>/capa.png
//   uso: node venda/ferramentas/capas.cjs        (rodar na raiz do repositório)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const S = path.resolve(__dirname, '../../skills');
const img = (rel) => 'data:image/jpeg;base64,' + fs.readFileSync(path.join(S, rel)).toString('base64');

const FONTES = `<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">`;
const CSS = `
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#f3f4f6;--ink:#0c0e13;--muted:#5b6070;--blue:#2b5cff;--blue-d:#1f47d6;--blue-soft:#e6ecff;--line:#e2e4ea;--stage:#0c0e13;--stage-2:#161922}
body{width:1600px;height:var(--h);background:var(--bg);font-family:Geist,sans-serif;color:var(--ink);overflow:hidden;position:relative}
.grade{position:absolute;inset:0;background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:48px 48px;opacity:.55;-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 45%,#000 100%)}
.brilho{position:absolute;right:-160px;top:-200px;width:900px;height:900px;border-radius:50%;background:radial-gradient(circle,rgba(43,92,255,.22),transparent 65%)}
.txt{position:absolute;left:96px;top:50%;transform:translateY(-50%);width:640px;z-index:2}
.rot{font-family:'Geist Mono',monospace;font-size:20px;letter-spacing:.14em;text-transform:uppercase;color:var(--blue);display:flex;align-items:center;gap:14px;margin-bottom:22px}
.rot b{display:inline-grid;place-items:center;width:40px;height:40px;border-radius:12px;background:var(--blue);color:#fff;font-weight:500;letter-spacing:0}
h1{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:var(--t);line-height:.92;letter-spacing:-.035em}
h1 em{font-style:normal;color:var(--blue)}
p{margin-top:24px;font-size:26px;line-height:1.35;color:var(--muted);max-width:600px}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}
.chip{font-family:'Geist Mono',monospace;font-size:19px;padding:9px 16px;border-radius:999px;background:#fff;border:1px solid var(--line);color:var(--ink)}
.chip.az{background:var(--blue);border-color:var(--blue);color:#fff}
.palco{position:absolute;right:0;top:0;bottom:0;width:900px;perspective:1600px;z-index:1}
.leque{position:absolute;inset:0;transform-style:preserve-3d;transform:rotateY(-18deg) rotateX(8deg)}
.card{position:absolute;border-radius:18px;overflow:hidden;background:#000;box-shadow:0 30px 60px -20px rgba(12,14,19,.45),0 0 0 1px rgba(255,255,255,.08)}
.card img{width:100%;height:100%;object-fit:cover;display:block}
.card span{position:absolute;left:12px;bottom:10px;font-family:'Geist Mono',monospace;font-size:15px;color:#fff;background:rgba(12,14,19,.72);padding:5px 10px;border-radius:8px}
.term{position:absolute;border-radius:22px;background:var(--stage);color:#eef0f5;font-family:'Geist Mono',monospace;box-shadow:0 40px 80px -25px rgba(12,14,19,.55);padding:30px 34px;font-size:21px;line-height:1.75}
.term .top{display:flex;gap:9px;margin-bottom:18px}.term .top i{width:13px;height:13px;border-radius:50%;background:#2a2e3a}
.term .ok{color:#18b26b}.term .az{color:#7d9cff}.term .mu{color:#9aa0b0}
.bolha{position:absolute;border-radius:22px;padding:20px 26px;font-size:24px;line-height:1.35;box-shadow:0 30px 60px -22px rgba(12,14,19,.4)}
.bolha.eu{background:var(--blue);color:#fff;border-bottom-right-radius:6px}
.bolha.ele{background:#fff;color:var(--ink);border:1px solid var(--line);border-bottom-left-radius:6px}
.bolha small{display:block;font-family:'Geist Mono',monospace;font-size:15px;opacity:.65;margin-bottom:6px}
`;

function pagina(h, t, rot, num, titulo, sub, chips, palco) {
  return `<!doctype html><html><head><meta charset="utf-8">${FONTES}<style>${CSS}</style></head>
<body style="--h:${h}px;--t:${t}px"><div class="grade"></div><div class="brilho"></div>
<div class="txt"><div class="rot">${num ? `<b>${num}</b>` : ''}${rot}</div><h1>${titulo}</h1><p>${sub}</p>
<div class="chips">${chips.map((c, i) => `<span class="chip${i === 0 ? ' az' : ''}">${c}</span>`).join('')}</div></div>
<div class="palco"><div class="leque">${palco}</div></div></body></html>`;
}

// cartas em leque: [arquivo, rótulo]
function leque(lista, w, h) {
  const n = lista.length, cols = Math.min(n, 3), linhas = Math.ceil(n / cols);
  const gx = 22, gy = 22, W = cols * w + (cols - 1) * gx, H = linhas * h + (linhas - 1) * gy;
  const x0 = 430 - W / 2, y0 = (ALTURA - H) / 2;
  return lista.map(([f, r], i) => {
    const c = i % cols, l = Math.floor(i / cols), resto = n - l * cols;
    const dx = resto < cols ? (cols - resto) * (w + gx) / 2 : 0;
    const z = 40 - Math.abs(c - (cols - 1) / 2) * 30 + (l % 2 ? 20 : 0);
    return `<div class="card" style="left:${x0 + dx + c * (w + gx)}px;top:${y0 + l * (h + gy)}px;width:${w}px;height:${h}px;transform:translateZ(${z}px)"><img src="${img(f)}"><span>/${r}</span></div>`;
  }).join('');
}

let ALTURA = 560;
const CAPAS = [
  { saida: 'capa.png', h: 640, t: 128, rot: 'Pacote de skills para Claude Code', num: '', titulo: 'Editor<br>no <em>Piloto</em>',
    sub: 'Roteiro, voz, legenda, edição, música, efeitos e post. Tudo em uma skill só.',
    chips: ['/comecar', '/roteiro', '/sample-yellow', '/efeito-vhs'],
    palco: () => leque([['3-legendas/sample-yellow/exemplo.jpg', 'sample-yellow'], ['4-efeitos/efeito-cinema/exemplo.jpg', 'efeito-cinema'],
      ['3-legendas/street/exemplo.jpg', 'street'], ['3-legendas/red-sharp/exemplo.jpg', 'red-sharp'], ['5-formatos-de-video/video-gif/exemplo.jpg', 'video-gif'],
      ['4-efeitos/efeito-filme-antigo/exemplo.jpg', 'efeito-filme-antigo'], ['3-legendas/rocks/exemplo.jpg', 'rocks'],
      ['3-legendas/mistury/exemplo.jpg', 'mistury'], ['4-efeitos/efeito-vhs/exemplo.jpg', 'efeito-vhs']], 236, 166) },
  { saida: '1-base/capa.png', num: '1', rot: 'Base', titulo: 'O <em>motor</em>', sub: 'A base que todas as outras skills usam. Vai junto sempre, sozinho.',
    chips: ['motor', 'setup.sh'],
    palco: () => `<div class="term" style="left:170px;top:90px;width:640px"><div class="top"><i></i><i></i><i></i></div>
<div><span class="az">$</span> bash motor/setup.sh</div><div><span class="ok">✓</span> Node.js, Python e ffmpeg</div><div><span class="ok">✓</span> 37 fontes instaladas</div>
<div><span class="ok">✓</span> transcrição (Whisper)</div><div><span class="ok">✓</span> legenda, fundo e música</div><div class="mu">pronto para editar.</div></div>` },
  { saida: '2-roteiro-voz-post/capa.png', num: '2', rot: 'Começo, roteiro, voz e post', titulo: 'Da <em>ideia</em><br>ao post', sub: 'Você conta a ideia. Ele escreve o roteiro, narra, acha o fundo e entrega o texto do post.',
    chips: ['/comecar', '/roteiro', '/voz', '/buscar-midia', '/post'],
    palco: () => `<div class="bolha eu" style="left:330px;top:70px;width:470px;transform:translateZ(40px)"><small>você</small>quero um canal de motivação com cenas de anime</div>
<div class="bolha ele" style="left:120px;top:205px;width:520px;transform:translateZ(10px)"><small>/roteiro</small>3 roteiros com 3 ganchos cada. Qual você quer?</div>
<div class="bolha ele" style="left:200px;top:330px;width:420px;transform:translateZ(30px)"><small>/voz</small>narração pronta ▶ 0:52</div>
<div class="bolha ele" style="left:300px;top:430px;width:500px;transform:translateZ(50px)"><small>/post</small>título, legenda, tags e horário</div>` },
  { saida: '3-legendas/capa.png', num: '3', rot: 'Legendas', titulo: '9 <em>legendas</em>', sub: 'Escolha o estilo, troque a fonte por qualquer outra e some os efeitos que quiser.',
    chips: ['/sample-yellow', '/street', '/rocks', '/fontes'],
    palco: () => ['sample-yellow', 'legenda-dinamica', 'legenda-3d-invisivel', 'mistury', 'street', 'rocks', 'samplerocks', 'invisible', 'red-sharp'].map(s => [`3-legendas/${s}/exemplo.jpg`, s]) },
  { saida: '4-efeitos/capa.png', num: '4', rot: 'Efeitos', titulo: '7 <em>efeitos</em>', sub: 'Somam com qualquer legenda. Dá para juntar vários no mesmo vídeo.',
    chips: ['/efeitos', '/efeito-vhs', '/efeito-cinema'],
    palco: () => ['cinema', 'filme-antigo', 'manga', 'rua', 'sombrio', 'sonho', 'vhs'].map(s => [`4-efeitos/efeito-${s}/exemplo.jpg`, 'efeito-' + s]) },
  { saida: '5-formatos-de-video/capa.png', num: '5', rot: 'Formatos de vídeo', titulo: '6 <em>formatos</em>', sub: 'GIF, narração, personagem falando, edit na batida, vídeo longo e aesthetic.',
    chips: ['/video-gif', '/video-narracao', '/edit-musica'],
    palco: () => ['video-gif', 'video-narracao', 'video-fala', 'edit-musica', 'video-longo'].map(s => [`5-formatos-de-video/${s}/exemplo.jpg`, s]) },
];

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ deviceScaleFactor: 1 });
  for (const c of CAPAS) {
    ALTURA = c.h || 560;
    let palco = c.palco();
    if (Array.isArray(palco)) palco = leque(palco, 220, 155);
    await p.setViewportSize({ width: 1600, height: ALTURA });
    await p.setContent(pagina(ALTURA, c.t || 104, c.rot, c.num, c.titulo, c.sub, c.chips, palco), { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(S, c.saida) });
    console.log('capa:', c.saida);
  }
  await b.close();
})();
