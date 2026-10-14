---
name: video-longo
description: Estilo de vídeo "Vídeo longo" para o YouTube normal: horizontal 1920x1080, 10 a 30 minutos, fundo em loop, voz limpa, legenda palavra por palavra num canto livre, música baixa e capítulos na descrição; renderiza em partes paralelas. Use quando o usuário pedir vídeo longo, horizontal ou para o YouTube normal.
---
# Vídeo longo (YouTube horizontal)

Requer **motor**. Arquivos extras desta skill vão para `motor/` (render em trechos, render rápido, limpeza de voz).

1. **Voz** em partes: limpar cada uma (chiado, "s" estridente) e igualar o volume: `bash limpa_audio.sh parte.wav parte_limpa.wav`.
   Emendar sem cortar palavra (conferir as emendas ouvindo os trechos).
2. **Tempos**: `bash transcreve_longo.sh` (transcrição em partes paralelas + alinhamento com o roteiro) → `words.json`.
3. **Fundo**: GIF/vídeo curto ampliado (se precisar, `upscale/esrgan_np.py` da skill video-gif) e em loop sem emenda, 1920x1080.
   1080p é suficiente.
4. **Legenda** (`legenda.json`: `keywords`, `nomes`, `quebras`, `referencia`): posição num canto livre, longe do personagem, com
   `OUTW=1920 OUTH=1080 BANDH=1080 LEGX=0.27 LEGY=0.36 LEGW=0.44 SIZE=66`. Testar: `node render_legenda.mjs words.json fundo.mp4 audio.wav /tmp/t <dur> check 30,300`.
5. **Render**: `bash render_rapido.sh ...` (cerca de 10x mais rápido; 26 min de vídeo ≈ 24 min) ou `bash render_longo.sh <words> <fundo> <audio> <saída> <dur>`
   (trechos paralelos; se cair, rodar de novo continua de onde parou).
6. **Música** baixa (−4 a −6 dB, abaixa sozinha na fala) e crédito na descrição se for licença CC-BY.
7. **Entrega**: passa de 30 MB → subir no Google Drive do usuário (ou outro serviço que ele indicar) e mandar o link.
8. **Post**: descrição com CAPÍTULOS (00:00 Título...) a partir dos tempos do `words.json`.
