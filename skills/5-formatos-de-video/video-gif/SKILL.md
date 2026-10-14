---
name: video-gif
description: Estilo de vídeo "Shorts de GIF": um GIF em loop sem emenda, ampliado com IA para alta resolução, num telão no meio da tela vertical, com a legenda ao lado do personagem como se ele estivesse falando, narração e música. Use quando o usuário mandar um GIF ou pedir um vídeo "tipo GIF".
---
# Shorts de GIF

Requer **motor** + uma legenda (a mais usada aqui é **sample-yellow** em 2 linhas). O usuário manda a ideia e o GIF.

## GIF
- No chat, o GIF costuma virar foto parada: peça o arquivo pelo Google Drive (ou outro link direto).
- `ffmpeg -i gif.gif -movflags +faststart -pix_fmt yuv420p gif_original.mp4`
- Ampliar com IA (Real-ESRGAN anime, roda no processador, alguns minutos):
  `python3 upscale/esrgan_np.py ../projetos/X/gif_original.mp4 ../projetos/X/gif_up1080.mp4 1920 1080`
- Loop sem emenda: tirar o quadro repetido do fim, `framerate=fps=30` (mistura suave entre quadros) e repetir:
  gerar 3 cópias em sequência e usar a do meio → `gif_loop.mp4`.
- Repetir até cobrir a voz e montar o telão. O personagem não pode ser cortado: desloque o recorte para o lado dele.
  Exemplo (personagem à direita): `ffmpeg -stream_loop -1 -i gif_loop.mp4 -t <dur> -filter_script:v filtro.txt -an -c:v libx264 -crf 16 -pix_fmt yuv420p faixa.mp4`,
  com o filtro da legenda trocando o `crop` para `crop=1534:1080:330:0` e o zoom `scale=2160:1520,zoompan=z='1+0.06*on/<quadros>':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x760:fps=30`.

## Legenda ao lado de quem "fala"
`lado.json`: `"estilo": "sample-yellow"`, `"multilinha": true`, `"maxch": 56`, `"tamanho": 50`, cena `{"t":0,"x":0.36,"y":0.5,"maxw":0.56}`
(espelhe o x se o personagem estiver à esquerda), `"referencia"` no topo quando houver, `"nomes"`, `"quebras"` e `"keywords"`.
Nunca encostar no personagem.

## Resto
Fluxo padrão do motor: voz → tempos → quadros de teste → render → música começando já tocando (`musica.sh ... <início> -6 0`) → post.
