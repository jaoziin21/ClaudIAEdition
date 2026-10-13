#!/usr/bin/env python3
"""Gera a pasta skills/ do produto (ClaudIAEdition) a partir do motor do canal, em versão limpa e independente por skill."""
import json, os, re, shutil, sys
SRC = '/home/user/getsemani---canal-/getsemani-videos/engine'
AML = '/home/user/getsemani---canal-/.claude/skills/anime-motion-lab'
IMG = '/tmp/claude-0/-home-user/063bb3a9-aa90-5c57-a776-b32035416c1c/scratchpad/pag/img'
OUT = '/home/user/claudiaedition/skills'

if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)

def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(text.lstrip('\n'))

def cp(skill, rel, dst_rel=None):
    """copia SRC/rel para skills/<skill>/arquivos/<dst_rel> (vai para motor/ na instalação)"""
    d = os.path.join(OUT, skill, 'arquivos', dst_rel or rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy2(os.path.join(SRC, rel), d)

def img(skill, name, dst='exemplo.jpg'):
    os.makedirs(os.path.join(OUT, skill), exist_ok=True)
    shutil.copy2(os.path.join(IMG, name), os.path.join(OUT, skill, dst))

def skill_md(name, desc, body, hint=None):
    fm = f'---\nname: {name}\ndescription: {desc}\n' + (f'argument-hint: {hint}\n' if hint else '') + '---\n'
    return fm + body.lstrip('\n')

# ───────────────────────────── MOTOR (base) ─────────────────────────────
for f in ['render_lado.mjs', 'faixa.mjs', 'transcribe.mjs', 'transcribe_clips.mjs', 'alinha.py', 'musica.sh',
          'scene_lado.html', 'efeitos/_motor.js', 'efeitos/efeitos.json', 'efeitos/pacotes.json']:
    cp('motor', f)
pk = json.load(open(os.path.join(SRC, 'package.json'))); pk['name'] = 'editor-motor'
w(f'{OUT}/motor/arquivos/package.json', json.dumps(pk, indent=2, ensure_ascii=False) + '\n')
w(f'{OUT}/motor/arquivos/setup.sh', r'''
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
''')
os.chmod(f'{OUT}/motor/arquivos/setup.sh', 0o755)
os.makedirs(f'{OUT}/motor/arquivos/estilos', exist_ok=True); open(f'{OUT}/motor/arquivos/estilos/.gitkeep', 'w').close()

w(f'{OUT}/motor/SKILL.md', skill_md('motor', 'Motor de edição de vídeos curtos (base de todas as outras skills): prepara o computador, organiza o projeto, transcreve a voz com o texto certo, monta o fundo, renderiza a legenda, mistura a música e confere o vídeo final. Use junto com qualquer skill de legenda, efeito ou estilo de vídeo, ou quando o usuário pedir para instalar/configurar o editor.', r'''
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
8. **Música** (skill /musica ou arquivo do usuário): medir em que segundo a faixa já está tocando de verdade
   (`volumedetect` por segundo) e começar dali, sem fade-in:
   `bash musica.sh $P/final_voz.mp4 <musica.mp3> $P/final.mp4 <início_s> -6 0`.
9. **Conferir**: duração, volume (`ffmpeg -i final.mp4 -af ebur128=peak=true -f null -` ≈ −14 LUFS), uma folha de quadros.
   Gerar `final_envio.mp4` e mandar. Depois do "aprovado", rodar a skill /post.
''', '[o que fazer: instalar, conferir, ou o pedido de edição]'))

# ───────────────────────────── LEGENDAS ─────────────────────────────
LEG = {
 'sample-yellow': dict(nome='Sample Yellow', img='leg-sample-yellow-0.jpg',
   desc='Legenda "Sample Yellow": legenda de TV que chama atenção, amarela em itálico fino, palavra por palavra numa caixinha escura translúcida; imagem sonhadora com brilho, grão e luz. Boa para reflexão, fala de personagem e Shorts de GIF.',
   como='''- Roboto itálico fino amarelo, minúsculo, palavra por palavra no lugar final; a caixinha escura cresce junto com as palavras.
- `medeFundo`: caixa forte em fundo claro, fraca em fundo médio, nenhuma em fundo escuro. Separação RGB leve; palavra-chave = amarelo mais claro com um pulinho de brilho (use poucas).
- Imagem: brilho estourado, grão e vinheta; na cena, vazamentos de luz, clarão em cada corte e risco verde de glitch.
- Posição padrão: embaixo no centro (`x: 0.5, y: 0.86`), uma linha.
- Variação em 2 linhas ao lado do personagem (como se ele falasse): `"multilinha": true`, `"maxch": 56`, `"tamanho": 50`, cena `{"t":0,"x":0.36,"y":0.5,"maxw":0.56}` (ajuste o x para o lado livre).''',
   lado='{"estilo": "sample-yellow", "keywords": ["poucas"], "cenas": [{"t": 0, "x": 0.5, "y": 0.86}]}'),
 'legenda-dinamica': dict(nome='Legenda Dinâmica', estilo='dinamica', img='leg-legenda-dinamica-0.jpg',
   desc='Legenda "Dinâmica": serifa itálica elegante (Playfair) ao lado de quem fala, mudando de canto a cada frase; palavras surgem do escuro e saem em fumaça, palavra-chave vermelha com brilho; vídeo escuro com cara de Super 8. Boa para diálogo e cena dramática.',
   como='''- Playfair itálico minúsculo; palavras surgem do fundo e saem em fumaça; palavra-chave acende em vermelho com brilho.
- A legenda fica AO LADO de quem fala e varia de canto a cada cena (sup./inf., esq./dir., centro); nunca no rosto.
- Imagem escura (sombra) com grão e textura de Super 8.
- Mapeie os cortes de cena (`ffmpeg -i X -an -vf "fps=30,scale=480:-1,select='gt(scene,0.2)',metadata=print" -f null -`), veja um quadro de cada cena e escolha o espaço livre. Cena sem lugar bom: `{"t": ..., "nada": true}`.''',
   lado='{"estilo": "dinamica", "keywords": [...], "cenas": [{"t": 0, "x": 0.3, "y": 0.25, "maxw": 0.4}, {"t": 4.2, "x": 0.7, "y": 0.8}]}'),
 'legenda-3d-invisivel': dict(nome='3D Invisível', estilo='3d-invisivel', img='leg-legenda-3d-invisivel-0.jpg', extra=['estilos/reticula_manga.png', 'estilos/hachura_manga.png'],
   desc='Legenda "3D Invisível": uma palavra por vez no centro, letra grossa maiúscula (Montserrat Black) com relevo 3D, palavra-chave azul-gelo com linhas de impacto de mangá; imagem com luz quente e textura de mangá. Boa para frases curtas de impacto.',
   como='''- UMA palavra por vez no centro, Montserrat Black maiúscula off-white com relevo 3D profundo; letras sobem em sequência e saem em dissolve.
- Palavra-chave azul-gelo com linhas de impacto de mangá (escolha as 5–6 palavras mais fortes do vídeo).
- Imagem com luz quente e textura de mangá (traço de tinta, retícula e hachura) — já vem no filtro do estilo.
- Cenas: todas `x: 0.5, y: 0.5` (os cortes servem só para a palavra sumir no corte).''',
   lado='{"estilo": "3d-invisivel", "keywords": ["5 a 6 palavras fortes"], "cenas": [{"t": 0, "x": 0.5, "y": 0.5}]}'),
 'mistury': dict(nome='Mistury', img='leg-mistury-0.jpg',
   desc='Legenda "Mistury": cada frase vira um cartaz tipográfico novo, misturando fontes — palavra forte grande e colorida, apoio pequeno e remate em cursiva escrito na hora; a cor se ajusta ao fundo. Boa para versículo, citação e frase marcante.',
   como='''- Cada frase (até fim de frase ou corte; `maxch` 30) vira um CARTAZ: herói = palavra-chave da frase (ou a mais longa) grande numa fonte de destaque; apoio = conectores pequenos; remate = uma palavra forte em cursiva de pincel branca.
- 7 visuais que se alternam: `didone`, `condensada`, `gotica`, `romana`, `bebas`, `bloco`, `fina`. Para forçar um visual numa cena: `"look": "gotica"` na cena.
- `medeFundo`: em fundo claro o herói troca para cor escura e a sombra fica mais densa.
- Cada palavra só aparece quando é falada; o cartaz some inteiro no fim da frase. Varie os cantos, nunca no rosto.''',
   lado='{"estilo": "mistury", "keywords": ["UMA palavra forte por frase"], "cenas": [{"t": 0, "x": 0.5, "y": 0.4}]}'),
 'street': dict(nome='Street', img='leg-street-1.jpg',
   desc='Legenda "Street": legenda pequena que se escreve sílaba por sílaba, palavra-chave vermelha, palavras de grito piscando GIGANTES em letra gótica, colagem de painéis com outros momentos do próprio vídeo; imagem escura e contrastada. Boa para edit agressivo, anime e luta.',
   como='''- Legenda pequena (Arimo branco), frases curtas (`maxch` 24), no centro; palavra longa se escreve por sílabas; palavra-chave vermelha.
- **Gritos**: palavras da lista `"gritos"` (sem lista = palavras-chave) piscam GIGANTES na altura da imagem em gótica fina, alternando vermelho e branco com contorno. Máx. 1 grito a cada 2,5 s — escolha 4 a 8 no vídeo.
- **Colagem**: o motor tira quadros do próprio vídeo; nos cortes e nos gritos pipocam 1–3 painéis com outros momentos.
- Precisa do fim de cada palavra no `words.json` (o fluxo padrão já gera). Nos quadros de teste, inclua o quadro de cada grito (tempo da palavra + 0,05).''',
   lado='{"estilo": "street", "keywords": [...], "gritos": ["4 a 8 palavras de impacto"], "cenas": [{"t": 0, "x": 0.5, "y": 0.5}]}'),
 'rocks': dict(nome='Rocks', img='leg-rocks-0.jpg',
   desc='Legenda "Rocks": maiúsculas serifadas brancas com relevo cromado e brilho, num plano inclinado, em duas linhas encaixadas em escada, capitular gigante, risco de luz em cada palavra; vídeo com cara de fita VHS. Boa para épico e retrô.',
   como='''- Frases curtas (`maxch` 22) em VERSAL serifada (Tinos) branca com relevo cromado escuro e brilho, num plano inclinado.
- 2 linhas em escada; a palavra-chave (ou a mais longa) fica maior. Frase que começa com letra solta (A, E, O, É) vira capitular gigante.
- Cada palavra entra com risco de luz; fim da frase = corte seco. Vídeo VHS (macio, borda colorida, grão, varredura, tracking nos cortes).
- Posição: embaixo à esquerda (`x ≈ 0.32, y ≈ 0.76`), variando quando o espaço pedir.''',
   lado='{"estilo": "rocks", "keywords": [...], "cenas": [{"t": 0, "x": 0.32, "y": 0.76}]}'),
 'samplerocks': dict(nome='Samplerocks', img='leg-samplerocks-0.jpg',
   desc='Legenda "Samplerocks": layout inclinado do Rocks com letra sem serifa branca e palavras AMARELAS; cada palavra entra esticada da direita e encaixa; imagem limpa com grão. Boa para fala de personagem com visual limpo.',
   como='''- Versal Archivo 600 branca, 1–3 linhas curtas em escada, plano inclinado, sombra discreta.
- Palavras-chave AMARELAS; frase sem chave → última linha amarela.
- Cada palavra vem da direita esticada com rastro e encaixa; fim da frase = corte seco. Imagem limpa com grão fino.
- Posição: embaixo à esquerda (`x ≈ 0.33, y ≈ 0.76`).''',
   lado='{"estilo": "samplerocks", "keywords": ["1 a 2 por frase"], "cenas": [{"t": 0, "x": 0.33, "y": 0.76}]}'),
 'invisible': dict(nome='Invisible', img='leg-invisible-0.jpg',
   desc='Legenda "Invisible": a letra é feita da própria imagem do vídeo, como vidro, e pega sozinha as cores de cada cena; maiúscula grossa (Montserrat Black) no centro com relevo. Boa para visual estético e frases curtas.',
   como='''- O motor tira os quadros do vídeo em meia resolução (pasta `motor/quadros/`, refeita só se a faixa mudar) e desenha a face de cada letra com o quadro atual, deslocado como vidro.
- Relevo com extrusão translúcida, sombra longa e fio de luz na borda. Montserrat Black VERSAL no centro, frases curtas (`maxch` 18).
- Letras sobem em sequência; risco de luz atravessa a frase; palavra-chave com luz mais forte; saída em dissolve. Imagem limpa e viva.''',
   lado='{"estilo": "invisible", "keywords": ["poucas"], "cenas": [{"t": 0, "x": 0.5, "y": 0.5}]}'),
 'red-sharp': dict(nome='Red Sharp', img='leg-red-sharp-0.jpg',
   desc='Legenda "Red Sharp": legenda pequena serifada numa tarja preta e, nas frases de impacto, palavras VERMELHAS empilhadas com a última em itálico, com soco, tremida e vinheta vermelha; imagem escura. Boa para motivação e frase forte.',
   como='''- Legenda normal: serifada (Tinos) branca minúscula numa tarja preta que cresce palavra por palavra, no centro.
- Frase com palavra-chave = IMPACTO: palavras VERMELHAS empilhadas (máx. 4 linhas), Montserrat Black, a última em Bodoni itálico maior; soco + tremida + vinheta vermelha.
- Use POUCAS palavras-chave (2 a 4 no vídeo), nas frases mais fortes e curtas. Imagem escura e dessaturada com grão.''',
   lado='{"estilo": "red-sharp", "keywords": ["2 a 4 palavras das frases mais fortes"], "cenas": [{"t": 0, "x": 0.5, "y": 0.55}]}'),
}
for sk, d in LEG.items():
    est = d.get('estilo', sk)
    pre = json.load(open(os.path.join(SRC, 'estilos', est + '.json')))
    for k in ['origem', 'versao', 'posicao', 'dica_keywords']: pre.pop(k, None)
    w(f'{OUT}/{sk}/arquivos/estilos/{est}.json', json.dumps(pre, indent=1, ensure_ascii=False) + '\n')
    cp(sk, pre['filtro'])
    cp(sk, pre['cena'])
    for e in d.get('extra', []): cp(sk, e)
    img(sk, d['img'])
    w(f'{OUT}/{sk}/SKILL.md', skill_md(sk, d['desc'], f'''
# Legenda {d['nome']}

Requer a skill **motor** (pasta `motor/`). Siga o **fluxo padrão** do motor (`.claude/skills/motor/SKILL.md`) com o estilo `{est}`.
Exemplo do visual: `exemplo.jpg` nesta pasta.

## Como o estilo funciona (automático)
{d['como']}

## lado.json do projeto
```json
{d['lado']}
```
Escolha as palavras-chave lendo o roteiro: as que carregam o sentido da frase, nunca artigos ou conectores.

## Passos
1. Voz, texto e tempos das palavras: passos 1–3 do motor → `words.json`.
2. Fundo: `node faixa.mjs <vídeo de fundo> ../projetos/X` (usa o filtro deste estilo; com uma skill de efeito, usa os efeitos dela).
3. `lado.json` como acima → quadros de teste → mandar → ajustar → render → música → `final_envio.mp4`.
''', '[vídeo ou pasta do projeto / observações]'))

# ───────────────────────────── EFEITOS ─────────────────────────────
CAT = json.load(open(os.path.join(SRC, 'efeitos/efeitos.json')))
PAC = json.load(open(os.path.join(SRC, 'efeitos/pacotes.json')))
for p, d in PAC.items():
    sk = 'efeito-' + p
    for e in d['efeitos']:
        c = CAT[e]
        if c.get('video'): cp(sk, 'efeitos/video/' + c['video'])
        if c.get('tela'): cp(sk, 'efeitos/tela/' + c['tela'])
        for tx in c.get('texturas', []): cp(sk, os.path.normpath('efeitos/' + tx))
    img(sk, f'efe-{p}.jpg'); img(sk, f'efe-{p}-b.jpg', 'exemplo-detalhe.jpg')
    desc = re.sub(r'\s+—.*$', '', d['descricao'])
    w(f'{OUT}/{sk}/SKILL.md', skill_md(sk, f'Pacote de efeitos "{p}" ({" + ".join(d["efeitos"])}): {d["descricao"]}. Soma com qualquer legenda.', f'''
# Efeito {p}

{d['descricao']}.
Partes: {", ".join(f"`{e}`" for e in d['efeitos'])}. Requer a skill **motor** e uma skill de legenda.
Exemplo: `exemplo.jpg` (com legenda) e `exemplo-detalhe.jpg` (detalhe do efeito).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "{p}"`.
   Dá para somar outro pacote (`"pacote": ["{p}", "vhs"]`) ou efeitos avulsos (`"efeitos": [{{"nome": "particulas", "forca": 0.5}}]`).
2. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — os efeitos de IMAGEM do pacote substituem o filtro da legenda.
3. Render normal (`node render_lado.mjs ...`): os efeitos de TELA (luz, chuva, glitch...) entram sozinhos, atrás ou na frente da legenda.
4. Quadros de teste antes do vídeo inteiro.
''', '[legenda / vídeo ou pasta do projeto / observações]'))

w(f'{OUT}/efeitos/SKILL.md', skill_md('efeitos', 'Índice dos pacotes de efeitos instalados: mostra cada um com a imagem de referência, aplica um ou mais junto com qualquer legenda e também mistura duas legendas no mesmo vídeo.', '''
# Efeitos (índice)

1. Liste os pacotes instalados: pastas `.claude/skills/efeito-*` (cada uma tem `exemplo.jpg` e o SKILL.md com a descrição).
   Mostre ao usuário o nome, a descrição e a imagem de cada um.
2. Aplique o que ele escolher no `lado.json`: `"pacote": "sonho"` ou vários `"pacote": ["sonho", "vhs"]`;
   efeitos avulsos com força: `"efeitos": [{"nome": "flash"}, {"nome": "particulas", "forca": 0.5}]`
   (lista completa em `motor/efeitos/efeitos.json`; só funcionam os que têm os arquivos instalados).
3. Legenda com a fonte de outra: `"trocaFonte": "pirata-one"` (skill /fontes) — ex.: Sample Yellow com a letra gótica da Street.
4. Duas legendas no mesmo vídeo: a legenda principal em `"estilo"` e, na cena da frase de impacto, `"estilo": "red-sharp"`
   (as duas skills de legenda precisam estar instaladas).
5. Fundo com `node faixa.mjs`, quadros de teste, render. Detalhes na skill **motor**.
'''))

# ───────────────────────────── ESTILOS DE VÍDEO ─────────────────────────────
cp('video-gif', 'upscale/esrgan_np.py'); cp('video-gif', 'upscale/pesos/realesr-animevideov3.pth')
img('video-gif', 'vid-shorts-gif.jpg')
w(f'{OUT}/video-gif/SKILL.md', skill_md('video-gif', 'Estilo de vídeo "Shorts de GIF": um GIF em loop sem emenda, ampliado com IA para alta resolução, num telão no meio da tela vertical, com a legenda ao lado do personagem como se ele estivesse falando, narração e música. Use quando o usuário mandar um GIF ou pedir um vídeo "tipo GIF".', r'''
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
'''))

img('video-narracao', 'vid-verso.jpg')
w(f'{OUT}/video-narracao/SKILL.md', skill_md('video-narracao', 'Estilo de vídeo "Narração": uma voz narrando um roteiro sobre cenas de fundo tratadas, com zoom lento e a referência no topo (versículo, frase, curiosidade). Use para vídeos de reflexão, motivação ou curiosidade a partir de uma ideia.', '''
# Narração

Requer **motor** + uma legenda + **roteiro** e **voz** (ou o áudio do usuário).

1. Ideia → `/roteiro` → o usuário escolhe → `roteiro.txt`.
2. `/voz` gera a narração (ou o usuário manda) → passos 1–3 do motor → `words.json`.
3. Fundo: o vídeo que o usuário mandar (ou cenas que ele indicar). Mais curto que a voz → repetir com `-stream_loop`.
   `node faixa.mjs fundo.mp4 ../projetos/X`.
4. `lado.json` com a legenda escolhida e `"referencia"` no topo quando houver (sempre completa: "Salmos 46:10", nunca só o capítulo;
   com número no começo, use `"refNumeros": "cheios"`).
5. Abertura forte: a primeira frase precisa aparecer escrita já no primeiro segundo.
6. Quadros de teste → render → música → post.
'''))

img('video-fala', 'vid-lado.jpg')
w(f'{OUT}/video-fala/SKILL.md', skill_md('video-fala', 'Estilo de vídeo "Personagem falando": uma cena com o áudio original; transcreve, mapeia cada corte e coloca a legenda no espaço vazio ao lado de quem fala, nunca em cima do rosto. Use quando o usuário mandar um trecho de filme, anime, série ou entrevista para legendar.', '''
# Personagem falando

Requer **motor** + uma legenda (Dinâmica, Sample Yellow, Samplerocks e Mistury combinam bem).

1. Vídeo do usuário em `entrada/`. Partes separadas → juntar com `concat` (com áudio) e conferir as emendas.
2. Áudio original: `audio.wav` com loudnorm −14. Transcrever (passo 3 do motor). Sem roteiro: escreva `roteiro.txt` a partir da
   transcrição, corrigindo nomes e palavras erradas, e só então alinhe.
3. Cortes de cena: `ffmpeg -i X -an -vf "fps=30,scale=480:-1,select='gt(scene,0.2)',metadata=print" -f null -` → tempos.
   Veja um quadro de cada cena (no recorte do telão, com grade) e escolha o espaço livre AO LADO de quem fala.
4. `lado.json`: uma cena por corte `{"t", "x", "y", "maxw"}` ou `{"t", "nada": true}`. Palavra falada bem no corte caindo no rosto →
   adiante o `t` da cena e use `"separa": true`.
5. Fundo com `node faixa.mjs`, quadros de teste (inclua quadros logo depois dos cortes) → render (o áudio é o original) → post.
'''))

for f in ['render_legenda.mjs', 'scene_legenda.html', 'render_longo.sh', 'render_rapido.sh', 'legenda_rapida/compor.py',
          'legenda_rapida/sprites.mjs', 'transcreve_longo.sh']:
    cp('video-longo', f)
for f in ['limpa_audio.sh']:
    d = f'{OUT}/video-longo/arquivos/{f}'; shutil.copy2(f'/home/user/getsemani---canal-/getsemani-videos/projetos/2026-10-13-video-longo/{f}', d)
img('video-longo', 'vid-longo.jpg')
w(f'{OUT}/video-longo/SKILL.md', skill_md('video-longo', 'Estilo de vídeo "Vídeo longo" para o YouTube normal: horizontal 1920x1080, 10 a 30 minutos, fundo em loop, voz limpa, legenda palavra por palavra num canto livre, música baixa e capítulos na descrição; renderiza em partes paralelas. Use quando o usuário pedir vídeo longo, horizontal ou para o YouTube normal.', r'''
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
'''))

for f in ['aesthetic/prepara.py', 'aesthetic/README.md', 'scene_aesthetic.html', 'render_aesthetic.mjs']:
    cp('aesthetic', f)
w(f'{OUT}/aesthetic/SKILL.md', skill_md('aesthetic', 'Edição "Aesthetic": vídeo em tela cheia feito de imagens paradas que ganham vida — quadrinhos com borda de raio sobre estrelas, zoom, giro, personagem em camadas, cortes na batida da música, inversão nas batidas fortes e texto palavra por palavra. Use quando o usuário mandar imagens e quiser um edit cortado na batida.', r'''
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
'''))

# anime-motion-lab (edit com música a partir de um nome)
dst = f'{OUT}/edit-musica'
shutil.copytree(AML, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
s = open(f'{dst}/SKILL.md').read()
s = s.replace('Projetos neste repositório: `getsemani-videos/projetos/AAAA-MM-DD-<nome>/`.', 'Projetos: `projetos/AAAA-MM-DD-<nome>/` na pasta do canal.')
s = s.replace('P=getsemani-videos/projetos/$(date +%F)-<nome>', 'P=projetos/$(date +%F)-<nome>')
s = s.replace('name: anime-motion-lab', 'name: edit-musica', 1)
open(f'{dst}/SKILL.md', 'w').write(s)
img('edit-musica', 'vid-edit-musica.jpg')

# ───────────────────────────── ROTEIRO / POST / COMEÇAR / VOZ ─────────────────────────────
w(f'{OUT}/roteiro/SKILL.md', skill_md('roteiro', 'Sistema de roteiro para vídeos curtos (Reels, TikTok, Shorts) de qualquer nicho: a partir da ideia do usuário, entrega 3 propostas com 3 ganchos cada, 110–135 palavras, linguagem humana e sem cara de texto de IA. Use sempre que o usuário pedir roteiro, ideia de vídeo, gancho, texto para narração ou "próximo vídeo".', '''
# Roteiro

Antes de escrever: leia `canal.md` (nicho, público, tom, fonte de conteúdo) e `regras.md`, e os roteiros já usados
(`roteiros/*.md` e o `roteiro.txt` de cada pasta em `projetos/`) para não repetir tema, abertura, personagem ou conclusão.
Registre cada roteiro novo em `roteiros/AAAA-MM-DD-titulo.md` com o que o usuário aprovou ou rejeitou.

## Sua função
Você é o roteirista do canal. Transforme a ideia do usuário em vídeos que façam a pessoa parar de rolar a tela, se identificar
e sair com algo que valha a pena. Escreva como alguém que entende o assunto e o público, não como uma IA tentando emocionar.

## Voz
Português brasileiro falado, frases que alguém diria numa conversa, palavras comuns, cenas concretas. Pausas onde forem naturais
para a narração; não picote tudo em frases curtas para fabricar emoção. Algumas frases podem ser simples e diretas.

## Comece pela vida real
Antes de escrever, escolha uma situação específica do mundo do canal: uma cena, um conflito, um detalhe pouco lembrado da história,
do personagem, do jogo, do atleta, da passagem. Mostre o que isso significa na prática, sem inventar drama.

## Gancho
Os 2 primeiros segundos dão o motivo para ficar. Nada de saudação, "você precisa ouvir isso", "3 coisas que...", "você sabia que...".
Abra com uma situação reconhecível, uma contradição, uma pergunta que a pessoa teria vergonha de fazer, o momento menos lembrado
de uma história conhecida, um fato que muda o jeito de ver o assunto. Sempre 3 opções de gancho por roteiro; marque a escolhida.
Não prometa o que o vídeo não entrega.

## Estrutura
45–60 s, 110–135 palavras (ajuste ao que o `canal.md` e o `regras.md` disserem). Uma base possível: abertura → desenvolvimento →
virada de compreensão → conclusão. É ferramenta, não fórmula. O fim pode "puxar" o começo para o vídeo rodar em loop.
Nem sempre termine com frase de efeito: às vezes uma pergunta, um gesto concreto ou uma verdade simples funciona melhor.

## Fonte do conteúdo
Use a fonte do canal (Bíblia, história do anime, carreira do atleta, ciência, filosofia...) quando ela acrescentar algo verdadeiro.
Confira fatos, falas e referências. Não invente citação, versículo, estatística ou fala de personagem. Paráfrase não é citação.
Referência sempre completa (ex.: "1 Samuel 16:1-13", "Naruto, ep. 133").

## Proibido soar como IA
Evite frases feitas do nicho, construções "não é X, é Y" só para impacto, três frases curtas seguidas, reticências demais,
pergunta retórica em todo parágrafo, listas de três adjetivos, conclusões com cara de slogan, sofrimento inventado.

## Variedade e retenção
Alterne temas, personagens, estruturas e tons entre vídeos. Cada frase acrescenta algo: um detalhe, uma consequência, uma dúvida.
Sem enrolação e sem esconder informação simples para esticar o vídeo.

## Entrega (3 propostas diferentes, salvo pedido diferente)
1. Título de trabalho. 2. Ideia central (1 frase). 3. Três ganchos, com o escolhido marcado. 4. Roteiro completo em texto corrido,
pronto para narrar. 5. Referência/fonte (ou "sem referência direta"). 6. Direção de narração (tom). 7. Pergunta para comentários
ou convite para compartilhar, só quando fizer sentido.

## Teste final
O começo faria alguém parar? É específico ou genérico? Soa natural em voz alta? Cada trecho acrescenta? Tem frase com cara de IA?
Se o roteiro servir para qualquer canal, ainda não está pronto: reescreva.
'''))

w(f'{OUT}/post/SKILL.md', skill_md('post', 'Gera o texto de postagem de um vídeo aprovado: título do YouTube Shorts, legenda do Instagram/TikTok, descrição do YouTube e tags, seguindo o que funciona para viralizar. Use quando o usuário aprovar o vídeo ou pedir título, legenda, descrição, hashtags ou tags.', '''
# Post

Quando o usuário aprovar o vídeo, mande JUNTO com o vídeo final, sem ele pedir, e salve em `projetos/.../post.md`.
Sempre UMA versão de cada item, a melhor (não dê opções).

1. **Título (YouTube Shorts)**: 40–70 caracteres, palavra-chave de busca NO COMEÇO, promessa ou emoção clara, sem hashtag e sem clickbait.
2. **Legenda (Instagram/TikTok)**: o mesmo título + 1 frase pedindo para mandar a alguém ("Manda pra alguém que...") + 3–5 hashtags específicas.
3. **Descrição (YouTube)**: palavra-chave e referência nos primeiros 100 caracteres, 2–3 frases curtas, chamada para comentar,
   crédito da música se a licença pedir, 3–5 hashtags no fim (pode ter #shorts). Vídeo longo: capítulos (00:00 ...).
4. **Tags (YouTube)**: 5–8, a primeira é a palavra-chave exata do título.

## O que mais pesa (lembrar o usuário quando fizer sentido)
- O vídeo pesa mais que título e tags: gancho nos 2 primeiros segundos, legenda aparecendo já no 1º segundo, 25–45 s, fim que emenda no começo.
- No Reels o sinal mais forte é COMPARTILHAR por DM e SALVAR. Nunca repetir a mesma legenda em dois vídeos.
- Horários (Brasil): 18h30–20h em dias úteis; testar 7h–8h30 e 12h–13h30; domingo à noite costuma ser forte. Até 3 posts por dia,
  com 4 h entre eles. Medir as 2 primeiras horas de cada post e repetir o tipo de gancho que mais segurou.
'''))

w(f'{OUT}/comecar/SKILL.md', skill_md('comecar', 'Configura o canal do usuário a partir da ideia dele ("quero um canal de X com Y"): entrevista curta, cria canal.md e regras.md, sugere legenda, efeitos, formato de vídeo e voz, e instala o motor. Use na primeira conversa ou quando o usuário quiser mudar a cara do canal.', '''
# Começar

1. Pergunte, em poucas mensagens (só o que ele ainda não disse):
   - Sobre o que é o canal e para quem (nicho e público). Exemplo de resposta: "motivação com cenas de anime, voz grave".
   - Fonte do conteúdo (Bíblia, animes, futebol, história, ciência...) e o que ele NÃO quer.
   - Tom (íntimo, épico, sombrio, engraçado, direto) e duração preferida.
   - Voz: própria, ElevenLabs ou Fish Audio (skill /voz). Fundo: GIFs/cenas que ele manda ou busca por nome (/edit-musica).
   - Redes e horários em que pretende postar.
2. Sugira o pacote inicial com o motivo de cada escolha: 1 legenda, 1 efeito (opcional) e 1 estilo de vídeo, olhando as skills
   instaladas (`.claude/skills/`) e o `exemplo.jpg` de cada uma. Exemplos:
   cristão → narração ou Shorts de GIF + Sample Yellow; motivação → Red Sharp + efeito sombrio; anime → edit com música + Street;
   futebol → edit com música + 3D Invisível.
3. Escreva `canal.md` (nicho, público, tom, fonte, o que evitar, legenda/efeito/formato padrão, voz, duração, horários) e
   `regras.md` (vazio no começo, com o título "O que o usuário aprovou e rejeitou").
4. Rode `bash motor/setup.sh` e resolva o que faltar.
5. Proponha o primeiro vídeo: chame o fluxo de `/roteiro` com 3 ideias de tema para ele escolher.
'''))

w(f'{OUT}/voz/SKILL.md', skill_md('voz', 'Gera a narração do roteiro aprovado: pelo ElevenLabs conectado ao Claude (pede ao usuário para conectar na primeira vez) ou com o passo a passo do Fish Audio (gratuito, vozes de personagens), ou usa a voz gravada do usuário. Use quando chegar a hora de narrar um roteiro ou o usuário pedir voz/áudio.', '''
# Voz

## Opção 1 — ElevenLabs (o Claude gera)
1. Se as ferramentas do ElevenLabs não estiverem disponíveis nesta conversa, peça ao usuário para conectar:
   claude.ai → Configurações → Conectores → ElevenLabs (entrar com a conta dele), e abrir uma conversa nova depois.
2. Liste as vozes da conta, escolha a que combina com o `canal.md` (ou a que ele já aprovou em `regras.md`) e diga qual escolheu.
3. Gere o roteiro aprovado com **`generations_count: 1` — SEMPRE UMA voz por pedido, nunca 4** (cada variação gasta crédito do usuário).
   Se der "Free Tier disabled", pare: monte o flow com a voz e o texto, mande o link, o usuário gera no site e manda o mp3. Texto longo → em 2 partes, cortando em fim de frase. Baixe para `projetos/.../voz_parte1.mp3`, `voz_parte2.mp3`.
4. Siga o passo 1 do motor (juntar partes e normalizar). Registre a voz aprovada em `regras.md`.

## Opção 2 — Fish Audio (gratuito, o usuário gera)
Passe este passo a passo:
1. Criar a conta em fish.audio (navegador ou app).
2. Procurar uma voz pronta na biblioteca (nome do personagem ou estilo, ex.: "narrador grave") e ouvir as amostras —
   ou criar uma voz nova enviando um áudio (MP3/WAV/M4A, uma pessoa falando, sem música e sem eco; 15 s funcionam, 1–2 min ficam melhores).
3. Na tela de texto para fala: escolher a voz, colar o roteiro e gerar. Dá para pôr emoção no texto, como (calmo) ou (animado).
4. Ouvir; se alguma palavra sair estranha, mudar a pontuação ou gerar de novo só aquele trecho.
5. Baixar o áudio (pode ser em partes) e mandar no chat junto com o roteiro.

## Opção 3 — voz do usuário
Gravar no celular em lugar silencioso, a 20 cm da boca, e mandar o arquivo. Se tiver chiado: `afftdn` + `loudnorm` (ver video-longo/limpa_audio.sh).
'''))


w(f'{OUT}/buscar-midia/SKILL.md', skill_md('buscar-midia', 'Busca na internet GIFs, fotos, animações e clipes (anime, filmes, esportes, natureza, qualquer assunto) para o fundo dos vídeos, prioriza fontes gratuitas, mostra opções, baixa a escolhida e registra a fonte. Use SEMPRE que um vídeo precisar de fundo e o usuário não mandar o arquivo, ou quando ele pedir "acha um GIF/imagem/cena de...".', r"""
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
"""))

os.makedirs(f'{OUT}/fontes', exist_ok=True)
shutil.copy2('/tmp/claude-0/-home-user/063bb3a9-aa90-5c57-a776-b32035416c1c/scratchpad/mostruario.jpg', f'{OUT}/fontes/mostruario.jpg')
w(f'{OUT}/fontes/SKILL.md', skill_md('fontes', 'Troca a fonte de qualquer legenda por outra (37 fontes prontas ou qualquer fonte do Google Fonts): mostra o mostruário, aplica no projeto e testa. Use quando o usuário pedir outra fonte, letra diferente, "muda a fonte", ou quiser ver as fontes disponíveis.', r"""
# Fontes

Requer **motor** + a skill da legenda. Mostruário com as 37 fontes instaladas: `mostruario.jpg` nesta pasta (mande ao usuário).

## Trocar a fonte principal da legenda
No `lado.json` do projeto: `"trocaFonte": "bebas-neue"` (o nome em amarelo do mostruário). Quadros de teste, e pronto.
O motor usa o mesmo peso e estilo da original quando a fonte nova tiver; se não tiver, o mais perto.

## Trocar uma parte específica (legendas com mais de uma fonte)
`"trocaFonte": {"GRT": "pirata-one", "CAP": "dm-sans"}` — família da cena → fonte nova:

| Legenda | Famílias (fonte original) |
|---|---|
| Sample Yellow | `RB` (roboto itálico) |
| Dinâmica | `PF` (playfair-display itálico) |
| Street | `CAP` legenda (arimo) · `GRT` gritos gigantes (grenze-gotisch) |
| Rocks | `TN` (tinos) |
| Samplerocks | `AR` (archivo) |
| Invisible | `MONB` (montserrat 900) |
| Red Sharp | `TN` legenda (tinos) · `MONB` impacto (montserrat 900) · `BODI` última palavra (bodoni-moda itálico) |
| Mistury | `DID` `GOT` `ROM` `CON` `BEB` `MON` `BOD` (heróis) · `SCR` `MRD` `GV` (cursivas) |
| 3D Invisível | usa a chave própria `"fonte"`: montserrat-black, outfit, urbanist, montserrat, lexend… |

## Fonte nova (qualquer uma do Google Fonts)
1. Nome em minúsculas com hífen (ex.: "Anton" → `anton`, "Permanent Marker" → `permanent-marker`).
2. `cd motor && npm install @fontsource/<nome>` (precisa de internet; se bloquear, liberar `registry.npmjs.org`).
3. `"trocaFonte": "<nome>"` e quadros de teste. Para o mostruário mostrar a nova, gere a prévia com uma frase do roteiro.

## Dicas
- Legenda pequena e longa: fonte legível (dm-sans, manrope, archivo, roboto). Palavra única gigante: bebas-neue, luckiest-guy, bangers, anton.
- Cursivas (great-vibes, mr-dafoe, yellowtail) só em frases curtas.
- Guarde a escolha aprovada em `regras.md` para os próximos vídeos.
"""))

# ───────────────────────────── limpeza de comentários pessoais ─────────────────────────────
FIX = [('(pedido dele, 13/out: "sempre começa com ela tocando já";', '(padrão: a música já está tocando no começo do vídeo;'),
       ('com o TEXTO dele', 'com o TEXTO do roteiro'), ('(o texto dele manda,', '(o texto do roteiro manda,'),
       ('(o texto dele)', '(o texto do roteiro)'), ('(pedido dele, Mateus 11:28)', ''), ('de dentro de engine/', 'de dentro de motor/'),
       ('## O que pedir para ele mandar', '## O que pedir para o usuário mandar'),
       ('dos vídeos dele nas trocas de cena (o teste foi feito assim, com o Inimigos)', 'dos vídeos do usuário nas trocas de cena'),
       ('(rodar dentro de engine/)', '(rodar dentro de motor/)'), ('(dentro de engine/)', '(dentro de motor/)'),
       ('Davi ungido, 13/out.', '')]
for root, _, files in os.walk(OUT):
    for f in files:
        if f.endswith(('.mjs', '.sh', '.py', '.md', '.html', '.js')):
            fp = os.path.join(root, f); t = open(fp).read(); t2 = t
            for a, b in FIX: t2 = t2.replace(a, b)
            if t2 != t: open(fp, 'w').write(t2)
print('ok')
