---
name: edit-musica
description: >-
  Pesquisador de assets + animador 2D/2.5D + editor de edits sincronizados com música, usando SÓ material que já
  existe (artes oficiais, painéis de mangá, pinturas, quadros e clipes existentes, arquivos do usuário) — NUNCA gera
  ilustração/personagem/cena nova por IA. Digite um nome ("Goku", "Itachi", "Jesus", "Neymar") e ele interpreta o
  sujeito, faz buscas reais por categoria de plano, baixa o que é legitimamente acessível, faz curadoria, recorta
  camadas (parallax 2.5D), anima com câmera/keyframes/efeitos (zoom, shake, glitch, flash, RGB split, glow, light
  sweep, motion blur, speed ramp), sincroniza com o beat e renderiza MP4 validado + manifesto de fontes. Use para:
  "faz um edit do Goku", "edit rap geek", "AMV", "anime essa imagem/desenho sem criar outra", "animação do Itachi
  com imagens da internet", "artes de Jesus em animação cinematográfica", "cenas de anime que combinem com essa
  música", "parallax", "transforme essa imagem estática em cena animada", "make an anime edit", "animate this
  drawing", "find existing art and sync to the beat", "2.5D parallax edit".
argument-hint: "[nome/tema] [música?] [referência?] [estilo: rap|cinematico|contemplativo] [só mangá?]"
---

# Anime Motion Lab — nome → edit, só com material existente

Fale com o usuário em português do Brasil (entende pedidos em PT e EN). Execute o fluxo; não devolva só recomendações.
Pergunte apenas o essencial (uma pergunta objetiva); o resto decida com bom senso e registre a decisão.

`SKILL_DIR` = pasta deste arquivo (no repositório: `.claude/skills/anime-motion-lab`; global:
`~/.claude/skills/anime-motion-lab`). CLI única: `python3 $SKILL_DIR/scripts/aml.py <comando>` (`-h` lista tudo).
Projetos: `projetos/AAAA-MM-DD-<nome>/` na pasta do canal.

## Regras que não se negociam
1. **Nada de IA generativa para conteúdo visual**: proibido Stable Diffusion, Midjourney, DALL-E, Canva generate-image,
   Higgsfield, preenchimento generativo, upscaler que inventa detalhe. Só transformar o que existe (recorte, máscara,
   camadas, câmera, deformação moderada, cor, luz, efeitos procedurais, composição). O fundo atrás do recorte é
   preenchido com **desfoque da própria imagem**, e o parallax é limitado para não expor esse preenchimento.
2. **Não fingir movimento que a imagem não tem**. Luta, corpo inteiro e expressão facial vêm de um CLIPE/GIF/sprite
   existente; uma imagem parada ganha câmera, profundidade, luz e deformação sutil (respirar, balançar, cabelo).
   Pessoa real (atleta etc.): sem deformar rosto/corpo, só câmera e efeitos.
3. **Pesquisa honesta**: só se diz que pesquisou o que foi pesquisado. Sem URL, autor, licença ou resolução inventados.
   Host bloqueado, login, paywall ou "não sou robô" → registrar no manifesto e seguir por outra fonte. Nunca contornar.
4. **Fontes e direitos**: tudo vai para `metadata/manifest.json` + `metadata/FONTES.md`. Avisar sempre que o material é
   protegido (anime, mangá, filme, foto de jogo): o mangá TAMBÉM tem direitos, só tem menos chance de cair no Content ID
   do YouTube do que o anime (que compara vídeo e áudio). Espelhar/recortar não engana o Content ID.
5. **Sem música → sem áudio inventado**: o vídeo sai mudo, com ritmo visual numa grade virtual, e oferece sincronizar
   quando ele mandar a música.
6. Não declarar pronto sem `qa` aprovado. Mandar folha de quadros antes do render longo quando der.

## Fluxo "digite o nome" (padrão)
```bash
A="python3 $SKILL_DIR/scripts/aml.py"; P=projetos/$(date +%F)-<nome>
$A env                                   # 1x por sessão: o que existe de verdade (libs, GPU, quais fontes respondem)
$A auto $P "Goku" --contexto "<pedido dele em texto>" [--midia manga] [--audio musica.mp3] [--referencia ref.mp4]
```
`auto` faz: entidade (`metadata/subject.json`: nome canônico, franquia, aliases, cenas famosas, o que evitar,
preset) → ~18 buscas por CATEGORIA DE PLANO (close, pose, ação, transformação, aberto, silhueta, contemplativo,
clipes, cenas famosas) em toda fonte que responder → pontua títulos/canais (penaliza fan-art, IA, reação, gameplay,
cosplay e edit de terceiros; bonifica oficial/raw/4K) → baixa variado (máx. N quadros por vídeo) → filtro medido
(mangá P&B/tingido pela dispersão de matiz, nitidez, quadro preto) → **folha numerada `metadata/revisao.jpg`**.

**Curadoria (obrigatória, você faz)**: abra a folha com Read e reprove o que não é o sujeito certo (outro personagem,
"Goku Black" no lugar do Goku, capa com texto grande, rascunho, colorido quando pediram só mangá, duplicata):
`$A reprovar $P 3 7 12` / `$A aprovar $P 5` (`$A revisar $P --todos` mostra todos). Não envolva o usuário nisso,
a menos que ele queira participar.

Depois: `$A montar $P --previa` → abra `output/previa_quadros.jpg` (1 quadro por plano) → ajuste → `$A montar $P`
(render + QA + FONTES) → `python3 -c` com `render.export_share` (ou `ffmpeg`) para a cópia ≤ 28 MB do chat.
Mande vídeo + resumo das fontes + limitações encontradas.

