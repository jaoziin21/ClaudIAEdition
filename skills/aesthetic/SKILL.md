---
name: aesthetic
description: Edição "Aesthetic": vídeo em tela cheia feito de imagens paradas que ganham vida — quadrinhos com borda de raio sobre estrelas, zoom, giro, personagem em camadas, cortes na batida da música, inversão nas batidas fortes e texto palavra por palavra. Use quando o usuário mandar imagens e quiser um edit cortado na batida.
---
# Aesthetic

Requer **motor**. Na primeira vez: `python3 -m pip install "rembg[cpu]" pillow numpy` (recorte do personagem; o modelo baixa no 1º uso).
Detalhes do que pedir ao usuário: `motor/aesthetic/README.md`.

1. `projetos/AAAA-MM-DD-nome/` com `imagens/` (JPG/PNG; PNG transparente = personagem recortado) e `audio.wav`
   (música com batida e/ou narração, loudnorm −14). Sem imagens: `"de_video"` tira quadros de um vídeo nas trocas de cena.
2. Texto (opcional): transcrever a narração → `words.json` (motor); palavras em `"keywords"` ficam vermelhas.
3. `aesthetic.json`: `{"audio":"audio.wav","imagens":"imagens","recorte":true,"keywords":[...],"fps":60}`.
4. `cd motor && python3 -I aesthetic/prepara.py ../projetos/X` (batidas → cortes → plano de movimentos);
   teste: `node render_aesthetic.mjs ../projetos/X/audio.wav /tmp/q check 1,5,9`; vídeo: `node render_aesthetic.mjs ../projetos/X/audio.wav ../projetos/X/final.mp4`.
5. `final_envio.mp4` (até 30 MB) → mandar → post.
