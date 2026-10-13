# Dependências e rede

## Usadas de verdade
| item | papel | obrigatório |
|---|---|---|
| Python 3.10+ (testado 3.13) | tudo | sim |
| FFmpeg/FFprobe (testado 6.1, libx264) | decodificar, encode H.264/AAC, cortes de cena, blackdetect, ebur128 | sim |
| NumPy, Pillow, SciPy | render, efeitos, áudio (STFT/batidas), recorte/partes | sim |
| requests | pesquisa e download | sim (para pesquisa) |
| rembg + onnxruntime (+ modelo `isnet-anime`) | recorte → parallax 2.5D | opcional (sem ele: só câmera) |
| librosa | só confere o BPM | opcional |
| GPU NVIDIA + h264_nvenc | encode mais rápido (`--gpu`) | opcional (testado: indisponível aqui → CPU) |
Não usados (avaliados e dispensados): OpenCV, MoviePy, Remotion — NumPy+Pillow+FFmpeg cobrem tudo com menos peso.

Instalação: `pip install numpy pillow scipy requests "rembg[cpu]"` + ffmpeg no PATH. `aml.py env` confere.

## Rede (ambiente Claude Code na nuvem com rede "Custom")
Para a pesquisa funcionar além do YouTube, liberar no ambiente (menu do ambiente → Edit → Network access →
Allowed domains, mantendo "package managers"):
```
commons.wikimedia.org
upload.wikimedia.org
api.openverse.org
archive.org
collectionapi.metmuseum.org
images.metmuseum.org
api.artic.edu
www.artic.edu
i.pinimg.com
cdna.artstation.com
```
(Google Images/Pinterest/Bing ficam para descoberta via WebSearch; o download é da página de origem.)
Já funcionam: www.youtube.com, i.ytimg.com, drive.google.com, drive.usercontent.google.com.
Download de vídeo do YouTube exige login ("not a bot") — não é contornado; clipes vêm de arquivos do usuário/Drive.
