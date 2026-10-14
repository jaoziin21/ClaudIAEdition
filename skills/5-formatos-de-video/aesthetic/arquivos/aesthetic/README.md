# Aesthetic — edição de imagens que "ganham vida" (comando `/aesthetic`)
Referência (10/out): edit "Jesus Christus | JoJo Steel Ball Run | 120Fps" — quadrinhos de mangá animados, borda de raio,
estrelas, Terra, raios de luz, tinta/RGB/inversão nas batidas, versículo palavra por palavra, glitch no fim.
Nosso formato: TELA CHEIA vertical 1080x1920, 60 fps (movimento liso).

## O que pedir para o usuário mandar
1. **Imagens**: ~1 a cada 1–1,5 s de vídeo (≈20 para 25 s). Quadrinhos de mangá/anime ou ilustrações, 1 momento forte cada
   (misturar rosto bem de perto, mãos/detalhe, corpo inteiro e cena aberta). Mínimo 1500 px no lado menor, JPG/PNG,
   sem marca d'água, sem estar cortado. Vertical ou quadrado rende mais; horizontal vira "pan" ou quadrinho recortado.
2. **Personagem recortado (opcional, melhora muito)**: PNG com fundo transparente → movimento em CAMADAS (personagem na frente,
   fundo desfocado atrás em outro ritmo + raios de mangá). Sem isso, `"recorte": true` tenta recortar sozinho (rembg isnet-anime).
3. **Áudio**: música com batida marcada (os cortes caem nela) e/ou narração do versículo (vira o texto).
Sem imagens: `"de_video"` tira quadros dos vídeos do usuário nas trocas de cena.

## Como o motor funciona
- `aesthetic/prepara.py`: fluxo espectral do áudio → batidas (fortes = 20% maiores); cortes na batida mais forte entre
  `corte_min` (0,7 s) e `corte_max` (1,6 s); palavras-chave também puxam corte; cada plano ganha imagem (em ordem) e movimento
  sem repetir em seguida → `aesthetic_data.js`.
- `scene_aesthetic.html` (canvas 1080x1920): movimentos zoom | card (borda de raio azul/branca sobre estrelas) | pan | gira |
  voa (encolhe e voa no espaço) | tremor | camadas; entrada com soco de escala + rastro + clarão; batida forte = inversão de cor
  ou tinta vermelha/verde; separação RGB em cada corte; texto Bebas 168 px com brilho, chave vermelha; glitch derretendo no fim; grão.
- `render_aesthetic.mjs`: abas do Chromium em paralelo, JPEG → ffmpeg com o áudio.
