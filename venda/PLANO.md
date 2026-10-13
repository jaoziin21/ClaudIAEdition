# Plano de venda — pacote de skills de edição com Claude Code
Atualizado: 13/out/2026. Decisão dele: vender SÓ as skills/comandos e o jeito de trabalhar (não os vídeos, voz, GIFs nem músicas dele).

## O produto — nome provisório: "Editor no Piloto"
PÚBLICO: QUALQUER NICHO (decisão dele, 13/out): cristão, motivação, anime, futebol...
`/comecar`: o aluno conta a ideia do canal ("quero um canal de X com Y") e o Claude monta o padrão dele.
Página explicativa (artifact): https://claude.ai/artifact/MpJwaRJrwGDGDabHLxzd4v — fonte em `venda/pagina/`.
Fish Audio (13/out, ele): gratuito, vozes de personagens de anime; entra na página como opção grátis de voz.
NÃO entra no produto a dica de criar outra conta quando os créditos acabam (vai contra os termos do site; risco de bloqueio dos alunos).
Repositório privado no GitHub que o aluno abre no Claude Code. Ele manda voz + texto + música/imagem e recebe o vídeo pronto + post.

| Módulo | O que tem | Situação |
|---|---|---|
| Legendas | `/sample-yellow`, `/legenda-dinamica`, `/legenda-3d-invisivel`, `/mistury`, `/street`, `/rocks`, `/samplerocks`, `/invisible`, `/red-sharp` | pronto (tirar referências ao canal) |
| Efeitos | `/efeitos` + 7 pacotes (`/efeito-cinema`, `-filme-antigo`, `-manga`, `-rua`, `-sombrio`, `-sonho`, `-vhs`) | pronto |
| Estilos de vídeo | Shorts de GIF, VERSO (narração), LADO (personagem falando), Aesthetic, vídeo longo horizontal | pronto, falta virar comando com nome |
| Música | skill NOVA `/musica`: biblioteca do aluno → escolhe a que combina com o vídeo, acha onde ela já está "tocando", mixa | A FAZER |
| Post | título, legenda IG/TikTok, descrição YouTube e tags (`viralizar.md`) | pronto, virar comando `/post` |
| Roteiro | `/roteiro`: o aluno só dá a ideia/tema; 3 propostas × 3 ganchos (sistema roteiro-getsemani generalizado) | ENTRA (decisão dele 13/out) |
| Voz | `/voz`: pede para o aluno conectar o ElevenLabs dele (claude.ai/customize/connectors) e gera a narração; alternativa: voz dele ou Fish Audio | A FAZER |
| Voz de personagem | guia passo a passo do Fish Audio (biblioteca de vozes ou clonar com áudio curto) | na página; virar guia no pacote |
| Base | instalador (Windows/Mac/nuvem), `/comecar` (configura canal, nicho, estilo), CLAUDE.md modelo que "aprende" o que o aluno aprova | A FAZER |

FLUXO DO ALUNO (13/out): conta a ideia → Claude escreve roteiro → gera a voz (ElevenLabs) → escolhe a música (`/musica`) → edita → post.
O aluno NÃO manda texto nem música; manda só a ideia e, se quiser, o GIF/vídeo de fundo.

## O que NÃO pode ir no produto
- Músicas: ELE QUER a skill `/musica` vindo com as músicas dele dentro (13/out: "vendo a skill, não as músicas").
  Alerta dado: arquivo de música de terceiros dentro de pacote pago = distribuição, mesmo sem cobrar "pela música".
  Alternativas propostas: catálogo com fichas (nome, artista, clima, ponto de entrada) + o aluno baixa os arquivos; ou músicas livres/licenciadas no pacote. DECISÃO PENDENTE.
- Voz, GIFs/clipes de anime, vídeos e notas pessoais (e-mail, Drive).
- Histórico do git deste repositório (3 GB). O produto nasce num repositório NOVO, gerado a partir deste.
- Skills de terceiros (Higgsfield, `watch`) são MIT: podem ir com o arquivo LICENSE, ou ficar como "instalar à parte".

## Custo para o aluno (confirmado na doc oficial, 13/out)
Claude Code NÃO funciona no plano grátis. Mínimo: Claude Pro, US$ 20/mês (ou API por uso, sem a versão na nuvem).
Render, transcrição e mixagem rodam no computador dele com programas grátis → sem custo extra por vídeo. Dizer isso na página.
Não usar a marca Claude/Anthropic como se fosse produto oficial.

## Situação das skills (13/out)
PRONTAS em `skills/` (testadas instalando só motor + 1 skill numa pasta vazia: Sample Yellow + VHS, 3D Invisível, Street):
motor, comecar, roteiro, voz, post, 9 legendas, efeitos + 7 pacotes, video-gif, video-narracao, video-fala, edit-musica, video-longo, aesthetic.
FALTA: `/musica` (esperando as músicas dele). Instalação: `bash skills/instalar.sh <pasta> [skills]`.

## Etapas
1. Decisões: nome, ~~público~~ (qualquer nicho), formato (só skills ou skills + aulas), preço, plataforma (Kiwify/Hotmart).
2. Skill `/musica` (testar no canal dele primeiro, com as músicas que ele mandar).
3. Gerar o repositório do produto: limpo, genérico, instalador, `/comecar`, README, exemplos com material livre.
4. Beta com 3–5 pessoas (de graça, em troca de depoimento): medir quantos vídeos/dia cabem no Claude Pro.
5. Página de venda + entrega automática (pagamento → convite no repositório privado) + vídeos de bastidores no canal.
6. Lançamento e atualização mensal (estilos novos) para manter valor contra pirataria.

## Onde fica cada coisa
- PRODUTO e venda: este repositório (`jaoziin21/ClaudIAEdition`).
- Canal dele: `jaoziin21/getsemani---canal-` (motor, legendas, projetos). O produto copia de lá só a versão limpa dos comandos e do motor.
