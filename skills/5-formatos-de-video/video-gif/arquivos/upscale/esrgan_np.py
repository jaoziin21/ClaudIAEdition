# Upscale de anime com IA (Real-ESRGAN "realesr-animevideov3", 4x) rodando em numpy puro — sem torch/GPU.
# Os pesos (.pth) vêm do GitHub oficial do Real-ESRGAN (HuggingFace e PyTorch são bloqueados aqui):
#   curl -sSL -o engine/upscale/pesos/realesr-animevideov3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth
# uso: python3 -I esrgan_np.py <entrada.mp4> <saida.mp4> [largura=1920] [altura=1080]
# Faz 4x com a rede e reduz com lanczos para o tamanho final (fica bem mais nítido que só esticar). ~3–5 s por quadro de 736x414.
import sys, os, zipfile, pickle, subprocess, json, time, numpy as np

PESOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pesos', 'realesr-animevideov3.pth')

def carrega(path):
    # lê o .pth (zip + pickle do torch) SEM torch e sem executar nada do arquivo: só reconstrói tensores float32
    z = zipfile.ZipFile(path); raiz = z.namelist()[0].split('/')[0]
    class Storage:
        def __init__(self, key): self.a = np.frombuffer(z.read(f'{raiz}/data/{key}'), dtype=np.float32)
    def rebuild(st, off, size, stride, *_):
        a = st.a; return np.lib.stride_tricks.as_strided(a[off:], shape=size, strides=[s * 4 for s in stride]).copy() if size else a[off:off + 1].copy()
    class U(pickle.Unpickler):
        def find_class(self, mod, name):
            if (mod, name) == ('collections', 'OrderedDict'): import collections; return collections.OrderedDict
            if (mod, name) == ('torch._utils', '_rebuild_tensor_v2'): return rebuild
            if mod == 'torch' and name == 'FloatStorage': return 'float'
            raise pickle.UnpicklingError(f'proibido: {mod}.{name}')
        def persistent_load(self, pid):
            assert pid[0] == 'storage' and pid[1] == 'float', pid
            return Storage(pid[2])
    d = U(z.open(f'{raiz}/data.pkl')).load()
    return d.get('params', d)

P = carrega(PESOS)
convs = sorted({int(k.split('.')[1]) for k in P if k.endswith('.weight') and P[k].ndim == 4})
# cada conv 3x3 vira uma matriz (9*Cin, Cout); a imagem (layout H, W, C) vira colunas em faixas de 48 linhas (im2col)
L = [(np.ascontiguousarray(P[f'body.{i}.weight'].transpose(2, 3, 1, 0)).reshape(-1, P[f'body.{i}.weight'].shape[0]), P[f'body.{i}.bias'], P.get(f'body.{i + 1}.weight')) for i in convs]
UP = 4

def conv(x, w, b, S=48):
    H, W, C = x.shape; xp = np.pad(x, ((1, 1), (1, 1), (0, 0))); out = np.empty((H, W, w.shape[1]), np.float32)
    for y in range(0, H, S):
        h = min(S, H - y)
        col = np.lib.stride_tricks.sliding_window_view(xp[y:y + h + 2], (3, 3), axis=(0, 1))   # h, W, C, 3, 3
        out[y:y + h] = (np.ascontiguousarray(col.transpose(0, 1, 3, 4, 2)).reshape(h * W, 9 * C) @ w + b).reshape(h, W, -1)
    return out

def sr(img):   # img: H,W,3 float32 0..1 → 4H,4W,3
    x = img
    for w, b, a in L:
        x = conv(x, w, b)
        if a is not None: x = np.where(x >= 0, x, x * a)          # PReLU por canal
    H, W, _ = x.shape
    x = x.reshape(H, W, 3, UP, UP).transpose(0, 3, 1, 4, 2).reshape(H * UP, W * UP, 3)   # pixel shuffle
    return x + np.repeat(np.repeat(img, UP, 0), UP, 1)             # + imagem esticada (vizinho mais próximo)

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]; OW = int(sys.argv[3]) if len(sys.argv) > 3 else 1920; OH = int(sys.argv[4]) if len(sys.argv) > 4 else 1080
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate', '-of', 'json', src]))['streams'][0]
    W, H, fps = info['width'], info['height'], info['r_frame_rate']
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb48le', '-s', f'{W * UP}x{H * UP}', '-r', fps, '-i', '-',
                            '-vf', f'scale={OW}:{OH}:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '10', '-pix_fmt', 'yuv444p', '-an', dst], stdin=subprocess.PIPE)
    n, t0 = 0, time.time()
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        y = sr(np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255)
        enc.stdin.write((np.clip(y, 0, 1) * 65535 + 0.5).astype('<u2').tobytes()); n += 1
        if n % 10 == 0: print(f'{n} quadros, {(time.time() - t0) / n:.1f} s/quadro', flush=True)
    enc.stdin.close(); enc.wait(); print(f'PRONTO {dst}: {n} quadros em {(time.time() - t0) / 60:.1f} min')
