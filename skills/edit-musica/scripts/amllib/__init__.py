"""Anime Motion Lab — motor de animação 2D/2.5D sobre material EXISTENTE (sem IA generativa).

Módulos:
  util      — utilitários (subprocess, json, ffprobe)
  project   — estrutura do projeto + manifesto de fontes
  media     — inspeção de imagens/vídeos (resolução, nitidez, potencial de animação)
  search    — busca real em APIs abertas (Commons, Openverse, Internet Archive, Met, AIC) + consultas p/ WebSearch
  fetch     — download legítimo + registro no manifesto
  prep      — recorte (rembg), camadas 2.5D, preenchimento SEM geração, partes de puppet, spritesheet
  audio     — BPM, batidas, impactos, energia e seções (NumPy puro; librosa opcional)
  motion    — easing, keyframes, presets de câmera
  effects   — efeitos cinematográficos (glow, RGB split, glitch, flash, grão, ...)
  render    — compositor por quadro → FFmpeg
  plan      — planejamento automático do edit sincronizado com a música
  qa        — validação do vídeo final e das fontes
  reference — análise de vídeo de referência (ritmo de cortes, cor, movimento)
"""
__version__ = "1.0.0"
