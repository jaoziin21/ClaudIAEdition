# Editor no Piloto (repositório ClaudIAEdition) — COMECE AQUI

Produto à venda do usuário: pacote de skills para Claude Code que faz vídeos curtos (Reels, TikTok, Shorts) a partir de uma frase:
roteiro, texto, áudio, legenda, edição, música, efeitos e post. **"Tudo em uma skill só."** Nome comercial: **Editor no Piloto**
(não usar "Claude" no nome do produto: marca da Anthropic). O usuário fala português do Brasil, manda áudio pelo celular e quer
rapidez: faça, mostre, ajuste. Commit + push na `main` ao fim de cada etapa, sem perguntar.

## Regra nº 1: NÃO MISTURAR com o Getsêmani
- Este repositório = SÓ o produto e a venda.
- `jaoziin21/getsemani---canal-` = SÓ o canal cristão dele (motor original, vídeos, notas). Nada de venda entra lá.
- O produto copia do Getsêmani só a versão LIMPA (sem vozes, vídeos, músicas de terceiros, notas pessoais).
  Gerador: `venda/ferramentas/build_skills.py` (lê o motor do Getsêmani, escreve `skills/` PLANO; caminhos absolutos da sessão
  antiga, ajustar antes de rodar; ele apaga `skills/` e recria — depois mover cada skill para a pasta do grupo (ver abaixo), copiar
  de volta `skills/instalar.sh` (cópia em `venda/ferramentas/instalar.sh`) e `video-gif/LICENCA-REAL-ESRGAN.txt`, e rodar
  `python3 venda/ferramentas/readmes.py && node venda/ferramentas/capas.cjs` (READMEs e capas das pastas).

## Regras fixas que ele já cobrou
- **SEMPRE ATUALIZAR A PÁGINA (pedido dele, 14/out):** toda legenda, efeito, formato ou skill nova que entrar no produto entra
  TAMBÉM na página de vendas na mesma etapa: números (skills, legendas, efeitos, combinações), listas/tags, vitrines (compilados
  `legendas.mp4`/`efeitos.mp4` e quadradinhos `t-<nome>.mp4` via `venda/vitrine/monta.py` + `junta.sh`), carrossel das legendas,
  testador de fontes, capa dos efeitos, FAQ e oferta. Depois: copiar para `venda/site/`, publicar o artifact e mandar o link.
- **ElevenLabs: SEMPRE `generations_count: 1`. NUNCA 4.** (cada geração gasta crédito dele/do aluno). Em 13/out a conta grátis dele
  deu "Free Tier disabled (contas múltiplas)": voz agora = gravada por ele, Fish Audio, ou ElevenLabs pago.
- Fish Audio: ele diz que é gratuito e com vozes de personagens; NÃO colocar no produto a dica de criar outra conta quando os
  créditos acabam (fere os termos; risco de bloqueio dos alunos). Aviso sobre "voz de pessoa real" foi tirado da página a pedido dele.
- Página: nada com cara de IA. Ele REJEITOU: escuro + vermelho, escuro + amarelo, a seção "Combinações reais", a seção de nichos
  (Fé/Motivação/Anime/Futebol). Ele APROVOU: claro + azul cobalto, 3D, (o misturador "Monte sua combinação" foi aprovado em 13/out, mas em 14/out ele pediu para TIRAR: não recolocar).
- MÚSICAS (15/out): ele mandou ESQUECER o assunto ("esquece essa porra dessas músicas"). NÃO tocar mais no tema nem oferecer
  alternativas sem ele pedir. Estado: skill `/musicas` pronta (lista os nomes); os .mp3 dele de terceiros NÃO entram no produto
  (o sistema bloqueia; já explicado). Cópia das 13 músicas no canal: getsemani-videos/musicas/. Trilha original: `trilha/compor.py`.
- NÃO escrever que o plano pago do Claude (Pro) é obrigatório (pedido dele, 14/out: testou no chat dele e gerou vídeo, só mais
  devagar). Escrever "conta no Claude; com o Pro sai mais rápido e com mais limite". Comando que o comprador digita: "instalar".
  Textos para o comprador em português correto (ele cobrou "instala" sem o R).
- Sempre deixar claro que dá para juntar legenda + fonte de outra + vários efeitos (ex.: Sample Yellow com a letra gótica da Street).
- Fundo dos vídeos: procurar você mesmo (skill `buscar-midia`) antes de pedir. Pixabay/Pexels bloqueados na rede da nuvem;
  Wikimedia (limite de requisições) e Internet Archive funcionam (NASA "EarthInHd" e "Gulliver's Travels 1939" = domínio público).

## Onde está cada coisa
- `skills/` — 38 skills + motor, cada uma independente, DIVIDIDAS EM GRUPOS (pedido dele, 14/out: "não joga tudo numa pasta só"):
  `1-base/` (motor), `2-roteiro-voz-post/`, `3-legendas/`, `4-efeitos/`, `5-formatos-de-video/`. Cada grupo tem README com vitrine
  e `capa.png`. Instalação: `bash skills/instalar.sh <pasta-do-canal> [skills ou grupos]` (ex.: `legendas efeitos`); no canal do
  aluno tudo fica plano em `.claude/skills/<nome>/`. Catálogo: `skills/README.md`. Skill nova: pasta no grupo certo + uma linha em
  `GRUPOS` no `venda/ferramentas/readmes.py` + rodar readmes.py e capas.cjs.
  Testado instalando só motor + 1 skill numa pasta vazia.
  FEITO 15/out: `/musicas` (`2-roteiro-voz-post/musicas/`): mostra o NOME de todas as músicas (`arquivos/musicas/LISTA.md` → motor/musicas/),
  escolhe, começa já tocando, mixa e confere o volume nas pausas. Os .mp3 das 13 músicas dele NÃO estão no repositório (público =
  distribuir música de terceiros; o sistema bloqueou): ficam só locais em `venda/musicas/` (no .gitignore) e no canal
  (getsemani-videos/musicas/). Quando ele deixar o repositório PRIVADO: mover para `skills/2-roteiro-voz-post/musicas/arquivos/musicas/`.
- `venda/entrega/` — o que o COMPRADOR recebe (14/out): `CLAUDE.md` (o Claude dele lê e instala tudo quando ele escreve "instala";
  a pasta descompactada vira o canal), `guia.html` → `COMECE-AQUI.pdf` (7 páginas: caminhos A app do Claude [recomendado],
  B terminal, C nuvem/celular via GitHub privado + upload do ZIP; primeiro vídeo; comandos; dicas; problemas), `TERMOS-DE-USO.txt`,
  `LEIA-ME.txt`, `gitignore`. Gerar: `bash venda/ferramentas/gera_entrega.sh` → `venda/entrega/saida/Editor-no-Piloto.zip`
  (fora do git: o repositório é público). Rodar de novo sempre que mudar skill. Testado: descompactar + instalar + setup.sh ok.
- `venda/PLANO.md` — plano do produto e da venda (decisões e etapas).
- `venda/pagina/editor-no-piloto.html` — página de vendas (fonte, com `vid/` e `img/`). Publicada como artifact privado:
  https://claude.ai/artifact/MpJwaRJrwGDGDabHLxzd4v (atualizar com Artifact publish + `url`, depois de ler).
- `venda/pagina/editor-no-piloto-v2.html` — VERSÃO NOVA (15/out) no estilo do modelo que ele desenhou (creme + preto + bronze,
  monitor no topo, faixas de legendas/efeitos, oferta escura, FAQ + selo de garantia). Artifact: https://claude.ai/artifact/UteKgi6mFeciysfYycxupk
  Preço provisório R$ 27,99 (ele ainda não fechou; quer preço baixo). SEM WhatsApp/grupo/suporte (ainda não existe), SEM
  depoimentos, "+1.000 criadores" ou visualizações inventadas, SEM preço "de/por" falso. Ele vai comparar com a atual e escolher.
  Ajustes dele (15/out): topo = botão 3D "Quero acessar agora" (brilho + anel pulsando) e vídeo de Jesus Lucas 11:5-13 no monitor
  (`vid/hero-jesus.mp4`, só a voz; ele vai GRAVAR um vídeo dele explicando para pôr ali). "Veja o resultado na prática" = SÓ o vídeo,
  SEM títulos/subtítulos, TODOS com "Ativar som" (um som por vez), vídeos inteiros do canal com voz sem música, recorte 1080x940
  (`crop=1080:940:0:420,scale=540:-2`, do `final_voz_fim.mp4`/`final_voz.mp4` do projeto). Ordem (15/out, pedido dele: Toji e os de
  ontem/hoje primeiro, manter Lucas): `ex-toji-provocacao`, `ex-toji-sol`, `ex-pedro` (GIFs do Toji), `ex-creio` (The Chosen),
  `ex-salmo13`, `ex-jesus` (Amigo à meia-noite), `ex-lucas11` (1º vídeo do canal). Saíram da v2: ex-davi, ex-moises, ex-marta.
- `venda/site/` — a mesma página pronta para hospedar (`index.html` + vídeos, 28 MB). Ele recebeu `editor-no-piloto-site.zip`.
- `venda/vitrine/` e `venda/ferramentas/monta.py`, `junta.sh` — geram os compilados (13 legendas / 10 efeitos na mesma cena de anime). Rodar UM monta.py por vez
  (legendas e efeitos ao mesmo tempo misturam os arquivos do motor); depois `bash venda/vitrine/junta.sh` (copia para pagina/ e site/).
- `venda/demo-recomecar/` — vídeo "Mandei uma frase. Isso voltou." (feito de verdade: roteiro, voz ElevenLabs, NASA, Sample Yellow
  + fonte gótica pirata-one + cinema + sonho, trilha original) + `chat.html` (abertura) + NOTAS.md.

## Página de vendas (estado em 17/out: 38 skills, 14 legendas, 10 efeitos, +530 mil combinações = 14 legendas × 37 fontes × 2^10 efeitos)
Clara, azul cobalto, fontes Bricolage Grotesque + Geist. Seções: topo 3D (celular inclinado com legenda/comandos saindo da tela,
vídeo "mandei uma frase") + BOTÃO 3D grande centralizado embaixo (pedido 14/out; no celular vem antes do celular 3D) → números → "Tudo em uma skill só" (7 cartões que se juntam ao rolar e terminam encaixados num bloco; o cartão preto "Editor no Piloto" do fim foi TIRADO a pedido dele 14/out)
→ dores que viram (flip) + calculadora de horas → compilados (13 legendas, 10 efeitos) → conversa animada (como funciona) →
equipe (6 skills) → carrossel 3D das 13 legendas → testador de fontes (as 13 legendas, cada uma com a fonte original ou a escolhida) → capa 3D dos 10 efeitos → formatos → antes/depois arrastável
("1 Samuel 16") → comparação em 3 colunas → "Só de uma coisa: Claude Code" + bônus → oferta (borda girando) → FAQ → final 3D.
Sem preço e sem link de pagamento ainda (botões vão para #oferta). Garantia de 7 dias escrita na página.

## Próximos passos combinados
1. Ele vai **gravar um vídeo aparecendo e falando** (roteiro sugerido: "Já pensou juntar roteiro, texto, áudio, legenda, edição,
   música e efeitos em uma skill só? É isso que o Editor no Piloto faz…"). Editar com a skill video-fala + inserir a tela do chat e o
   vídeo da Terra no meio. Pode virar o vídeo do topo da página.
2. **Vender:** recomendação = **Kirvano** (checkout, Pix, entrega do ZIP, afiliados, sem mensalidade) + página no **Netlify Drop**
   (grátis; domínio .com.br no registro.br opcional). Shopify só se um dia tiver loja com vários produtos.
   Quando ele mandar o link de checkout: colocar em todos os botões (topo, oferta, final, barra do celular) e regerar `venda/site/`.
3. FEITO 14/out: ZIP de entrega + guia PDF + termos de uso (licença pessoal; permite vídeos para clientes — confirmar com ele).
   Ainda a fazer quando ele pedir: política de privacidade e e-mail de contato no rodapé da página; pixel do Meta/TikTok; preço;
   subir o ZIP na Kirvano.
4. **EFEITOS NOVOS (14/out): ele vai MANDAR PROMPTS de cada efeito que quer.** NÃO inventar a lista (ele recusou Brasas/Câmera
   na mão/Zoom/Prisma/Neve/Faixas/Duotone com "naooo"). Para cada prompt: criar no motor do Getsêmani (`engine/efeitos/`:
   `video/*.txt` fragmento ffmpeg e/ou `tela/*.js` EFX.add, entrada em `efeitos.json` + `pacotes.json`), teste de 5 s na cena da
   vitrine (`venda/ferramentas/monta.py`), mandar para aprovar; aprovado → pasta `skills/4-efeitos/efeito-<nome>/` (SKILL.md,
   arquivos/, exemplo.jpg), linha em `GRUPOS` do readmes.py, rodar readmes.py + capas.cjs + gera_entrega.sh.
   Antigo: legendas novas criadas do zero (ideias: Cinética 3D, Recorte/colagem, Neon,
   Holograma) e efeitos novos (Brasas, Câmera na mão, Zoom na batida, Prisma, Neve/poeira, Faixas de cinema, Duotone).
   Fazer teste de 5 s de cada para ele aprovar antes de virar comando.
   FEITO 14/out: `/efeito-xerox` (Xerox Halftone / Pixel Sort, prompt dele) APROVADO e no produto. É o 1º efeito de PROCESSO
   (`motor/efeitos/processo/xerox.py`, numpy + OpenCV, quadro a quadro, nos cortes ou em `momentos`); o `faixa.mjs` do motor roda
   esse tipo no fim.
   FEITO 14/out: `/efeito-parallax` (Parallax Cutout / Temporal Collage, prompt dele) APROVADO ("ok") e no produto.
   Processo com recorte rembg `u2net_human_seg` (setup.sh instala rembg só se a skill estiver; modelo 176 MB baixa no 1º uso)
   ou máscara própria. Exemplo-detalhe = dançarino de Kimberly Keyes, CC BY 4.0 (crédito no SKILL.md).
   FEITO 14/out (noite), tudo aprovado por ele ("pode aprovar todos"): legendas NOVAS a partir de vídeos de referência dele
   (`/black-sample`, `/black-point`, `/bruce`, `/basic-on`) em `skills/3-legendas/`, e efeito `/efeito-black-and-white`
   (P&B duro granulado + variação `black-white-claro` p/ contraluz) em `skills/4-efeitos/`. Basic On leva a fonte Nimbus Sans Bold
   (= Helvetica Bold, URW, AGPL c/ exceção de fonte; arquivos de licença juntos em `arquivos/fontes/nimbus-sans/`).
   render_lado.mjs do motor passa: glitch, piscar, reticencias, coresChave, credito, cor2, falante/falantes.
   Página atualizada com tudo isso (14/out, noite).
   FEITO 17/out: legenda `/getsup` (`skills/3-legendas/getsup/`, referência TikTok dele, APROVADA no canal): Times (Tinos) apertada,
   branca pequena somando palavras secas + letreiro VERMELHO (empilhado minúsculo ou versal espaçada); filtro_getsup.txt. Vitrine s13
   ("EU NÃO TENHO INIMIGOS", janela 88,6–92,3 s, look caixa) → legendas.mp4 + t-getsup.mp4; carrossel, testador (chip "gs"),
   números 14/38/+530 mil nas páginas v1, v2 e site/; readmes + capas + gera_entrega (ZIP: 39 pastas = 38 skills + motor).
5. **Pendências dele:** deixar este repositório PRIVADO (está público e as skills estão aqui; daqui não dá para mudar a visibilidade —
   ele faz em Settings → Change visibility).
