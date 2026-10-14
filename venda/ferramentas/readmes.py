#!/usr/bin/env python3
"""Escreve skills/README.md (catálogo) e o README.md de cada pasta de grupo a partir da lista abaixo.
Skill nova = acrescentar uma linha em GRUPOS, pôr a pasta no grupo certo e rodar:
    python3 venda/ferramentas/readmes.py && node venda/ferramentas/capas.cjs
"""
import os

S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'skills')

GRUPOS = [
    ('1-base', 'base', 'Base', 'A base que todas as outras skills usam. O instalador coloca ela junto sempre, você não precisa pedir.', [
        ('motor', '—', 'O motor de edição: instala o que precisa, junta e normaliza a voz, acha o tempo de cada palavra usando o seu texto, monta o fundo, renderiza a legenda, mistura a música e confere o vídeo final.', 'Node.js 20+, Python 3.10+, ffmpeg'),
    ]),
    ('2-roteiro-voz-post', 'roteiro-voz-post', 'Começo, roteiro, voz e post', 'Tudo o que vem antes e depois da edição: você conta a ideia, ele escreve, narra, acha o fundo e entrega o texto para postar.', [
        ('comecar', '/comecar', 'Você conta a ideia do canal ("quero um canal de motivação com cenas de anime"). Ele faz poucas perguntas, cria o perfil do canal e sugere legenda, efeito, formato e voz.', '—'),
        ('roteiro', '/roteiro', 'A partir de um tema, entrega 3 roteiros com 3 ganchos cada, de 45 a 60 segundos, com linguagem de gente e sem cara de texto de IA.', '—'),
        ('voz', '/voz', 'Gera a narração pelo ElevenLabs conectado, ou passa o passo a passo do Fish Audio (gratuito, vozes de personagens), ou usa a sua voz gravada.', 'conta no ElevenLabs ou Fish Audio'),
        ('buscar-midia', '/buscar-midia', 'Procura GIFs, fotos, animações e cenas na internet, mostra as opções, baixa a escolhida e anota a fonte. Diz quais sites liberar se a rede bloquear.', 'acesso à internet'),
        ('post', '/post', 'Quando o vídeo é aprovado, entrega título, legenda do Instagram/TikTok, descrição e tags do YouTube, além de horários para postar.', '—'),
    ]),
    ('3-legendas', 'legendas', 'Legendas', 'Cada uma é um estilo completo de legenda animada. Dá para trocar a fonte de qualquer uma (`/fontes`) e somar os efeitos que quiser.', [
        ('sample-yellow', '/sample-yellow', 'Legenda de TV amarela em itálico, palavra por palavra numa caixinha escura. Embaixo ou em 2 linhas ao lado do personagem.', 'motor'),
        ('legenda-dinamica', '/legenda-dinamica', 'Serifa itálica elegante ao lado de quem fala, mudando de canto; palavra-chave vermelha; vídeo escuro com cara de filme.', 'motor'),
        ('legenda-3d-invisivel', '/legenda-3d-invisivel', 'Uma palavra por vez no centro, maiúscula grossa com relevo 3D; palavra-chave azul-gelo; textura de mangá.', 'motor'),
        ('mistury', '/mistury', 'Cada frase vira um cartaz com fontes misturadas: palavra forte grande, apoio pequeno e cursiva escrita na hora.', 'motor'),
        ('street', '/street', 'Legenda pequena sílaba por sílaba e gritos GIGANTES em letra gótica, com colagem de outros momentos do vídeo.', 'motor'),
        ('rocks', '/rocks', 'Maiúsculas serifadas cromadas num plano inclinado, em escada, com capitular gigante e cara de VHS.', 'motor'),
        ('samplerocks', '/samplerocks', 'O layout inclinado do Rocks com letra sem serifa branca e palavras amarelas que entram esticadas.', 'motor'),
        ('invisible', '/invisible', 'A letra é feita da própria imagem do vídeo, como vidro, e pega as cores de cada cena.', 'motor'),
        ('red-sharp', '/red-sharp', 'Legenda pequena numa tarja preta e frases de impacto vermelhas empilhadas, com soco e tremida.', 'motor'),
        ('fontes', '/fontes', 'Troca a fonte de qualquer legenda: 37 fontes prontas (mostruário) ou qualquer uma do Google Fonts.', 'motor + uma legenda'),
    ]),
    ('4-efeitos', 'efeitos', 'Efeitos', 'Pacotes de efeito que somam com qualquer legenda. Peça um ou vários no mesmo vídeo: eles se juntam na ordem pedida.', [
        ('efeitos', '/efeitos', 'Índice: mostra os pacotes instalados, aplica um ou mais e mistura duas legendas no mesmo vídeo.', 'motor + uma legenda'),
        ('efeito-filme-antigo', '/efeito-filme-antigo', 'Super 8 escuro: cor quente, grão forte, poeira, riscos e janela de projetor.', 'motor + uma legenda'),
        ('efeito-manga', '/efeito-manga', 'Luz dourada com traço de tinta, retícula e hachura de mangá e linhas de impacto.', 'motor + uma legenda'),
        ('efeito-sonho', '/efeito-sonho', 'Brilho estourado suave, vazamentos de luz, poeira de luz flutuando e risco verde de glitch.', 'motor + uma legenda'),
        ('efeito-vhs', '/efeito-vhs', 'Fita VHS: imagem macia, borda colorida, varredura, tracking e clarão nos cortes.', 'motor + uma legenda'),
        ('efeito-sombrio', '/efeito-sombrio', 'Frio e quase sem cor, com chuva fina e bordas pulsando em vermelho.', 'motor + uma legenda'),
        ('efeito-cinema', '/efeito-cinema', 'Cor de cinema (azul-petróleo e laranja), feixes de luz e poeira de luz.', 'motor + uma legenda'),
        ('efeito-rua', '/efeito-rua', 'Escuro e contrastado, colagem de painéis e glitch nos cortes.', 'motor + uma legenda'),
    ]),
    ('5-formatos-de-video', 'formatos-de-video', 'Formatos de vídeo', 'O tipo de vídeo: de onde vem a imagem e como ela se mexe. Junte com qualquer legenda e efeito.', [
        ('video-gif', '/video-gif', 'Um GIF em loop sem emenda, ampliado com IA, no meio da tela vertical, com a legenda ao lado do personagem.', 'motor + uma legenda'),
        ('video-narracao', '/video-narracao', 'Narração de um roteiro sobre cenas de fundo, com zoom lento e a referência no topo.', 'motor + uma legenda'),
        ('video-fala', '/video-fala', 'Cena com o áudio original: a legenda fica ao lado de quem fala, nunca em cima do rosto.', 'motor + uma legenda'),
        ('edit-musica', '/edit-musica', 'Você digita um nome ("Goku", "Neymar"): ele busca artes que já existem, anima em camadas e corta na batida.', 'Python + ffmpeg'),
        ('video-longo', '/video-longo', 'Vídeo horizontal para o YouTube normal (10 a 30 min), com legenda num canto e capítulos.', 'motor'),
        ('aesthetic', '/aesthetic', 'Tela cheia de imagens paradas que ganham vida: quadrinhos, estrelas, zoom e cortes na batida.', 'motor'),
    ]),
]


