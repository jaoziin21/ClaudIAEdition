# Editor no Piloto — instruções para o Claude

Esta pasta é o **Editor no Piloto**: um pacote de skills que faz vídeos curtos (Reels, TikTok, Shorts) a partir de uma frase.
Quem abriu esta pasta acabou de comprar e quase sempre **não é programador**. Fale português do Brasil, simples, sem termo técnico,
um passo de cada vez. Faça você mesmo tudo o que der (rodar comandos, instalar programas); só peça à pessoa o que só ela pode
fazer (clicar em "permitir", digitar a senha do computador, escolher um nome).

## Se ainda NÃO estiver instalado (não existe `.claude/skills/motor/` nesta pasta)
Na primeira mensagem da pessoa, seja ela qual for ("oi", "instalar", "como usa?"), conduza a instalação:

1. Dê as boas-vindas em 1 linha e explique: "esta pasta vai virar o seu canal: tudo o que eu editar fica aqui dentro".
   Se ela preferir outra pasta, use a que ela disser (no lugar de `.` abaixo).
2. Instale todas as skills nesta pasta:  `bash skills/instalar.sh .`
   **Windows:** os scripts precisam do Git Bash (vem com o Git para Windows). Se `bash` não existir, instale com
   `winget install -e --id Git.Git` e peça para a pessoa fechar e abrir o Claude Code de novo nesta pasta e dizer
   "continua a instalação".
3. Prepare o motor:  `bash motor/setup.sh`
   Se aparecer "FALTA instalar", instale você mesmo e rode de novo:
   - **Windows:** `winget install -e --id OpenJS.NodeJS.LTS`, `winget install -e --id Python.Python.3.12`,
     `winget install -e --id Gyan.FFmpeg`. Depois de instalar, os programas só aparecem num terminal novo: peça para a pessoa
     fechar e abrir o Claude Code de novo nesta pasta e dizer "continua a instalação".
   - **Mac:** se não tiver o Homebrew, passe a ela o comando de instalação do site brew.sh para colar no Terminal (pede a senha
     do Mac). Depois: `brew install node python ffmpeg`.
   - **Linux / nuvem:** `sudo apt-get install -y nodejs npm python3 python3-pip ffmpeg` (na nuvem quase tudo já vem instalado).
   A primeira preparação baixa uns 300 MB (fontes, transcrição e o navegador que desenha a legenda) e pode levar alguns minutos:
   avise antes.
4. **Na nuvem (claude.ai/code ou app do celular):** a pasta é um repositório do GitHub da pessoa, onde ela subiu o
   `Editor-no-Piloto.zip`. Descompacte, mova o conteúdo da pasta `Editor-no-Piloto/` para a RAIZ do repositório (o
   `.claude/skills/` precisa ficar na raiz para os comandos aparecerem), apague o .zip e a pasta vazia, instale e faça commit
   e push para não perder nada quando a sessão fechar. O `.gitignore` já impede de subir o `motor/node_modules`.
5. Termine dizendo: "Pronto! Feche e abra o Claude Code de novo nesta pasta (para ele carregar os comandos) e digite **/comecar**."

## Se JÁ estiver instalado
Siga o pedido da pessoa usando as skills de `.claude/skills/`. Se ela não souber por onde começar, sugira `/comecar`
(configura o canal) e depois `/roteiro`. O guia completo para a pessoa está em `COMECE-AQUI.pdf`; o catálogo, em `skills/README.md`.

## Regras
- Voz pelo ElevenLabs: SEMPRE 1 geração por pedido (`generations_count: 1`). Cada geração gasta crédito da pessoa.
- Nunca apague arquivos da pessoa (vídeos, áudios, `projetos/`) sem perguntar.
- Se algo der erro, explique em 1 frase o que houve e tente resolver antes de pedir ajuda a ela.
