import os from 'os';
// AESTHETIC — render da edição de quadrinhos em tela cheia (1080x1920). Antes: python3 -I aesthetic/prepara.py <projeto>
// usage (dentro de motor/): node render_aesthetic.mjs <audio> <out.mp4> [check t1,t2,...]
import { chromium } from 'playwright';
import { spawn } from 'child_process';
import { pathToFileURL } from 'url';
import fs from 'fs'; import path from 'path';
const [,, audio, out, mode, times] = process.argv;
const AE = JSON.parse(fs.readFileSync('aesthetic_data.js', 'utf8').replace(/^const AE=/, '').replace(/;$/, ''));
const FPS = AE.fps, DUR = AE.dur, W = 1080, H = 1920;
const opt = { args: ['--allow-file-access-from-files', '--font-render-hinting=none'] };
if (fs.existsSync('/opt/pw-browsers')) { const d = fs.readdirSync('/opt/pw-browsers').filter(x => /^chromium-\d+$/.test(x)).sort().pop(); if (d) opt.executablePath = `/opt/pw-browsers/${d}/chrome-linux/chrome`; }
const browser = await chromium.launch(opt);
const abre = async () => { const pg = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await pg.goto(pathToFileURL(path.resolve('scene_aesthetic.html')).href);
  const ok = await pg.evaluate(() => window.fontsOK()); if (ok !== 'ok') { console.error(ok); process.exit(2); } return pg; };
const page = await abre();
if (mode === 'check') {
  for (const t of times.split(',')) { await page.evaluate(x => render(x), +t); await page.screenshot({ path: `${out}_${t}.jpg`, type: 'jpeg', quality: 90 }); }
} else {
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'mjpeg', '-r', String(FPS), '-i', '-', '-i', audio,
    '-map', '0:v', '-map', '1:a', '-af', 'apad', '-t', String(DUR), '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-r', String(FPS), '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const JOBS = +(process.env.JOBS || Math.max(1, os.cpus().length - 1)), NF = Math.round(DUR * FPS), pages = [page];
  for (let k = 1; k < JOBS; k++) pages.push(await abre());
  const chain = pages.map(() => Promise.resolve()), job = [];
  const pede = f => { if (f >= NF || job[f]) return; const k = f % JOBS;
    job[f] = chain[k] = chain[k].then(async () => { await pages[k].evaluate(x => render(x), f / FPS); return pages[k].screenshot({ type: 'jpeg', quality: 92 }); }); };
  const t0 = Date.now();
  for (let f = 0; f < NF; f++) { for (let a = f; a < f + JOBS * 2; a++) pede(a); const buf = await job[f]; job[f] = true;
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log(`PRONTO ${out} em ${((Date.now() - t0) / 60000).toFixed(1)} min`);
}
await browser.close();
