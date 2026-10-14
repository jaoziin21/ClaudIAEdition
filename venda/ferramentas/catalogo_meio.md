## Como instalar

**Pelo Claude Code (mais fácil):** abra o Claude Code na pasta do seu canal e peça:
> Instale as skills sample-yellow e video-gif do Editor no Piloto nesta pasta.

**Pelo terminal:**
```bash
# 1. descompacte o Editor no Piloto
# 2. instale na pasta do seu canal (o motor vai junto). Dá para pedir skills soltas ou grupos inteiros:
bash skills/instalar.sh ~/meu-canal sample-yellow efeito-vhs video-gif
bash skills/instalar.sh ~/meu-canal legendas efeitos
#    sem nomes = instala todas:
bash skills/instalar.sh ~/meu-canal
# 3. prepare o motor uma vez:
bash ~/meu-canal/motor/setup.sh
```
Grupos: `base`, `roteiro-voz-post`, `legendas`, `efeitos`, `formatos-de-video`.
No Windows, rode pelo **Git Bash** (vem com o Git para Windows) ou peça ao Claude Code para instalar.

**Quero só uma, sem instalador:** copie a pasta da skill para `meu-canal/.claude/skills/` e o conteúdo da pasta `arquivos/`
dela para `meu-canal/motor/` (faça o mesmo com a skill `motor`, em `1-base/`).

> As pastas de grupo (1-base, 3-legendas...) existem só para organizar aqui. No seu canal, todas as skills ficam lado a lado
> em `.claude/skills/`, que é onde o Claude Code procura.

## O que você precisa
- Claude Code com plano pago (Pro ou superior), no computador ou na nuvem.
- Node.js 20+, Python 3.10+ e ffmpeg (o `setup.sh` avisa o que falta; na nuvem já vem quase tudo).
- Para a voz: conta no ElevenLabs ou no Fish Audio (gratuito), ou a sua voz gravada.

## Junte do seu jeito (legenda + fonte + efeitos)
Tudo se combina. Peça em português, do seu jeito:
- **Legenda + fonte de outra:** "Faz com a /sample-yellow, só que com a fonte gótica da Street (pirata-one)". A legenda continua
  baixinha, com a caixinha e a animação da Sample Yellow; só a letra muda. Mostruário: `3-legendas/fontes/mostruario.jpg`.
- **Vários efeitos juntos:** "/red-sharp com /efeito-filme-antigo e /efeito-vhs". Os efeitos se somam, na ordem pedida.
- **Duas legendas no mesmo vídeo:** Sample Yellow no vídeo todo e Red Sharp só na frase de impacto.
- São mais de 40 mil combinações: 9 legendas × 38 opções de fonte × qualquer mistura dos 7 efeitos.

Por dentro (no `lado.json` do projeto): `"estilo": "sample-yellow", "trocaFonte": "pirata-one", "pacote": ["cinema", "sonho"]`.

## Como cada skill é organizada
```
3-legendas/              grupo (só para organizar)
  README.md              vitrine do grupo
  capa.png
  sample-yellow/
    SKILL.md             instruções que o Claude segue (vira o comando /sample-yellow)
    exemplo.jpg          como fica
    arquivos/            arquivos do motor que esta skill acrescenta (vão para motor/ na instalação)
```
