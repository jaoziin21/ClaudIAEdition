# Skills — catálogo

Cada pasta aqui é uma skill independente para o Claude Code. Você pode instalar todas ou só as que quiser.
O **motor** é a base: vai junto automaticamente.

## Como instalar

**Pelo Claude Code (mais fácil):** abra o Claude Code na pasta do seu canal e peça:
> Instale as skills sample-yellow e video-gif do ClaudIA Edition nesta pasta.

**Pelo terminal:**
```bash
# 1. baixe este repositório (botão "Code" → "Download ZIP") e descompacte
# 2. instale na pasta do seu canal (o motor vai junto):
bash skills/instalar.sh ~/meu-canal sample-yellow efeito-vhs video-gif
#    sem nomes = instala todas:
bash skills/instalar.sh ~/meu-canal
# 3. prepare o motor uma vez:
bash ~/meu-canal/motor/setup.sh
```
No Windows, rode pelo **Git Bash** ou pelo **WSL**, ou peça ao Claude Code para instalar.

**Quero só uma, sem instalador:** copie a pasta da skill para `meu-canal/.claude/skills/` e o conteúdo da pasta `arquivos/`
dela para `meu-canal/motor/` (faça o mesmo com a skill `motor`).

## O que você precisa
- Claude Code com plano pago (Pro ou superior), no computador ou na nuvem.
- Node.js 20+, Python 3.10+ e ffmpeg (o `setup.sh` avisa o que falta; na nuvem já vem quase tudo).
- Para a voz: conta no ElevenLabs ou no Fish Audio (gratuito), ou a sua voz gravada.

## Junte do seu jeito (legenda + fonte + efeitos)
Tudo se combina. Peça em português, do seu jeito:
- **Legenda + fonte de outra:** "Faz com a /sample-yellow, só que com a fonte gótica da Street (pirata-one)". A legenda continua
  baixinha, com a caixinha e a animação da Sample Yellow; só a letra muda. Mostruário das fontes: `fontes/mostruario.jpg`.
- **Vários efeitos juntos:** "/red-sharp com /efeito-filme-antigo e /efeito-vhs". Os efeitos se somam, na ordem pedida.
- **Duas legendas no mesmo vídeo:** Sample Yellow no vídeo todo e Red Sharp só na frase de impacto.
- São mais de 40 mil combinações: 9 legendas × 38 opções de fonte × qualquer mistura dos 7 efeitos.

Por dentro (no `lado.json` do projeto): `"estilo": "sample-yellow", "trocaFonte": "pirata-one", "pacote": ["cinema", "sonho"]`.

## Como cada skill é organizada
```
nome-da-skill/
  SKILL.md        instruções que o Claude segue (vira o comando /nome-da-skill)
  exemplo.jpg     como fica (nas visuais)
  arquivos/       arquivos do motor que esta skill acrescenta (vão para motor/)
```

## Base (obrigatória)

| | Skill | Comando | O que faz | Precisa de |
|---|---|---|---|---|
|  | `motor` | `—` | O motor de edição que todas as outras usam: instala o que precisa, junta e normaliza a voz, acha o tempo de cada palavra usando o seu texto, monta o fundo, renderiza a legenda, mistura a música e confere o vídeo final. | Node.js 20+, Python 3.10+, ffmpeg |

## Começo, roteiro, voz e post

| | Skill | Comando | O que faz | Precisa de |
|---|---|---|---|---|
|  | `comecar` | `/comecar` | Você conta a ideia do canal ("quero um canal de motivação com cenas de anime"). O Claude faz poucas perguntas, cria o perfil do canal e sugere legenda, efeito, formato e voz. | — |
|  | `roteiro` | `/roteiro` | A partir de um tema, entrega 3 roteiros com 3 ganchos cada, de 45 a 60 segundos, com linguagem de gente e sem cara de texto de IA. | — |
|  | `voz` | `/voz` | Gera a narração pelo ElevenLabs conectado ao Claude, ou passa o passo a passo do Fish Audio (gratuito, vozes de personagens), ou usa a sua voz gravada. | conta no ElevenLabs ou Fish Audio |
|  | `buscar-midia` | `/buscar-midia` | Procura GIFs, fotos, animações e cenas na internet (Pixabay, Pexels, Wikimedia, GIPHY, YouTube...), mostra as opções, baixa a escolhida e anota a fonte. Diz quais domínios liberar se a rede bloquear. | acesso à internet |
|  | `post` | `/post` | Quando o vídeo é aprovado, entrega título, legenda do Instagram/TikTok, descrição e tags do YouTube, além de horários para postar. | — |

## Legendas

