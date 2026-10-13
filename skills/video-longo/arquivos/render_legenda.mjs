// Estilo Ref. 2: imagem horizontal (16:9) esticada na largura, preto em cima/embaixo; legenda numa linha,
// palavra aparece só quando é falada. Sem pontuação, sem cor de destaque.
// usage: node render_legenda.mjs <words.json> <faixa.mp4 1080x608> <audio> <out.mp4> <dur> [check t1,t2]
// YouTube horizontal: OUTW=1920 OUTH=1080 BANDH=1080 (tela cheia); LEGX/LEGY = centro do bloco (0..1); LEGW = largura máx. (0..1, quebra em
// linhas equilibradas); SIZE = tamanho da letra; ESCALA=2 desenha tudo em dobro (4K 3840x2160 nítido com o layout de 1920x1080).
// Vídeo longo em paralelo: FRAMES=ini:fim renderiza só esses quadros, sem áudio (audio = '-'); NODATA=1 não reescreve legenda_data.js
// (ver render_longo.sh, que divide em trechos, roda JOBS de uma vez e junta com o áudio).
import { chromium } from 'playwright';
import { spawn, execFileSync } from 'child_process';
import { pathToFileURL } from 'url';
import fs from 'fs'; import path from 'path';
const [,, wordsPath, band, audio, out, durS, mode, times] = process.argv, FPS = 30, DUR = +durS;
const OW = +(process.env.OUTW || 1080), OH = +(process.env.OUTH || 1920);
const BW = OW, BH = +(process.env.BANDH || 608), BY = Math.round((OH - BH) / 2), PX = +(process.env.ESCALA || 1);
// RECORTE=x,y,w,h (px do layout) → só fotografa a área da legenda (bem mais rápido em 4K); SEMFILME=1 tira poeira/riscos da cena
const CLIP = process.env.RECORTE ? (([x, y, width, height]) => ({ x, y, width, height }))(process.env.RECORTE.split(',').map(Number)) : null;
const SHOT = { omitBackground: true, ...(CLIP ? { clip: CLIP } : {}) }, OVXY = CLIP ? `=${CLIP.x * PX}:${CLIP.y * PX}` : '';
const MAXCH = +(process.env.MAXCH || 42), GAP = 0.35;
// tira pontos perdidos (. , ; : … aspas) mas MANTÉM ? e ! (pergunta/exclamação)
const clean = w => w.replace(/(?<!\d)[.,;:…“”"]|[.,;:…“”"](?!\d)/g, '');
const semPont = w => w.replace(/[?!]+$/, '');
const words = JSON.parse(fs.readFileSync(wordsPath, 'utf8'));
const len = ws => ws.reduce((a, w) => a + clean(w.w).length + 1, 0);
// palavras-chave (cor diferente): legenda.json ao lado do words.json → {"keywords":[...], "cor":"vermelho"|"amarelo"}
const cfgPath = path.join(path.dirname(wordsPath), 'legenda.json');
const cfg = fs.existsSync(cfgPath) ? JSON.parse(fs.readFileSync(cfgPath, 'utf8')) : {};
const norm = w => semPont(clean(w)).toLowerCase();
// "quebras": ["de tal maneira", ...] = trechos que FECHAM uma linha (quebra forçada; a linha pode ter até MAXCH+4)
const BRK = new Set();
for (const q of cfg.quebras || []) { const t = q.split(/\s+/).map(norm);
  words.forEach((_, i) => { if (i >= t.length - 1 && t.every((x, k) => norm(words[i - t.length + 1 + k].w) === x)) BRK.add(i); }); }
