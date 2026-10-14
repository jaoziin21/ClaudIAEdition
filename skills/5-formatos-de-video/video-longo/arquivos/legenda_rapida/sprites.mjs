// LEGENDA RÁPIDA — passo 1: fotografa cada palavra UMA vez (mesma cena, fonte, degradê e posição do scene_legenda.html)
// em vez de fotografar a tela inteira em todo quadro. O passo 2 (compor.py) anima as palavras quadro a quadro.
// uso (de dentro de motor/, depois de `node render_legenda.mjs ... dados` com as mesmas variáveis OUTW/OUTH/BANDH/LEG*/SIZE/ESCALA):
//   node legenda_rapida/sprites.mjs <pasta_saida>
import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
import fs from 'fs'; import path from 'path';
const OUT = process.argv[2]; fs.mkdirSync(OUT, { recursive: true });
const OW = +(process.env.OUTW || 1080), OH = +(process.env.OUTH || 1920);
const BW = OW, BH = +(process.env.BANDH || 608), PX = +(process.env.ESCALA || 1);
const PAD = 40;   // folga em volta de cada palavra (px de layout): cabe desfoque, brilho e a inclinação
const opt = { args: ['--allow-file-access-from-files', '--font-render-hinting=none'] };
if (fs.existsSync('/opt/pw-browsers')) { const d = fs.readdirSync('/opt/pw-browsers').filter(x => /^chromium-\d+$/.test(x)).sort().pop(); if (d) opt.executablePath = `/opt/pw-browsers/${d}/chrome-linux/chrome`; }
const browser = await chromium.launch(opt);
const page = await browser.newPage({ viewport: { width: BW, height: BH }, deviceScaleFactor: PX });
await page.goto(pathToFileURL(path.resolve('scene_legenda.html')).href);
const ok = await page.evaluate(() => window.fontsOK()); if (ok !== 'ok') { console.error(ok); process.exit(2); }
// cena "parada": sem poeira, sem sombra do bloco (o compor.py refaz), sem animação
await page.evaluate(() => { window.film = () => {}; document.getElementById('fx').style.display = 'none';
  document.getElementById('wrap').style.filter = 'none'; });
const clip = (x, y, w, h) => { const x0 = Math.max(0, Math.floor(x)), y0 = Math.max(0, Math.floor(y));
  return { x: x0, y: y0, width: Math.min(BW, Math.ceil(x + w)) - x0, height: Math.min(BH, Math.ceil(y + h)) - y0 }; };
// sombreado escuro atrás do texto (fixo): foto dele sozinho, opacidade 1
await page.evaluate(() => { document.getElementById('wrap').style.visibility = 'hidden'; document.getElementById('shade').style.opacity = 1; });
await page.screenshot({ path: path.join(OUT, 'shade.png'), omitBackground: true });
await page.evaluate(() => { document.getElementById('wrap').style.visibility = 'visible'; document.getElementById('shade').style.opacity = 0; });
const meta = { BW, BH, OW, OH, PX, size: 0, lines: [] };
const nLines = await page.evaluate(() => LEG.lines.length); meta.size = await page.evaluate(() => LEG.size);
const t0 = Date.now();
for (let li = 0; li < nLines; li++) {
  // monta a linha igual ao render(): mesmos spans, palavras visíveis, sem filtro/transformação
  const words = await page.evaluate(i => {
    const L = LEG.lines[i], line = document.getElementById('line');
    line.innerHTML = L.words.map(w => `<span class="w${w.k ? ' k' : ''}">${w.k ? w.w.replace(/,$/, '<i class="v">,</i>') : w.w}</span>`).join('');
    return [...line.querySelectorAll('.w')].map(s => { s.style.opacity = 1; s.style.visibility = 'hidden';
      const r = s.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; });
  }, li);
  const L = { start: 0, end: 0, words: [] };
  for (let wi = 0; wi < words.length; wi++) {
    const b = words[wi], c = clip(b.x - PAD, b.y - PAD, b.w + 2 * PAD, b.h + 2 * PAD), f = `l${li}_w${wi}.png`;
    await page.evaluate(([wi, prev]) => { const sp = document.querySelectorAll('#line .w');
      if (prev >= 0) sp[prev].style.visibility = 'hidden'; sp[wi].style.visibility = 'visible'; }, [wi, wi - 1]);
    await page.screenshot({ path: path.join(OUT, f), omitBackground: true, clip: c });
    L.words.push({ f, box: b, crop: { x: c.x, y: c.y, w: c.width, h: c.height } });
  }
  meta.lines.push(L);
  if (li % 50 === 0) console.log(`linha ${li}/${nLines} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
}
// tempos e palavras-chave vêm do mesmo LEG que o render antigo usa
const LEG = await page.evaluate(() => LEG);
LEG.lines.forEach((l, i) => { Object.assign(meta.lines[i], { start: l.start, end: l.end });
  l.words.forEach((w, j) => Object.assign(meta.lines[i].words[j], { s: w.s, k: !!w.k })); });
fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify(meta));
console.log(`PRONTO ${nLines} linhas, ${meta.lines.reduce((a, l) => a + l.words.length, 0)} palavras em ${((Date.now() - t0) / 1000).toFixed(0)} s`);
await browser.close();
