---
name: motor
description: Motor de edição de vídeos curtos (base de todas as outras skills): prepara o computador, organiza o projeto, transcreve a voz com o texto certo, monta o fundo, renderiza a legenda, mistura a música e confere o vídeo final. Use junto com qualquer skill de legenda, efeito ou estilo de vídeo, ou quando o usuário pedir para instalar/configurar o editor.
argument-hint: [o que fazer: instalar, conferir, ou o pedido de edição]
---
# Motor de edição (base)

Todas as skills de legenda, efeito e estilo de vídeo usam este motor. Ele fica na pasta `motor/` do projeto do canal.

## Organização do projeto
```
pasta-do-canal/
  .claude/skills/   skills instaladas
  motor/            motor de edição (rodar os comandos de dentro dela)
  canal.md          perfil do canal (criado pelo /comecar)
  regras.md         o que o usuário aprovou e rejeitou (você mantém atualizado)
  entrada/          arquivos brutos que o usuário mandar (vídeos, GIFs)
  projetos/AAAA-MM-DD-nome/   um por vídeo
```

## Primeira vez
1. `bash motor/setup.sh`. Se faltar Node.js, Python ou ffmpeg, explique ao usuário como instalar no sistema dele
   (Windows: `winget install OpenJS.NodeJS.LTS Python.Python.3.12 Gyan.FFmpeg`; Mac: `brew install node python ffmpeg`).
2. Leia `canal.md` e `regras.md` se existirem. Se não existir `canal.md`, sugira o `/comecar`.
3. Faltou fundo (GIF, foto, cena)? Use a skill **/buscar-midia** antes de pedir ao usuário.

## Regras fixas
- Antes de editar, leia `regras.md`. O que o usuário aprovou vira padrão; o que ele rejeitou não se repete.
- Sempre mostre QUADROS DE TESTE antes de renderizar o vídeo inteiro. Ajuste o que ele pedir e só então renderize.
- Formato padrão: vertical 1080x1920, 30 fps, telão de 1080x760 no meio (preto em cima e embaixo), volume final −14 LUFS.
- A legenda segue o TEXTO do roteiro (não a transcrição): os tempos vêm da transcrição, as palavras vêm do texto.
- Legenda nunca em cima de rosto. Confira também o quadro logo depois de cada corte de cena.
- Ao terminar, registre no `projetos/.../NOTAS.md` os comandos usados e o que ele aprovou ou pediu para mudar.
  Pedido que vale para os próximos vídeos ("sempre começa com a música tocando", "a referência sempre com os versículos")
  vai também para `regras.md`.
- Arquivo para mandar no chat: `final_envio.mp4` com até ~30 MB (reencodar em ~3,9 Mb/s se passar).
- Avise quando o vídeo usar imagem ou música de terceiros (risco de Content ID no YouTube).

## Fluxo padrão (de dentro de `motor/`; P = ../projetos/AAAA-MM-DD-nome)
1. **Voz**: o áudio da narração (gerado pela skill /voz ou mandado pelo usuário; pode vir em partes).
   Juntar as partes cortando o silêncio das pontas, com 0,45 s de pausa entre elas, e normalizar:
   ```
   TRIM="silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse"
   ffmpeg -y -i $P/voz_parte1.mp3 -i $P/voz_parte2.mp3 -filter_complex "[0:a]aresample=48000,aformat=channel_layouts=mono,$TRIM[a];[1:a]aresample=48000,aformat=channel_layouts=mono,$TRIM[b];anullsrc=r=48000:cl=mono,atrim=0:0.45[p];[a][p][b]concat=n=3:v=0:a=1" $P/voz_junta.wav
   ffmpeg -y -i $P/voz_junta.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 $P/audio.wav
   ```
2. **Texto**: o roteiro exato em `$P/roteiro.txt`.
3. **Tempos das palavras**: achar as pausas (`ffmpeg -i $P/audio.wav -af silencedetect=n=-35dB:d=0.25 -f null -`), montar
   `$P/clips.json` = `[[início, duração], ...]` com trechos de 2 a 6 s cortados nas pausas, e então:
   ```
   node transcribe_clips.mjs $P/audio.wav $P/clips.json $P/clips_words.json
   python3 alinha.py $P $P/clips_words.json        # → $P/words.json (palavras do roteiro, tempos da fala)
   ```
4. **Fundo (faixa)**: o vídeo/GIF de fundo vira o telão 1080x760 com o tratamento do estilo e zoom lento:
   `node faixa.mjs <vídeo de fundo> $P` → `$P/faixa.mp4` (usa o filtro da legenda escolhida ou os efeitos do `lado.json`).
   Fundo mais curto que a voz: repetir antes com `ffmpeg -stream_loop -1 -i fundo.mp4 -t <duração> -c copy fundo_longo.mp4`.
5. **lado.json** do projeto (a skill da legenda diz os valores):
   `{"estilo": "<legenda>", "referencia": "texto do topo (opcional)", "keywords": [...], "cenas": [{"t": 0, "x": 0.5, "y": 0.5}]}`.
   Outras chaves úteis: `"nomes"` (nomes próprios com maiúscula), `"quebras"` (trechos que fecham um bloco), `"tamanho"`,
   `"maxch"`, `"multilinha": true` (Sample Yellow em 2 linhas), `"refNumeros": "cheios"` (números da referência na altura
   das maiúsculas), `"pacote"`/`"efeitos"` (skills de efeito), cena com `"estilo"` (2ª legenda só naquela cena).
6. **Quadros de teste**: `node render_lado.mjs $P $P/faixa.mp4 $P/audio.wav /tmp/teste <duração> check 3,10,20` →
   olhar os PNGs e mandar ao usuário.
7. **Render**: `node render_lado.mjs $P $P/faixa.mp4 $P/audio.wav $P/final_voz.mp4 <duração>` (alguns minutos).
8. **Música** (skill /musicas ou arquivo do usuário): medir em que segundo a faixa já está tocando de verdade
   (`volumedetect` por segundo) e começar dali, sem fade-in:
   `bash musica.sh $P/final_voz.mp4 <musica.mp3> $P/final.mp4 <início_s> -6 0`.
9. **Conferir**: duração, volume (`ffmpeg -i final.mp4 -af ebur128=peak=true -f null -` ≈ −14 LUFS), uma folha de quadros.
   Gerar `final_envio.mp4` e mandar. Depois do "aprovado", rodar a skill /post.