// frases LONGAS: quebra só em fim de frase (.!?…:) — vírgula e pausa não quebram;
// frase maior que MAXCH vira o mínimo de partes equilibradas, nunca terminando em conector
const DANGLE = new Set('a o as os um uma e de do da dos das em no na por para pra com que se me te lhe à ao não mas pois é meu teu seu sua quem'.split(' '));
const phr = []; let cur = [];
words.forEach((w, i) => { cur.push(w); if (i === words.length - 1 || BRK.has(i) || /[.!?:…”]["”]?$/.test(w.w)) { cur.forca = BRK.has(i); phr.push(cur); cur = []; } });
const split = ws => {
  if (len(ws) <= MAXCH + (ws.forca ? 4 : 0) || ws.length < 2) return [ws];
  const n = Math.ceil(len(ws) / MAXCH); let best = 1e9, cut = 1;
  for (let i = 1; i < ws.length; i++) {
    const a = len(ws.slice(0, i)), b = len(ws.slice(i));
    const c = Math.abs(a - len(ws) / n) + (DANGLE.has(clean(ws[i - 1].w).toLowerCase()) ? 40 : 0) + (/,$/.test(ws[i - 1].w) ? -10 : 0) + (a > MAXCH ? 50 : 0);
    if (c < best) { best = c; cut = i; } }
  const resto = ws.slice(cut); resto.forca = ws.forca;   // a última parte continua fechando a linha (quebras)
  return [ws.slice(0, cut), ...split(resto)];
};
// junta frases curtas seguidas (ex.: "então respire" "ore" "continue") se couber numa linha
const lines = [];
for (const p of phr.flatMap(split)) {
  const last = lines.at(-1);
  if (last && !last.forca && len(last) + len(p) <= MAXCH && Math.min(len(p), len(last)) <= 12 && p[0].s - last.at(-1).e < 0.9) { last.push(...p); last.forca = p.forca; } else lines.push(p);
}
// tudo minúsculo, menos nomes próprios
// "nomes" no legenda.json acrescenta nomes próprios deste vídeo (ex.: Filho, Evangelho)
const PROPER = new Map(['deus', 'isaías', 'jesus', 'senhor', 'bíblia', 'cristo', 'pai', 'espírito', 'salmo', 'salmos', ...(cfg.nomes || []).map(x => x.toLowerCase())].map(x => [x, x[0].toUpperCase() + x.slice(1)]));
const caseOf = w => { const l = w.toLowerCase(), b = semPont(l); return (PROPER.get(b) || b) + l.slice(b.length); };
const KW = (cfg.keywords || []).map(norm), MAXK = cfg.maxPorLinha ?? 2;
const CORES = { vermelho: ['#FF4A4A', '#D11A1A'], amarelo: ['#FFE07A', '#E0A21B'] };
const L = lines.map((ws, i) => {
  // vírgula onde a pausa é óbvia : no MEIO da linha, a pontuação do texto (. , ; : …) vira vírgula,
  // e antes de fala citada ("disse, venha…") também; no FIM da linha nada (só ? e !). "virgulas": false no legenda.json desliga.
  const VG = cfg.virgulas !== false, pausa = (w, nx) => /[.,;:…]["”]?$|["”][.,;:…]?$/.test(w) && !/[?!]["”]?$/.test(w) || /^["“]/.test(nx || '');
  const words = ws.map((w, j) => ({ w: caseOf(clean(w.w)) + (VG && j < ws.length - 1 && pausa(w.w, ws[j + 1].w) && !/[?!]$/.test(clean(w.w)) ? ',' : ''), s: w.s })).filter(w => w.w && w.w !== ',');
  words.map((w, j) => [j, KW.indexOf(norm(w.w))]).filter(([, r]) => r >= 0).sort((x, y) => x[1] - y[1]).slice(0, MAXK).forEach(([j]) => words[j].k = 1);
  return { start: ws[0].s - 0.02, end: i + 1 < lines.length ? lines[i + 1][0].s - 0.02 : Math.min(DUR, ws.at(-1).e + 1.4), words };
});
if (!process.env.NODATA) fs.writeFileSync('legenda_data.js', 'const LEG=' + JSON.stringify({ size: +(process.env.SIZE || cfg.tamanho || 48), kc: CORES[cfg.cor || 'vermelho'], x: +(process.env.LEGX || cfg.x || 0.5), y: +(process.env.LEGY || cfg.y || 0.5), w: +(process.env.LEGW || cfg.w || 0), lines: L }) + ';');
L.forEach(l => console.log(`${l.start.toFixed(2)}-${l.end.toFixed(2)} | ${l.words.map(w => w.k ? '*' + w.w + '*' : w.w).join(' ')}`));
if (mode === 'dados') process.exit(0);   // só monta as linhas (legenda_data.js) e sai

const opt = { args: ['--allow-file-access-from-files', '--font-render-hinting=none'] };
if (fs.existsSync('/opt/pw-browsers')) { const d = fs.readdirSync('/opt/pw-browsers').filter(x => /^chromium-\d+$/.test(x)).sort().pop(); if (d) opt.executablePath = `/opt/pw-browsers/${d}/chrome-linux/chrome`; }
const browser = await chromium.launch(opt);
const page = await browser.newPage({ viewport: { width: BW, height: BH }, deviceScaleFactor: PX });
// referência fixa (legenda.json "referencia") no centro, logo acima da imagem
const REF = cfg.referencia || '', REFH = 150, REFY = Math.max(0, BY - REFH - 10);
if (REF) {
  const rp = await browser.newPage({ viewport: { width: BW, height: REFH }, deviceScaleFactor: PX });
  await rp.setContent(`<html><head><style>@font-face{font-family:PF;src:url("${pathToFileURL(path.resolve('node_modules/@fontsource/playfair-display/files/playfair-display-latin-500-normal.woff2')).href}")}
    html,body{margin:0;background:transparent}div{height:${REFH}px;display:flex;align-items:center;justify-content:center;font:500 ${cfg.tamanhoReferencia || 50}px PF;letter-spacing:.06em;
    color:transparent;-webkit-background-clip:text;background-clip:text;background-image:linear-gradient(180deg,#fff,#d9d4cc);filter:drop-shadow(0 2px 6px rgba(0,0,0,.8))}</style></head>
    <body><div>${REF}</div></body></html>`);
  await rp.evaluate(() => document.fonts.ready); await rp.waitForTimeout(300);
  await rp.screenshot({ path: 'ref_label.png', omitBackground: true }); await rp.close();
}
const REFIN = REF ? ['-i', 'ref_label.png'] : [], REFOV = REF ? `[o0][${'IDX'}:v]overlay=0:${REFY * PX}` : '[o0]null';
await page.goto(pathToFileURL(path.resolve('scene_legenda.html')).href);
if (process.env.SEMFILME) await page.evaluate(() => { window.film = () => {}; });
const ok = await page.evaluate(() => window.fontsOK()); if (ok !== 'ok') { console.error(ok); process.exit(2); }
// LOOP=1: o fundo é um loop curto (ex.: GIF) que repete sem fim — começa no quadro certo do ciclo, sem gerar um fundo longo intermediário
const NF = process.env.LOOP ? +execFileSync('ffprobe', ['-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', band]).toString().trim() : 0;
if (mode === 'check') {
  for (const t of times.split(',')) {
    await page.evaluate(x => render(x), +t); await page.screenshot({ path: 'ov.png', ...SHOT });
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', NF ? String((Math.round(t * FPS) % NF) / FPS) : t, '-i', band, '-i', 'ov.png', ...REFIN, '-filter_complex', `[0:v]scale=${BW * PX}:${BH * PX}[b];[b][1:v]overlay${OVXY},pad=${OW * PX}:${OH * PX}:0:${BY * PX}:black[o0];${REFOV.replace('IDX', 2)}`, '-frames:v', '1', `${out}_${t}.png`]);
  }
  fs.unlinkSync('ov.png');
} else {
  // FRAMES=ini:fim → só esse trecho (vídeo sem áudio, para juntar depois); sem FRAMES = vídeo inteiro com áudio
  const [F0, F1] = process.env.FRAMES ? process.env.FRAMES.split(':').map(Number) : [0, Math.round(DUR * FPS)], parte = !!process.env.FRAMES;
  const T0 = F0 / FPS, TL = (F1 - F0) / FPS;
  const BIN = NF ? ['-stream_loop', '-1', '-ss', String((F0 % NF) / FPS), '-i', band] : ['-ss', String(T0), '-i', band];
  const AIN = parte ? [] : ['-i', audio], AMAP = parte ? ['-an'] : ['-map', '2:a', '-af', 'apad', '-c:a', 'aac', '-b:a', '192k'];
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', ...BIN, '-f', 'image2pipe', '-c:v', 'png', '-r', String(FPS), '-i', '-', ...AIN, ...REFIN,
    '-filter_complex', `[0:v]fps=${FPS},trim=0:${TL},setpts=PTS-STARTPTS,scale=${BW * PX}:${BH * PX}[b];[b][1:v]overlay${OVXY ? OVXY + ':' : '='}shortest=1,pad=${OW * PX}:${OH * PX}:0:${BY * PX}:black[o0];${REFOV.replace('IDX', parte ? 2 : 3)},format=yuv420p[o]`, '-map', '[o]', ...AMAP, '-t', String(TL),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', String(process.env.CRF || 18), ...(parte ? [] : ['-maxrate', '6M', '-bufsize', '10M']),
    // em 4K cada encoder chegava a 2,2 GB (vários em paralelo = falta de memória): limita threads e antecipação
    ...(PX > 1 ? ['-threads', '3', '-x264-params', 'rc-lookahead=12'] : []), '-r', String(FPS), '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = F0; f < F1; f++) {
    await page.evaluate(x => render(x), f / FPS);
    const buf = await page.screenshot({ type: 'png', ...SHOT });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log(`PRONTO ${out} em ${((Date.now() - t0) / 60000).toFixed(1)} min`);
}
await browser.close();
