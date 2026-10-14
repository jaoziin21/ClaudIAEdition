// Monta a FAIXA (imagem 1080x760 tratada + zoom lento) a partir do vídeo de entrada, aplicando os EFEITOS DE IMAGEM do projeto.
// usage (rodar dentro de motor/): node faixa.mjs <entrada.mp4> <projeto_dir> [saida.mp4] [inicio_s] [dur_s]
//   projeto_dir/lado.json: "pacote": "filme-antigo" (misturas prontas em efeitos/pacotes.json) e/ou "efeitos": ["vhs", ...] (avulsos, efeitos/efeitos.json)
//     → as partes de IMAGEM dos efeitos são encadeadas na ordem; as de TELA o render_lado.mjs desenha por cima/baixo da legenda.
//   Sem efeito de imagem na lista → usa o filtro do estilo de legenda (como antes), a não ser que "efeitosDaLegenda": false
//   (aí sai só a imagem limpa: recorte + nitidez).
// Saída padrão: projeto_dir/faixa.mp4
import fs from 'fs'; import path from 'path'; import { execFileSync } from 'child_process';
const [,, entrada, dir, saida0, ini0, dur0] = process.argv;
if (!entrada || !dir) { console.error('uso: node faixa.mjs <entrada.mp4> <projeto_dir> [saida.mp4] [inicio_s] [dur_s]'); process.exit(1); }
const cfg = JSON.parse(fs.readFileSync(path.join(dir, 'lado.json'), 'utf8'));
const CAT = JSON.parse(fs.readFileSync('efeitos/efeitos.json', 'utf8'));
const saida = saida0 || path.join(dir, 'faixa.mp4');
const durTot = +execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', entrada]).toString();
const ini = +(ini0 || 0), dur = +(dur0 || (durTot - ini)), NF = Math.round(dur * 30);
const PAC = JSON.parse(fs.readFileSync('efeitos/pacotes.json', 'utf8'));
const pacotes = [cfg.pacote || []].flat(); for (const p of pacotes) if (!PAC[p]) { console.error(`pacote desconhecido: ${p}`); process.exit(1); }
const nomes = [...new Set([...pacotes.flatMap(p => PAC[p].efeitos), ...(cfg.efeitos || []).map(e => typeof e === 'string' ? e : e.nome)])];
for (const n of nomes) if (!CAT[n]) { console.error(`efeito desconhecido: ${n} (ver efeitos/efeitos.json)`); process.exit(1); }
const looks = nomes.filter(n => CAT[n].video);
const BASE = 'fps=30,crop=1534:1080:193:0,hqdn3d=1.2:1.2:3:3,scale=1080:760:flags=lanczos,cas=0.3';
const ZOOM = `scale=2160:1520,zoompan=z='1+0.06*on/${NF}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x760:fps=30`;
let graph, inputs = ['-ss', String(ini), '-t', String(dur), '-i', entrada];
if (looks.length) {
  const parts = [`[0:v]${BASE}[s0]`];
  looks.forEach((n, i) => {
    let frag = fs.readFileSync(path.join('efeitos/video', CAT[n].video), 'utf8').trim().replace(/\n/g, '');
    (CAT[n].texturas || []).forEach((tx, k) => { const idx = inputs.filter(a => a === '-i').length; inputs.push('-loop', '1', '-framerate', '30', '-t', String(dur), '-i', path.join('efeitos', tx)); frag = frag.replaceAll(`{T${k}}`, `${idx}:v`); });
    parts.push(frag.replaceAll('{I}', `s${i}`).replaceAll('{O}', `s${i + 1}`).replaceAll('{P}', `p${i}`));
  });
  parts.push(`[s${looks.length}]${ZOOM},format=yuv420p[v]`);
  graph = parts.join(';');
} else if (cfg.efeitosDaLegenda !== false && cfg.estilo) {
  const est = JSON.parse(fs.readFileSync(path.join('estilos', cfg.estilo + '.json'), 'utf8'));
  const f = fs.readFileSync(est.filtro, 'utf8').trim().replace(/\n/g, '');
  if (/\[1:v\]/.test(f)) {   // filtro antigo do mangá (3 entradas, zoom já incluso)
    inputs.push('-loop', '1', '-framerate', '30', '-t', String(dur), '-i', 'estilos/reticula_manga.png', '-loop', '1', '-framerate', '30', '-t', String(dur), '-i', 'estilos/hachura_manga.png');
    graph = f.replace(/on\/\d+/, `on/${NF}`).replace(/\[v\]$/, ',format=yuv420p[v]');
  } else graph = `[0:v]${f},${ZOOM},format=yuv420p[v]`;
} else graph = `[0:v]${BASE},${ZOOM},format=yuv420p[v]`;
const grafo = saida + '.grafo.txt'; fs.writeFileSync(grafo, graph);   // nome único: dá para montar várias faixas ao mesmo tempo
console.log(`faixa: ${looks.length ? 'efeitos ' + looks.join(' + ') : (cfg.efeitosDaLegenda !== false && cfg.estilo ? 'filtro do estilo ' + cfg.estilo : 'limpa')} → ${saida} (${dur.toFixed(1)} s)`);
execFileSync('ffmpeg', ['-v', 'error', '-y', ...inputs, '-an', '-filter_complex_script', grafo, '-map', '[v]', '-t', String(dur),
  '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', saida], { stdio: 'inherit' });
fs.unlinkSync(grafo);
console.log('PRONTO', saida);
