#!/usr/bin/env bash
# Prepara o motor de edição (rode uma vez, e de novo se mudar de computador). Pode rodar quantas vezes quiser.
# Precisa ter instalado: Node.js 20+, Python 3.10+ e ffmpeg (veja o README da pasta skills/).
set -e
cd "$(dirname "$0")"
falta=0
for c in node npm python3 ffmpeg ffprobe; do command -v "$c" >/dev/null 2>&1 || { echo "FALTA instalar: $c"; falta=1; }; done
[ "$falta" = 1 ] && { echo "Instale o que falta e rode de novo: bash motor/setup.sh"; exit 1; }
mkdir -p estilos efeitos/tela efeitos/video
if [ -d node_modules/playwright ] && [ -d node_modules/sts-whisper-small ] && [ -d node_modules/@fontsource/roboto ]; then
  echo "motor ok"
else
  # onnxruntime tenta baixar binários de placa de vídeo: não precisa
  ONNXRUNTIME_NODE_INSTALL_CUDA=skip npm install --no-audit --no-fund --silent
fi
# navegador que desenha a legenda (já vem instalado na versão do Claude Code na nuvem)
if [ -d /opt/pw-browsers ]; then :; else npx --yes playwright install chromium >/dev/null; fi
python3 -c "import numpy" 2>/dev/null || python3 -m pip install -q numpy 2>/dev/null || python3 -m pip install -q --break-system-packages numpy || true
echo "motor pronto"
