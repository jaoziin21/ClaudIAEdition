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
- **ElevenLabs: SEMPRE `generations_count: 1`. NUNCA 4.** (cada geração gasta crédito dele/do aluno). Em 13/out a conta grátis dele
  deu "Free Tier disabled (contas múltiplas)": voz agora = gravada por ele, Fish Audio, ou ElevenLabs pago.
- Fish Audio: ele diz que é gratuito e com vozes de personagens; NÃO colocar no produto a dica de criar outra conta quando os
  créditos acabam (fere os termos; risco de bloqueio dos alunos). Aviso sobre "voz de pessoa real" foi tirado da página a pedido dele.
- Página: nada com cara de IA. Ele REJEITOU: escuro + vermelho, escuro + amarelo, a seção "Combinações reais", a seção de nichos
  (Fé/Motivação/Anime/Futebol). Ele APROVOU: claro + azul cobalto, 3D, o misturador "Monte sua combinação" ("ficou monstruosa").
- Música de terceiros dentro do produto pago: avisado que é distribuição; decisão pendente (ver PLANO). Trilha original sem direitos:
  `trilha/compor.py` do motor.
- Sempre deixar claro que dá para juntar legenda + fonte de outra + vários efeitos (ex.: Sample Yellow com a letra gótica da Street).
- Fundo dos vídeos: procurar você mesmo (skill `buscar-midia`) antes de pedir. Pixabay/Pexels bloqueados na rede da nuvem;
  Wikimedia (limite de requisições) e Internet Archive funcionam (NASA "EarthInHd" e "Gulliver's Travels 1939" = domínio público).

## Onde está cada coisa
- `skills/` — 29 skills + motor, cada uma independente, DIVIDIDAS EM GRUPOS (pedido dele, 14/out: "não joga tudo numa pasta só"):
  `1-base/` (motor), `2-roteiro-voz-post/`, `3-legendas/`, `4-efeitos/`, `5-formatos-de-video/`. Cada grupo tem README com vitrine
  e `capa.png`. Instalação: `bash skills/instalar.sh <pasta-do-canal> [skills ou grupos]` (ex.: `legendas efeitos`); no canal do
  aluno tudo fica plano em `.claude/skills/<nome>/`. Catálogo: `skills/README.md`. Skill nova: pasta no grupo certo + uma linha em
  `GRUPOS` no `venda/ferramentas/readmes.py` + rodar readmes.py e capas.cjs.
  Testado instalando só motor + 1 skill numa pasta vazia. FALTA: `/musica` (ele vai mandar as músicas).
- `venda/entrega/` — o que o COMPRADOR recebe (14/out): `CLAUDE.md` (o Claude dele lê e instala tudo quando ele escreve "instala";
  a pasta descompactada vira o canal), `guia.html` → `COMECE-AQUI.pdf` (7 páginas: caminhos A app do Claude [recomendado],
  B terminal, C nuvem/celular via GitHub privado + upload do ZIP; primeiro vídeo; comandos; dicas; problemas), `TERMOS-DE-USO.txt`,
  `LEIA-ME.txt`, `gitignore`. Gerar: `bash venda/ferramentas/gera_entrega.sh` → `venda/entrega/saida/Editor-no-Piloto.zip`
  (fora do git: o repositório é público). Rodar de novo sempre que mudar skill. Testado: descompactar + instalar + setup.sh ok.
- `venda/PLANO.md` — plano do produto e da venda (decisões e etapas).
- `venda/pagina/editor-no-piloto.html` — página de vendas (fonte, com `vid/` e `img/`). Publicada como artifact privado:
  https://claude.ai/artifact/MpJwaRJrwGDGDabHLxzd4v (atualizar com Artifact publish + `url`, depois de ler).
- `venda/site/` — a mesma página pronta para hospedar (`index.html` + vídeos, 28 MB). Ele recebeu `editor-no-piloto-site.zip`.
- `venda/vitrine/` e `venda/ferramentas/monta.py`, `junta.sh` — geram os compilados (9 legendas / 7 efeitos na mesma cena de anime).
- `venda/demo-recomecar/` — vídeo "Mandei uma frase. Isso voltou." (feito de verdade: roteiro, voz ElevenLabs, NASA, Sample Yellow
  + fonte gótica pirata-one + cinema + sonho, trilha original) + `chat.html` (abertura) + NOTAS.md.

## Página de vendas (estado em 13/out)
Clara, azul cobalto, fontes Bricolage Grotesque + Geist. Seções: topo 3D (celular inclinado com legenda/comandos saindo da tela,
vídeo "mandei uma frase") → números → "Tudo em uma skill só" (7 cartões que se juntam ao rolar) → misturador legenda+fonte+efeitos
→ dores que viram (flip) + calculadora de horas → compilados (9 legendas, 7 efeitos) → conversa animada (como funciona) →
equipe (6 skills) → carrossel 3D das 9 legendas → testador de fontes → capa 3D dos 7 efeitos → formatos → antes/depois arrastável
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
4. **Depois (ele disse "a gente fala disso depois"):** legendas novas criadas do zero (ideias: Cinética 3D, Recorte/colagem, Neon,
   Holograma) e efeitos novos (Brasas, Câmera na mão, Zoom na batida, Prisma, Neve/poeira, Faixas de cinema, Duotone).
   Fazer teste de 5 s de cada para ele aprovar antes de virar comando.
5. **Pendências dele:** deixar este repositório PRIVADO (está público e as skills estão aqui); mandar as músicas para a `/musica`.