| | Skill | Comando | O que faz | Precisa de |
|---|---|---|---|---|
| <img src="sample-yellow/exemplo.jpg" width="160"> | `sample-yellow` | `/sample-yellow` | Legenda de TV amarela em itálico, palavra por palavra numa caixinha escura. Embaixo ou em 2 linhas ao lado do personagem. | motor |
| <img src="legenda-dinamica/exemplo.jpg" width="160"> | `legenda-dinamica` | `/legenda-dinamica` | Serifa itálica elegante ao lado de quem fala, mudando de canto; palavra-chave vermelha; vídeo escuro com cara de filme. | motor |
| <img src="legenda-3d-invisivel/exemplo.jpg" width="160"> | `legenda-3d-invisivel` | `/legenda-3d-invisivel` | Uma palavra por vez no centro, maiúscula grossa com relevo 3D; palavra-chave azul-gelo; textura de mangá. | motor |
| <img src="mistury/exemplo.jpg" width="160"> | `mistury` | `/mistury` | Cada frase vira um cartaz com fontes misturadas: palavra forte grande, apoio pequeno e cursiva escrita na hora. | motor |
| <img src="street/exemplo.jpg" width="160"> | `street` | `/street` | Legenda pequena sílaba por sílaba e gritos GIGANTES em letra gótica, com colagem de outros momentos do vídeo. | motor |
| <img src="rocks/exemplo.jpg" width="160"> | `rocks` | `/rocks` | Maiúsculas serifadas cromadas num plano inclinado, em escada, com capitular gigante e cara de VHS. | motor |
| <img src="samplerocks/exemplo.jpg" width="160"> | `samplerocks` | `/samplerocks` | O layout inclinado do Rocks com letra sem serifa branca e palavras amarelas que entram esticadas. | motor |
| <img src="invisible/exemplo.jpg" width="160"> | `invisible` | `/invisible` | A letra é feita da própria imagem do vídeo, como vidro, e pega as cores de cada cena. | motor |
| <img src="red-sharp/exemplo.jpg" width="160"> | `red-sharp` | `/red-sharp` | Legenda pequena numa tarja preta e frases de impacto vermelhas empilhadas, com soco e tremida. | motor |
| <img src="fontes/mostruario.jpg" width="160"> | `fontes` | `/fontes` | Troca a fonte de qualquer legenda: 37 fontes prontas (mostruário) ou qualquer uma do Google Fonts. | motor + uma legenda |

## Efeitos (somam com qualquer legenda)

| | Skill | Comando | O que faz | Precisa de |
|---|---|---|---|---|
|  | `efeitos` | `/efeitos` | Índice: mostra os pacotes instalados, aplica um ou mais e mistura duas legendas no mesmo vídeo. | motor + uma legenda |
| <img src="efeito-filme-antigo/exemplo.jpg" width="160"> | `efeito-filme-antigo` | `/efeito-filme-antigo` | Super 8 escuro: cor quente, grão forte, poeira, riscos e janela de projetor. | motor + uma legenda |
| <img src="efeito-manga/exemplo.jpg" width="160"> | `efeito-manga` | `/efeito-manga` | Luz dourada com traço de tinta, retícula e hachura de mangá e linhas de impacto. | motor + uma legenda |
| <img src="efeito-sonho/exemplo.jpg" width="160"> | `efeito-sonho` | `/efeito-sonho` | Brilho estourado suave, vazamentos de luz, poeira de luz flutuando e risco verde de glitch. | motor + uma legenda |
| <img src="efeito-vhs/exemplo.jpg" width="160"> | `efeito-vhs` | `/efeito-vhs` | Fita VHS: imagem macia, borda colorida, varredura, tracking e clarão nos cortes. | motor + uma legenda |
| <img src="efeito-sombrio/exemplo.jpg" width="160"> | `efeito-sombrio` | `/efeito-sombrio` | Frio e quase sem cor, com chuva fina e bordas pulsando em vermelho. | motor + uma legenda |
| <img src="efeito-cinema/exemplo.jpg" width="160"> | `efeito-cinema` | `/efeito-cinema` | Cor de cinema (azul-petróleo e laranja), feixes de luz e poeira de luz. | motor + uma legenda |
| <img src="efeito-rua/exemplo.jpg" width="160"> | `efeito-rua` | `/efeito-rua` | Escuro e contrastado, colagem de painéis e glitch nos cortes. | motor + uma legenda |

## Estilos de vídeo

| | Skill | Comando | O que faz | Precisa de |
|---|---|---|---|---|
| <img src="video-gif/exemplo.jpg" width="160"> | `video-gif` | `/video-gif` | Um GIF em loop sem emenda, ampliado com IA, no meio da tela vertical, com a legenda ao lado do personagem. | motor + uma legenda |
| <img src="video-narracao/exemplo.jpg" width="160"> | `video-narracao` | `/video-narracao` | Narração de um roteiro sobre cenas de fundo, com zoom lento e a referência no topo. | motor + uma legenda |
| <img src="video-fala/exemplo.jpg" width="160"> | `video-fala` | `/video-fala` | Cena com o áudio original: a legenda fica ao lado de quem fala, nunca em cima do rosto. | motor + uma legenda |
| <img src="edit-musica/exemplo.jpg" width="160"> | `edit-musica` | `/edit-musica` | Você digita um nome ("Goku", "Neymar"): ele busca artes que já existem, anima em camadas e corta na batida. | Python + ffmpeg (não precisa do motor) |
| <img src="video-longo/exemplo.jpg" width="160"> | `video-longo` | `/video-longo` | Vídeo horizontal para o YouTube normal (10 a 30 min), com legenda num canto e capítulos. | motor |
|  | `aesthetic` | `/aesthetic` | Tela cheia de imagens paradas que ganham vida: quadrinhos, estrelas, zoom e cortes na batida. | motor |

## Em breve
- `/musica`: biblioteca de músicas com ficha (clima, energia, ponto de entrada) e escolha automática da trilha certa para cada vídeo.

## Licenças de terceiros
- Fontes: pacotes @fontsource (licença OFL), instalados pelo `setup.sh`.
- Transcrição: modelo Whisper small (Apache-2.0), instalado pelo `setup.sh`.
- Ampliação com IA (video-gif): pesos do Real-ESRGAN (BSD 3-Clause), ver `video-gif/LICENCA-REAL-ESRGAN.txt`.
