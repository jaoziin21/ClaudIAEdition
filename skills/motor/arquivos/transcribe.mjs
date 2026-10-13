// usage: node transcribe.mjs <audio.mp3|wav> words_raw.json
// Whisper small (offline, from npm) -> word timestamps, NFC text. Needs ffmpeg on PATH.
import { pipeline, env } from '@huggingface/transformers';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import fs from 'fs'; import path from 'path';
env.allowRemoteModels = false;
env.localModelPath = path.join(path.dirname(fileURLToPath(import.meta.url)), 'node_modules', 'sts-whisper-small', 'models') + path.sep;
const pcm = spawnSync('ffmpeg', ['-v', 'error', '-i', process.argv[2], '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], { maxBuffer: 1 << 30 }).stdout;
const audio = new Float32Array(pcm.buffer, pcm.byteOffset, pcm.length / 4);
const asr = await pipeline('automatic-speech-recognition', 'Xenova/whisper-small', { dtype: 'q8' });
const out = await asr(audio, { language: 'portuguese', task: 'transcribe', chunk_length_s: 30, stride_length_s: 5, return_timestamps: 'word' });
const words = [];
for (const c of out.chunks) { const w = c.text.trim().normalize('NFC'); if (!w) continue;
  if (w.startsWith('-') && words.length) { words.at(-1).w += w; words.at(-1).e = c.timestamp[1]; continue; }
  words.push({ w, s: +c.timestamp[0].toFixed(2), e: +(c.timestamp[1] ?? c.timestamp[0] + .3).toFixed(2) }); }
fs.writeFileSync(process.argv[3], JSON.stringify(words, null, 0));
console.log(out.text);
