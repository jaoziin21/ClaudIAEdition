---
name: buscar-midia
description: Busca na internet GIFs, fotos, animações e clipes (anime, filmes, esportes, natureza, qualquer assunto) para o fundo dos vídeos, prioriza fontes gratuitas, mostra opções, baixa a escolhida e registra a fonte. Use SEMPRE que um vídeo precisar de fundo e o usuário não mandar o arquivo, ou quando ele pedir "acha um GIF/imagem/cena de...".
---
# Buscar mídia

Sempre que faltar fundo para um vídeo, procure você mesmo antes de pedir ao usuário.

## 1. Entender o que precisa
Leia o roteiro e o `canal.md`: personagem ou assunto, clima (calmo, épico, triste), formato (GIF em loop, foto parada, clipe com movimento),
orientação (horizontal serve para o telão 1080x760 do meio). Monte 3 a 5 buscas diferentes (em português e em inglês).

## 2. Onde procurar (nesta ordem)
| Fonte | Para quê | Domínios para liberar |
|---|---|---|
| Pixabay | vídeos, fotos, ilustrações gratuitos | pixabay.com, cdn.pixabay.com |
| Pexels | vídeos e fotos gratuitos | pexels.com, images.pexels.com, videos.pexels.com |
| Wikimedia Commons | pinturas, fotos históricas, domínio público | commons.wikimedia.org, upload.wikimedia.org |
| Internet Archive | filmes antigos, domínio público | archive.org |
| GIPHY / Tenor | GIFs de anime, filmes, reações | giphy.com, media.giphy.com, tenor.com, media.tenor.com |
| YouTube | cenas e trechos (use o filtro Creative Commons quando der) | youtube.com, youtu.be, googlevideo.com |

## 3. Rede bloqueada?
Se uma busca ou download falhar por bloqueio de rede, diga ao usuário exatamente quais domínios liberar e onde:
- **Claude Code na nuvem (claude.ai/code):** configurações do ambiente → acesso à rede → adicionar os domínios da tabela.
- **Claude Code no computador:** quando aparecer o pedido de permissão para o site, é só autorizar.
Depois de liberar, continue de onde parou.

## 4. Mostrar opções
Encontre de 3 a 6 candidatos. Para cada um, tire um quadro (`ffmpeg -ss 1 -i <arquivo> -frames:v 1 previa_N.jpg`), monte uma folha
com as prévias e mande ao usuário com: de onde veio, duração, resolução e licença. Ele escolhe (ou você escolhe a melhor, se ele pediu).

## 5. Baixar e registrar
- Arquivo direto: `curl -L -o entrada/<nome>.<ext> <link>`.
- YouTube: `yt-dlp -f "bv*[height<=1080]+ba/b" --download-sections "*INICIO-FIM" -o entrada/<nome>.mp4 <link>` (só o trecho que precisa).
  Se o YouTube pedir login ("sign in / not a bot"), peça ao usuário o arquivo ou outro link.
- GIF: converter com `ffmpeg -i x.gif -movflags +faststart -pix_fmt yuv420p entrada/<nome>.mp4`; GIF pequeno → ampliar com a skill video-gif.
- Anote em `projetos/.../fontes.md`: link, autor, licença e o trecho usado. Licença livre (Pixabay, Pexels, domínio público) = pode usar.
  Material de terceiros (anime, filmes, esportes) = avise que pode haver reivindicação de direitos (Content ID) no YouTube.
