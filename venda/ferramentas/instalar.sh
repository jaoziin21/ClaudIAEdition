#!/usr/bin/env bash
# Instala skills na pasta do seu canal. O motor (base) sempre vai junto.
#   uso: bash skills/instalar.sh <pasta-do-canal> [skill ou grupo ...]
#   ex.: bash skills/instalar.sh ~/meu-canal sample-yellow efeito-vhs video-gif
#        bash skills/instalar.sh ~/meu-canal legendas efeitos     (grupos inteiros)
#        bash skills/instalar.sh ~/meu-canal                      (sem nomes = instala todas)
# Grupos: base, roteiro-voz-post, legendas, efeitos, formatos-de-video
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
DEST="$1"; [ -n "$DEST" ] || { echo "uso: bash skills/instalar.sh <pasta-do-canal> [skill ou grupo ...]"; exit 1; }
shift
mkdir -p "$DEST/.claude/skills" "$DEST/motor" "$DEST/projetos" "$DEST/entrada"

# pasta de uma skill (as skills ficam dentro das pastas de grupo: 3-legendas/sample-yellow ...)
achar() { for d in "$AQUI"/*/"$1"; do [ -f "$d/SKILL.md" ] && { echo "$d"; return; }; done; }
# skills de um grupo ("legendas" acha a pasta 3-legendas)
grupo() { for g in "$AQUI"/*-"$1"; do [ -d "$g" ] && for d in "$g"/*/; do [ -f "$d/SKILL.md" ] && basename "$d"; done; done; }

[ $# -eq 0 ] && set -- $(for d in "$AQUI"/*/*/SKILL.md; do basename "$(dirname "$d")"; done)
LISTA="motor"
for s in "$@"; do
  if [ -n "$(grupo "$s")" ]; then LISTA="$LISTA $(grupo "$s" | tr '\n' ' ')"
  elif [ -n "$(achar "$s")" ]; then LISTA="$LISTA $s"
  else echo "skill não encontrada: $s (veja a lista em skills/README.md)"; exit 1; fi
done

FEITAS=" "
for s in $LISTA; do
  case "$FEITAS" in *" $s "*) continue;; esac; FEITAS="$FEITAS$s "
  ORIG="$(achar "$s")"
  rm -rf "$DEST/.claude/skills/$s"
  cp -R "$ORIG" "$DEST/.claude/skills/$s"
  rm -rf "$DEST/.claude/skills/$s/arquivos"
  [ -d "$ORIG/arquivos" ] && cp -R "$ORIG/arquivos/." "$DEST/motor/"
  echo "instalada: $s"
done
chmod +x "$DEST/motor/"*.sh 2>/dev/null || true
echo
echo "Pronto. Agora rode uma vez:  bash \"$DEST/motor/setup.sh\""
echo "Depois abra o Claude Code na pasta \"$DEST\" e digite /comecar (se instalou) ou o comando da skill."
