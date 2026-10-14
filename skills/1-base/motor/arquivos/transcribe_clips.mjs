// usage: node transcribe_clips.mjs <audio.wav> <clips.json [[ini,dur],...]> <out.json>
// Transcreve TRECHOS CURTOS (cortados nas pausas) com o modelo carregado uma vez só. Em janelas longas o Whisper
// atrasa os tempos das palavras (até 3 s); em trechos curtos que começam numa pausa os tempos ficam certos.
import { pipeline, env } from '@huggingface/transformers';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import fs from 'fs'; import path from 'path';
env.allowRemoteModels = false;
env.localModelPath = path.join(path.dirname(fileURLToPath(import.meta.url)), 'node_modules', 'sts-whisper-small', 'models') + path.sep;
const [,, file, clipsF, outF] = process.argv;
const pcm = spawnSync('ffmpeg', ['-v', 'error', '-i', file, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], { maxBuffer: 1 << 30 }).stdout;
const all = new Float32Array(pcm.buffer, pcm.byteOffset, pcm.length / 4);
const asr = await pipeline('automatic-speech-recognition', 'Xenova/whisper-small', { dtype: 'q8' });
const res = [];
// às vezes o alinhamento interno falha e todas as palavras vêm em 29,98 s → tenta de novo com o trecho deslocado/acolchoado
const tenta = async (ini, dur, pad) => {
  const a = all.slice(Math.round(ini * 16000), Math.round((ini + dur) * 16000)), audio = new Float32Array(a.length + Math.round(pad * 16000));
  audio.set(a, Math.round(pad * 16000));
  const out = await asr(audio, { language: 'portuguese', task: 'transcribe', return_timestamps: 'word' });
  const words = [];
  for (const c of out.chunks) { const w = c.text.trim().normalize('NFC'); if (!w) continue;
    const s = c.timestamp[0] - pad, e = (c.timestamp[1] ?? c.timestamp[0] + 0.3) - pad;
    words.push({ w, s: +(s + ini).toFixed(2), e: +(Math.min(e, dur) + ini).toFixed(2), ok: s > -0.2 && s < dur + 0.2 }); }
  return { text: out.text.trim(), words, ok: words.length > 0 && words.every(w => w.ok) };
};
for (const [ini, dur] of JSON.parse(fs.readFileSync(clipsF, 'utf8'))) {
  let r, tag = '';
  for (const [d, pad] of [[0, 0], [0, 0.5], [-0.3, 0], [0.25, 0], [-0.5, 0.3], [0, 1.0]]) {
    r = await tenta(ini + d, dur - d, pad); tag = `desloc ${d} pad ${pad}`; if (r.ok || !r.words.length) break; }
  const words = r.words.filter(w => w.ok).map(({ ok, ...w }) => w);
  res.push({ ini, dur, text: r.text, words });
  console.log(`${ini.toFixed(2)} +${dur.toFixed(1)}  ${r.ok ? '' : '[SEM TEMPO] '}${r.text}  (${tag})`);
}
fs.writeFileSync(outF, JSON.stringify(res));
