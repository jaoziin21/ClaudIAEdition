---
name: voz
description: Gera a narração do roteiro aprovado: pelo ElevenLabs conectado ao Claude (pede ao usuário para conectar na primeira vez) ou com o passo a passo do Fish Audio (gratuito, vozes de personagens), ou usa a voz gravada do usuário. Use quando chegar a hora de narrar um roteiro ou o usuário pedir voz/áudio.
---
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
