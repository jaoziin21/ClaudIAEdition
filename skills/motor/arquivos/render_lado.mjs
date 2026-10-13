import os from 'os';
// Legenda AO LADO de quem fala (estilo Lucas 11) + efeitos Super 8 no overlay (scene_lado.html).
// usage: node render_lado.mjs <projeto_dir> <faixa.mp4 (1080xBANDH, já tratada)> <audio> <out.mp4> <dur> [check t1,t2]
// projeto_dir/words.json  [{w,s,e}]
// projeto_dir/lado.json   {referencia, cor, keywords:[...], tamanho, cenas:[{t, x, y, align?, maxw?} | {t, nada:true}], burns:[t]}
//   cena com "separa": true → palavra falada logo depois do corte aparece na cena nova (não é puxada para a frase anterior)
//   cena com "look": "gotica" (só no estilo mistury) → força o visual do cartaz daquela cena
//   cada cena vale de t até a próxima; x,y = centro do bloco (0..1 na faixa); a legenda nunca atravessa um corte.
// MISTURAS (catálogo em estilos/ e efeitos/):
//   "efeitos": ["vhs", {"nome":"particulas","forca":0.6}, ...] → partes de TELA desenhadas atrás/na frente da legenda
//     (as partes de IMAGEM entram na faixa pelo faixa.mjs); "efeitosDaLegenda": false = faixa sem o filtro da legenda.
//   cena com "estilo": "red-sharp" → DUAS (ou mais) LEGENDAS no mesmo vídeo: as frases daquela cena usam outro estilo.
import { chromium } from 'playwright';
import { spawn, execFileSync } from 'child_process';
import { pathToFileURL } from 'url';
import fs from 'fs'; import path from 'path';
const [,, dir, band, audio, out, durS, mode, times] = process.argv, FPS = 30, DUR = +durS;
const BW = 1080, BH = +(process.env.BANDH || 760), BY = Math.round((1920 - BH) / 2);
const words = JSON.parse(fs.readFileSync(path.join(dir, 'words.json'), 'utf8'));
const cfg0 = JSON.parse(fs.readFileSync(path.join(dir, 'lado.json'), 'utf8'));
// "estilo": nome de um preset em estilos/ (catálogo de legendas; o lado.json do projeto tem prioridade)
const carrega = est => est ? { ...JSON.parse(fs.readFileSync(path.join('estilos', est + '.json'), 'utf8')), ...cfg0, estilo: est } : cfg0;
const cfg = carrega(cfg0.estilo);
const CAT = JSON.parse(fs.readFileSync('efeitos/efeitos.json', 'utf8'));
// "pacote": "filme-antigo" → mistura pronta de efeitos (efeitos/pacotes.json), somada aos "efeitos" avulsos
const PAC = JSON.parse(fs.readFileSync('efeitos/pacotes.json', 'utf8'));
const pacotes = [cfg0.pacote || []].flat(); for (const p of pacotes) if (!PAC[p]) { console.error(`pacote desconhecido: ${p}`); process.exit(1); }
const EFS = [...pacotes.flatMap(p => PAC[p].efeitos), ...(cfg0.efeitos || [])].map(e => typeof e === 'string' ? { nome: e } : e).filter((e, i, a) => a.findIndex(x => x.nome === e.nome) === i);
for (const e of EFS) if (!CAT[e.nome]) { console.error(`efeito desconhecido: ${e.nome}`); process.exit(1); }
const TELA = EFS.filter(e => CAT[e.nome].tela);
const colagemN = Math.max(0, ...EFS.map(e => CAT[e.nome].colagem || 0));
const estiloCena = c => (c && c.estilo) || cfg0.estilo || null;
// tira pontos perdidos (. , ; : … aspas) mas MANTÉM ? e ! (pergunta/exclamação)
const clean = w => w.replace(/(?<!\d)[.,;:…“”"]|[.,;:…“”"](?!\d)/g, '');
const base = w => w.replace(/[?!]+$/, '');
const len = ws => ws.reduce((a, w) => a + clean(w.w).length + 1, 0);
// "quebras": ["de tal maneira", ...] = trechos que FECHAM um bloco (quebra forçada; o bloco pode ter até MAXCH+4)
const nrm = w => base(clean(w)).toLowerCase(), BRK = new Set();
for (const q of cfg.quebras || []) { const t = q.split(/\s+/).map(nrm);
  words.forEach((_, i) => { if (i >= t.length - 1 && t.every((x, k) => nrm(words[i - t.length + 1 + k].w) === x)) BRK.add(i); }); }