Nome fora da tabela (`confirmar: true`): confirme quem é com **WebSearch** (franquia/tipo) e rode de novo com
`--franquia` e `--tipo`. Ambíguo de verdade (ex.: "Ronaldo"): use o contexto; só pergunte se mudar o resultado.

## Fontes: o que usar e como
| fonte | como | observação |
|---|---|---|
| YouTube | `search_youtube` (página de resultados real) → capa + quadros automáticos `maxres1..3` (1280x720, i.ytimg.com) | ótimo para cenas/painéis; baixar o VÍDEO costuma pedir login → não contornar |
| Wikimedia Commons, Openverse, Internet Archive, Met, Art Institute | APIs em `search.py` (licença vem da API) | melhor para Jesus/arte clássica (domínio público) |
| Google Images, Pinterest, Bing, ArtStation, Pixiv, DeviantArt, sites oficiais | **WebSearch/WebFetch** do agente para DESCOBRIR; achar a página original; `$A candidato` + `$A baixar` | o download só funciona se a rede liberar o host |
| arquivos do usuário / Google Drive | `$A add` (copia; original intacto) | preferir quando ele mandar |
`$A env` mostra o que responde; bloqueado → diga qual host liberar (ver `references/rede-e-dependencias.md`).

## Técnica por asset (o `plan` decide; dá para forçar no `edit.json`)
- **Clipe/GIF/sprite existente** (`technique: clip`): `$A clipes $P <id>` acha trechos dentro de uma cena (sem corte no
  meio, mais ação ou mais calmo), speed ramp `[[0,1.4],[0.35,0.45],[1,1]]`, câmera leve, cor e impacto por cima.
- **Imagem com recorte bom** (`parallax`): fundo e personagem em camadas, câmera com profundidade, `orbit` mostra a
  paralaxe; personagem respira/balança e o contorno (cabelo/roupa) tremula de leve; `$A parte` cria partes (ex.:
  cabeça) para puppet com pivô.
- **Imagem sem recorte útil** (`camera`): só câmera + luz + efeitos. Zoom limitado pela resolução da fonte (`zmax`).
- Plano aberto de imagem larga na vertical: `fill: fit_blur` (imagem inteira sobre cópia desfocada dela mesma).

## Direção (presets) — `references/estetica.md`
- `rap` (rap geek/AMV): 1–4 batidas por plano conforme a energia, flash/zoom-burst na entrada de seção, whip/glitch nas
  batidas fortes, zoom de impacto + shake + RGB split nos impactos, pausa dramática antes do clímax, negativo (mangá).
- `cinematico`: 2–8 batidas, dissolve/light leak, impactos contidos, light sweep, letterbox no 16:9.
- `contemplativo` (Jesus/reverente): 8 batidas+, dissolve/dip, push-in lento, glow, sem shake.
- Mangá (`--midia manga`): cor `manga_tinta` (P&B de tinta), flash vermelho no clímax, negativo nas batidas fortes.
- Referência do usuário: `$A referencia <video> --proj $P` mede duração de plano, cortes/min, cortes na batida,
  flashes, P&B, silhuetas e movimento → o `plan` adota o ritmo/cor sugeridos (extrai a linguagem, não copia a sequência).

## Música
`$A audio $P musica.mp3` (copia o original em `audio/`, WAV de trabalho sem alterar o volume) → BPM (autocorrelação +
batidas por programação dinâmica, refinadas ±50 ms), tempos fortes, impactos (subida de grave), energia, seções
(intro/verso/build/refrão/clímax/pausa/final), subidas. BPM pouco confiável → cortes pelos impactos/onsets. Áudio
original preservado; `audio_fade_out` só no fim.

## Comandos (resumo)
`env` · `init` · `add` · `consultas NOME` · `buscar P "q"` · `candidato` · `baixar` · `auto` · `revisar` · `aprovar` ·
`reprovar` · `prep` · `parte` · `spritesheet` · `clipes` · `quadros` · `audio` · `referencia` · `plano` · `previa`
(`--video` = MP4 meia resolução) · `render` (`--gpu` usa NVENC se existir; senão CPU) · `qa` · `fontes` · `montar` ·
`animar IMAGEM` (anima uma imagem só: `--camera orbit --efeitos glow,light_sweep --impactos 1.5,3`).
Formato do `edit.json` e receitas: `references/receitas-edit-json.md`. Técnicas: `references/tecnicas-animacao.md`.
Pesquisa: `references/pesquisa-fontes.md`.

## Qualidade (o `qa` checa; não entregar reprovado)
H.264 yuv420p, resolução/duração do plano, A/V sincronizados (±0,1 s), decodifica sem erro, sem preto inesperado
(blackdetect fora de dip/fade), **sem salto de movimento fora dos cortes** (pico isolado ou câmera travada que
dispara), aviso de plano parado demais ("cara de slide"), loudness, folha `output/folha_qa.jpg`, avisos de direitos.
Vertical 1080x1920 (TikTok/Reels/Shorts) ou 1920x1080 (YouTube), 30 fps, CRF 18 limitado a 20 Mbps.

## Limitações conhecidas deste ambiente (registrar quando aparecerem)
- Rede "Custom": Google/Pinterest/Commons/Archive/ArtStation/sites de mangá respondem 403; YouTube e i.ytimg.com
  funcionam. Download de vídeo do YouTube pede login (não contornado) → clipes só de arquivos do usuário/Drive.
- Sem GPU: render em CPU, ~4 quadros/s em 1080x1920 com 4 núcleos (20 s ≈ 3 min). `previa` é ~4x mais rápida.
- Recorte: modelo local `isnet-anime` (rembg). Outros modelos baixam no 1º uso se a rede deixar.