def foto(pasta, nome):
    for f in ('exemplo.jpg', 'mostruario.jpg'):
        if os.path.exists(os.path.join(S, pasta, nome, f)):
            return f'{nome}/{f}'


def readme_grupo(pasta, chave, titulo, intro, itens):
    n = pasta.split('-')[0]
    out = [f'<img src="capa.png" alt="{titulo}" width="100%">', '', f'# {n} · {titulo}', '', intro, '',
           f'**Instalar só este grupo:** `bash skills/instalar.sh ~/meu-canal {chave}`', '']
    com_foto = [i for i in itens if foto(pasta, i[0])]
    sem_foto = [i for i in itens if not foto(pasta, i[0])]
    for nome, cmd, desc, prec in sem_foto:
        cab = f'`{cmd}`' if cmd != '—' else f'`{nome}`'
        out += [f'### {cab}', desc, '', f'<sub>Pasta: [`{nome}/`]({nome}/) · Precisa de: {prec}</sub>', '']
    if com_foto:
        out += ['<table>']
        for i in range(0, len(com_foto), 3):
            out.append('<tr>')
            for nome, cmd, desc, prec in com_foto[i:i + 3]:
                out.append(f'<td width="33%" valign="top"><a href="{nome}/"><img src="{foto(pasta, nome)}" width="100%"></a><br>'
                           f'<b><code>{cmd}</code></b><br><sub>{desc}</sub></td>')
            out.append('</tr>')
        out += ['</table>', '']
    out += ['---', '[← voltar ao catálogo](../README.md)', '']
    open(os.path.join(S, pasta, 'README.md'), 'w').write('\n'.join(out))


def readme_catalogo():
    total = sum(len(g[4]) for g in GRUPOS)
    out = ['<img src="capa.png" alt="Editor no Piloto" width="100%">', '', '# Editor no Piloto · skills', '',
           f'{total} skills para o Claude Code que fazem vídeos curtos (Reels, TikTok, Shorts) a partir de uma frase: roteiro, voz, legenda,',
           'edição, música, efeitos e post. Cada skill é independente: instale todas ou só as que quiser. O **motor** vai junto sempre.', '',
           '## As pastas', '', '<table>']
    for i in range(0, len(GRUPOS), 2):
        out.append('<tr>')
        for pasta, chave, titulo, intro, itens in GRUPOS[i:i + 2]:
            out.append(f'<td width="50%" valign="top"><a href="{pasta}/"><img src="{pasta}/capa.png" width="100%"></a><br>'
                       f'<b><a href="{pasta}/">{pasta.split("-")[0]} · {titulo}</a></b> <sub>({len(itens)})</sub><br><sub>{intro}</sub></td>')
        out.append('</tr>')
    out += ['</table>', '', open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'catalogo_meio.md')).read().strip(), '',
            '## Todos os comandos', '']
    for pasta, chave, titulo, intro, itens in GRUPOS:
        out += [f'**[{titulo}]({pasta}/)**', '', '| Comando | O que faz | Precisa de |', '|---|---|---|']
        out += [f'| `{cmd if cmd != "—" else nome}` | {desc} | {prec} |' for nome, cmd, desc, prec in itens]
        out.append('')
    out += ['## Em breve',
            '- `/musica`: biblioteca de músicas com ficha (clima, energia, ponto de entrada) e escolha automática da trilha certa para cada vídeo.', '',
            '## Licenças de terceiros',
            '- Fontes: pacotes @fontsource (licença OFL), instalados pelo `setup.sh`.',
            '- Transcrição: modelo Whisper small (Apache-2.0), instalado pelo `setup.sh`.',
            '- Ampliação com IA (video-gif): pesos do Real-ESRGAN (BSD 3-Clause), ver `5-formatos-de-video/video-gif/LICENCA-REAL-ESRGAN.txt`.', '']
    open(os.path.join(S, 'README.md'), 'w').write('\n'.join(out))


for g in GRUPOS:
    readme_grupo(*g)
readme_catalogo()
print('READMEs escritos')