const cenas = cfg0.cenas.slice().sort((a, b) => a.t - b.t);
const cenaDe = t => cenas.filter(c => c.t <= t + 1e-6).at(-1);
const cortes = cenas.map(c => c.t).filter(t => t > 0);
// blocos: frase (até . ! ? :), nunca atravessando corte de cena; frase longa vira partes equilibradas
const DANGLE = new Set('a o as os um uma e de do da dos das em no na por para pra com que se me te lhe à ao não mas pois é meu teu seu sua quem nos'.split(' '));
const phr = []; let cur = [];
const fimFrase = w => /[.!?:…”][\"”]?$/.test(w.w);
words.forEach((w, i) => {
  if (cur.length && cenaDe(w.s) !== cenaDe(cur[0].s)) { cur.porCorte = true; phr.push(cur); cur = []; }
  cur.push(w); if (i === words.length - 1 || fimFrase(w) || BRK.has(i)) { cur.forca = BRK.has(i); phr.push(cur); cur = []; }
});
// pedacinho de 1–2 palavras de uma frase cortada pela cena vai junto com o resto da frase
for (let i = 0; i < phr.length - 1; i++) {
  const a = phr[i], b = phr[i + 1]; if (!a.porCorte || cenaDe(b[0].s).separa) continue;   // cena com "separa": o pedaço falado depois do corte fica na cena nova
  if (a.length <= 2 && i > 0 && !fimFrase(phr[i - 1].at(-1))) { phr[i - 1].push(...a); phr.splice(i, 1); i--; continue; }
  if (a.length <= 2) { b.unshift(...a); phr.splice(i, 1); i--; continue; }
  const k = b.findIndex(fimFrase), frag = k < 0 ? b.length : k + 1;
  if (frag <= 2) { a.push(...b.splice(0, frag)); if (!b.length) phr.splice(i + 1, 1); }
}
// dados de UMA legenda (estilo): blocos só das cenas que usam esse estilo
function dados(cfg) {
const SIZE = cfg.tamanho || 46, MAXCH = cfg.maxch || 44;
const split = ws => {
  if (len(ws) <= MAXCH + (ws.forca ? 4 : 0) || ws.length < 2) return [ws];
  const n = Math.ceil(len(ws) / MAXCH); let best = 1e9, cut = 1;
  for (let i = 1; i < ws.length; i++) { const a = len(ws.slice(0, i));
    const c = Math.abs(a - len(ws) / n) + (DANGLE.has(clean(ws[i - 1].w).toLowerCase()) ? 40 : 0) + (/,$/.test(ws[i - 1].w) ? -10 : 0) + (a > MAXCH ? 50 : 0);
    if (c < best) { best = c; cut = i; } }
  return [ws.slice(0, cut), ...split(ws.slice(cut))];
};
let groups = phr.flatMap(split);
// junta pedacinhos curtos seguidos na mesma cena (ex.: "Amém" "Amém")
groups = groups.reduce((acc, g) => { const l = acc.at(-1);
  if (l && !l.forca && cenaDe(l[0].s) === cenaDe(g[0].s) && len(l) + len(g) <= MAXCH && Math.min(len(l), len(g)) <= 12 && g[0].s - l.at(-1).e < 0.9) { l.push(...g); l.forca = g.forca; } else acc.push(g); return acc; }, []);
// minúsculas, menos nomes próprios; palavras-chave (máx. 2 por bloco)
// "nomes" no lado.json acrescenta nomes próprios deste vídeo (ex.: Filho, Evangelho)
const PROPER = new Map(['deus', 'jesus', 'senhor', 'pai', 'cristo', 'espírito', 'salmos', 'bíblia', ...(cfg.nomes || []).map(x => x.toLowerCase())].map(x => [x, x[0].toUpperCase() + x.slice(1)]));
const KW = (cfg.keywords || []).map(k => clean(k).toLowerCase());
const CORES = { vermelho: ['#FF4A4A', '#D11A1A'], amarelo: ['#FFE07A', '#E0A21B'], brasa: ['#FF5A1F', '#E0400A'], ciano: ['#3CF0FF', '#12B8D0'], ouro: ['#FFD27A', '#F2A33A'] };
const blocks = groups.map((ws, i) => {
  const c = (m => cenaDe(m))(ws[Math.floor((ws.length - 1) / 2)].s), nx = groups[i + 1];
  // fim da última palavra às vezes vem esticado do alinhamento: o corte manda (a legenda não invade a cena seguinte)
  const nextCut = Math.max(cortes.find(t => t > ws[0].s) ?? DUR, ws.at(-1).s + 0.35);
  const end = Math.min(nx ? nx[0].s - 0.02 : DUR, ws.at(-1).e + 2.0, nextCut - 0.03, DUR);
  const ww = ws.map(w => { const l = clean(w.w).toLowerCase(), b = base(l); return { w: (PROPER.get(b) || b) + l.slice(b.length), s: w.s, e: w.e }; }).filter(w => w.w);
  ww.map((w, j) => [j, KW.indexOf(base(w.w).toLowerCase())]).filter(([, r]) => r >= 0).sort((a, b) => a[1] - b[1]).slice(0, 2).forEach(([j]) => ww[j].k = 1);
  // quebra em linhas curtas (bloco lateral): ~maxw da largura
  const maxLine = Math.max(14, Math.round((cfg.telaCheia ? (cfg.maxwFora || 0.86) : Math.max(c.maxw || 0.44, 0.26)) * BW / (SIZE * (cfg.charW || 0.47))));
  const lines = []; let ln = [];
  for (const w of ww) { if (ln.length && (len(ln) + w.w.length > maxLine)) { lines.push(ln); ln = []; } ln.push(w); }
  if (ln.length) lines.push(ln);
  // não deixar conector sozinho no fim da linha
  for (let k = 0; k < lines.length - 1; k++) { const l = lines[k]; while (l.length > 1 && DANGLE.has(l.at(-1).w)) lines[k + 1].unshift(l.pop()); }
  // linha que ficou só com um conector desce para a próxima
  for (let k = lines.length - 2; k >= 0; k--) if (lines[k].length === 1 && DANGLE.has(base(lines[k][0].w))) { lines[k + 1].unshift(lines[k][0]); lines.splice(k, 1); }
  // última linha com 1 palavra curta sobe para a anterior
  if (lines.length > 1 && lines.at(-1).length === 1 && lines.at(-1)[0].w.length <= 4) lines.at(-2).push(...lines.pop());
  return { start: ws[0].s - 0.05, end, x: c.x, y: c.y, esc: c.escala || 1, align: c.align || 'center', maxw: c.maxw, look: c.look, lines, nada: !!c.nada };
}).filter(b => !b.nada && (estiloCena(cenaDe(b.start + 0.05)) || null) === (cfg.estilo || null));
// "medeFundo": true (estilo mistury) → mede a cor média da imagem atrás de cada frase (0..1) para escolher cores que contrastem
if (cfg.medeFundo) for (const b of blocks) {
  const cw = Math.round(BW * 0.5), ch = Math.round(BH * 0.45);
  const cx = Math.round(Math.min(Math.max(b.x * BW - cw / 2, 0), BW - cw)), cy = Math.round(Math.min(Math.max(b.y * BH - ch / 2, 0), BH - ch));
  try { const px = execFileSync('ffmpeg', ['-v', 'error', '-ss', ((b.start + b.end) / 2).toFixed(2), '-i', band, '-frames:v', '1',
      '-vf', `scale=${BW}:${BH},crop=${cw}:${ch}:${cx}:${cy},scale=1:1:flags=area`, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']);
    b.fundo = [px[0] / 255, px[1] / 255, px[2] / 255].map(v => +v.toFixed(3)); } catch { b.fundo = null; }
}
// "colagem": N (estilo street) → tira N quadros parados espalhados pela faixa para os painéis de colagem
const stills = [];
const NCOL = Math.max(cfg.colagem || 0, colagemN);
if (NCOL) { fs.mkdirSync('colagem', { recursive: true });
  for (let i = 0; i < NCOL; i++) { const t = (DUR * (i + 0.5) / NCOL).toFixed(2), f = `colagem/c_${String(i).padStart(2, '0')}.jpg`;
    try { execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', t, '-i', band, '-frames:v', '1', '-vf', `scale=${BW}:${BH}`, '-q:v', '3', f]); stills.push({ src: f, t: +t }); } catch {} } }
// "quadros": true (estilo invisible) → tira TODOS os quadros da faixa em meia resolução (quadros/f_00001.jpg…) para a cena
// preencher a letra com a própria imagem do vídeo. Reaproveita se a faixa não mudou.
let quadros = null;
if (cfg.quadros) {
  const st = fs.statSync(band), id = `${path.resolve(band)}|${st.size}|${st.mtimeMs}`, info = 'quadros/info.txt';
  if (!fs.existsSync(info) || fs.readFileSync(info, 'utf8') !== id) {
    fs.rmSync('quadros', { recursive: true, force: true }); fs.mkdirSync('quadros');
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', band, '-vf', `fps=${FPS},scale=${BW / 2}:${BH / 2}`, '-q:v', '4', 'quadros/f_%05d.jpg']);
    fs.writeFileSync(info, id);
  }
  quadros = { n: fs.readdirSync('quadros').filter(f => f.endsWith('.jpg')).length, fps: FPS };
}
const FULL = !!cfg.telaCheia;   // overlay do quadro inteiro (legenda fora da imagem, no preto)
const LADO = ({ size: SIZE, kc: CORES[cfg.cor || 'vermelho'], cuts: cortes, burns: cfg.burns || [], blocks, band: { y: BY, h: BH }, fonte: cfg.fonte || null, brilho: !!cfg.brilho, looks: cfg.looks || null, gritos: (cfg.gritos || []).map(k => clean(k).toLowerCase()), stills, quadros, efeitos: TELA, semEfeitos: cfg0.efeitosDaLegenda === false, multilinha: !!cfg.multilinha });
blocks.forEach(b => console.log(`${cfg.estilo || ''} ${b.start.toFixed(2)}-${b.end.toFixed(2)} [${b.x},${b.y}]${b.fundo ? ' fundo ' + b.fundo : ''} ${b.lines.map(l => l.map(w => w.k ? '*' + w.w + '*' : w.w).join(' ')).join(' / ')}`));
return { cfg, LADO };
}
const ESTILOS = [...new Set([estiloCena(cenas[0]), ...cenas.map(estiloCena)])];
const DADOS = ESTILOS.map(e => dados(carrega(e)));
DADOS.forEach(({ cfg: c, LADO }, i) => {
  const nome = `lado_data_${i}.js`; fs.writeFileSync(nome, 'const LADO=' + JSON.stringify(LADO) + ';');
  if (i === 0) fs.writeFileSync('lado_data.js', 'const LADO=' + JSON.stringify(LADO) + ';');
  const html = fs.readFileSync(c.cena || process.env.SCENE || 'scene_lado.html', 'utf8').replace('src="lado_data.js"', `src="${nome}"`);
  fs.writeFileSync(`_cena_${i}.html`, html);
});
const FULL = !!cfg.telaCheia;   // overlay do quadro inteiro (legenda fora da imagem, no preto) — vale o estilo principal
const CORES = { vermelho: ['#FF4A4A', '#D11A1A'], amarelo: ['#FFE07A', '#E0A21B'], brasa: ['#FF5A1F', '#E0400A'], ciano: ['#3CF0FF', '#12B8D0'], ouro: ['#FFD27A', '#F2A33A'] };
const donoDe = t => Math.max(0, ESTILOS.indexOf(estiloCena(cenaDe(t))));

const opt = { args: ['--allow-file-access-from-files', '--font-render-hinting=none'] };
if (fs.existsSync('/opt/pw-browsers')) { const d = fs.readdirSync('/opt/pw-browsers').filter(x => /^chromium-\d+$/.test(x)).sort().pop(); if (d) opt.executablePath = `/opt/pw-browsers/${d}/chrome-linux/chrome`; }
const browser = await chromium.launch(opt);
// referência fixa no topo (ex.: "Mateus 6:9-13")
const REF = cfg.referencia || '', REFH = 150, REFY = Math.max(0, BY - REFH - 10);
if (REF) {
  const rp = await browser.newPage({ viewport: { width: BW, height: REFH } });
  const fut = cfg.estiloRef === 'futuro';
  const fontUrl = pathToFileURL(path.resolve(fut ? 'node_modules/@fontsource/chakra-petch/files/chakra-petch-latin-600-normal.woff2' : 'node_modules/@fontsource/playfair-display/files/playfair-display-latin-500-normal.woff2')).href;
  const css = fut
    ? `font:600 34px RF;letter-spacing:.32em;text-transform:uppercase;color:#E9EEF2;filter:drop-shadow(0 2px 6px rgba(0,0,0,.8))`
    : `font:500 50px RF;letter-spacing:.06em;color:transparent;-webkit-background-clip:text;background-clip:text;background-image:linear-gradient(180deg,#fff,#d9d4cc);filter:drop-shadow(0 2px 6px rgba(0,0,0,.8))`;
  const deco = fut ? `<b style="display:inline-block;width:46px;height:3px;background:${(CORES[cfg.cor] || CORES.vermelho)[0]};margin:0 26px;vertical-align:middle"></b>` : '';
  // "refNumeros": "cheios" → números na altura das maiúsculas (o Playfair usa números "antigos": o 1 fica pequeno). 
  const nums = cfg.refNumeros === 'cheios' ? ';font-variant-numeric:lining-nums' : '';
  fs.writeFileSync('ref_label.html', `<html><head><style>@font-face{font-family:RF;src:url("${fontUrl}")}
    html,body{margin:0;background:transparent}div{height:${REFH}px;display:flex;align-items:center;justify-content:center;${css}${nums}}</style></head><body><div>${deco}${REF}${deco}</div></body></html>`);
  await rp.goto(pathToFileURL(path.resolve('ref_label.html')).href);
  await rp.evaluate(() => document.fonts.ready); await rp.waitForTimeout(400);
  await rp.screenshot({ path: 'ref_label.png', omitBackground: true }); await rp.close();
}
// uma página por legenda (estilo); efeitos de tela injetados depois da cena carregar
const abre = async i => {
  const pg = await browser.newPage({ viewport: { width: BW, height: FULL ? 1920 : BH }, deviceScaleFactor: 1 });
  await pg.goto(pathToFileURL(path.resolve(`_cena_${i}.html`)).href);
  const ok = await pg.evaluate(() => window.fontsOK()); if (ok !== 'ok') { console.error(ok); process.exit(2); }
  if (TELA.length) { await pg.addScriptTag({ path: 'efeitos/_motor.js' });
    for (const f of [...new Set(TELA.map(e => CAT[e.nome].tela))]) await pg.addScriptTag({ path: path.join('efeitos/tela', f) });
    await pg.evaluate(() => window.EFX.liga()); }
  return pg; };
const grupo = async () => { const g = []; for (let i = 0; i < DADOS.length; i++) g.push(await abre(i)); return g; };
const page = await grupo();
if (TELA.length) console.log('efeitos de tela:', TELA.map(e => e.nome).join(' + '));
if (DADOS.length > 1) console.log('legendas:', ESTILOS.join(' + '));
const REFIN = REF ? ['-i', 'ref_label.png'] : [];
const refov = idx => REF ? `[o0][${idx}:v]overlay=0:${REFY}` : '[o0]null';
if (mode === 'check') {
  for (const t of times.split(',')) {
    const pg = page[donoDe(+t)]; await pg.evaluate(x => render(x), +t); await pg.screenshot({ path: 'ov.png', omitBackground: true });
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', t, '-i', band, '-i', 'ov.png', ...REFIN, '-filter_complex', FULL ? `[0:v]scale=${BW}:${BH},pad=1080:1920:0:${BY}:black[b];[b][1:v]overlay[o0];${refov(2)}` : `[0:v]scale=${BW}:${BH}[b];[b][1:v]overlay,pad=1080:1920:0:${BY}:black[o0];${refov(2)}`, '-frames:v', '1', `${out}_${t}.png`]);
  }
  fs.unlinkSync('ov.png');
} else {
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-i', band, '-f', 'image2pipe', '-c:v', 'png', '-r', String(FPS), '-i', '-', '-i', audio, ...REFIN,
    '-filter_complex', (FULL ? `[0:v]fps=${FPS},trim=0:${DUR},setpts=PTS-STARTPTS,scale=${BW}:${BH},pad=1080:1920:0:${BY}:black[b];[b][1:v]overlay=shortest=1[o0];${refov(3)},format=yuv420p[o]` : `[0:v]fps=${FPS},trim=0:${DUR},setpts=PTS-STARTPTS,scale=${BW}:${BH}[b];[b][1:v]overlay=shortest=1,pad=1080:1920:0:${BY}:black[o0];${refov(3)},format=yuv420p[o]`),
    '-map', '[o]', '-map', '2:a', '-af', 'apad', '-t', String(DUR),
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-maxrate', '8M', '-bufsize', '12M', '-r', String(FPS), '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  // vários quadros em paralelo (uma aba do Chromium por núcleo; a cena é determinística por tempo) → bem mais rápido
  const JOBS = +(process.env.JOBS || Math.max(1, os.cpus().length - 1)), NF = Math.round(DUR * FPS);
  const pages = [page];
  for (let k = 1; k < JOBS; k++) pages.push(await grupo());
  const chain = pages.map(() => Promise.resolve()), job = [];
  const pede = f => { if (f >= NF || job[f]) return; const k = f % JOBS;
    job[f] = chain[k] = chain[k].then(async () => { const pg = pages[k][donoDe(f / FPS)]; await pg.evaluate(x => render(x), f / FPS); return pg.screenshot({ type: 'png', omitBackground: true }); }); };
  const t0 = Date.now();
  for (let f = 0; f < NF; f++) {
    for (let a = f; a < f + JOBS * 2; a++) pede(a);
    const buf = await job[f]; job[f] = true;
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log(`PRONTO ${out} em ${((Date.now() - t0) / 60000).toFixed(1)} min`);
}
await browser.close();
