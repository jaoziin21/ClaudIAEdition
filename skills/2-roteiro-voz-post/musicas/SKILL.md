---
name: musicas
description: Biblioteca de músicas do canal. Mostra o NOME de todas as músicas disponíveis (com artista, duração e clima) quando o usuário digitar /musicas ou perguntar "quais músicas tem"; escolhe a música que combina com o vídeo, começa no ponto em que ela já está tocando e mistura baixinho por baixo da voz. Use também quando o usuário mandar músicas novas para guardar.
---
# Músicas

As músicas ficam em `motor/musicas/` e a lista em `motor/musicas/LISTA.md`.

## /musicas = mostrar a lista
Quando o usuário digitar `/musicas` (ou perguntar quais músicas tem), mostre a tabela de `motor/musicas/LISTA.md`
com o NOME de cada música, o artista, a duração e o clima. Não precisa tocar trecho.
Confira se cada arquivo da lista existe na pasta e se há algum `.mp3` na pasta que ainda não está na lista; se houver,
acrescente a linha (nome, artista e duração:
`ffprobe -v error -show_entries format=duration:format_tags=title,artist -of compact=p=0 arquivo.mp3`).
Música da lista cujo arquivo não está na pasta: mostre marcada como "(falta o arquivo)".
No fim, diga: "Para usar uma, é só falar o nome no pedido do vídeo. Se não falar, eu escolho a que combina."

## Guardar músicas novas
Quando o usuário mandar músicas: copie para `motor/musicas/` com nome curto (minúsculas, `_` no lugar de espaço),
meça a duração e em que segundo ela já está no volume normal (abaixo) e acrescente uma linha na `LISTA.md`.
Arquivo que não é áudio (ex.: instalador `.exe`) não se guarda nem se abre.

## Usar num vídeo
1. **Escolher** pelo clima do texto (calmo, emotivo, épico) quando o usuário não disser qual. Diga qual escolheu.
2. **Começar já tocando** (sem fade-in): use a coluna "Começa tocando em" da lista. Para música nova, meça o volume por segundo:
   `ffmpeg -i musica.mp3 -t 40 -af "asetnsamples=48000,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level" -f null - 2>&1 | grep -o "RMS_level=[-0-9.]*"`
   e comece no primeiro segundo em que ela chega perto do volume normal da faixa.
3. **Misturar**: `bash motor/musica.sh <final_voz.mp4> motor/musicas/<arquivo.mp3> <final.mp4> <início_s> -6 0`
   (−6 = volume da música; 0 = sem fade-in).
4. **Conferir o volume nas pausas da voz** (ache as pausas com `ffmpeg -i audio.wav -af silencedetect=n=-35dB:d=0.25 -f null -`):
   `ffmpeg -ss <segundo_da_pausa> -t 0.3 -i final.mp4 -af volumedetect -vn -f null - 2>&1 | grep mean_volume`
   O certo é a música ficar entre −29 e −33 dB nas pausas. Se ficar mais alta (faixa "cheia"), refaça com −10 a −14 no lugar de −6.
5. Na descrição do post, escreva `Música: "<nome>" — <artista>` (Kevin MacLeod exige crédito).

## Direitos
Músicas de outros artistas podem gerar reivindicação de direitos (Content ID) no YouTube. As de Kevin MacLeod são liberadas com crédito.
Avise o usuário uma vez quando usar uma música de terceiros.
