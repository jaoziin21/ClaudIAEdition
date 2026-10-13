#!/usr/bin/env bash
# Instala skills na pasta do seu canal. O motor (base) sempre vai junto.
#   uso: bash skills/instalar.sh <pasta-do-canal> [skill ...]
#   ex.: bash skills/instalar.sh ~/meu-canal sample-yellow efeito-vhs video-gif
#        bash skills/instalar.sh ~/meu-canal            (sem nomes = instala todas)
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
DEST="$1"; [ -n "$DEST" ] || { echo "uso: bash skills/instalar.sh <pasta-do-canal> [skill ...]"; exit 1; }
shift
mkdir -p "$DEST/.claude/skills" "$DEST/motor" "$DEST/projetos" "$DEST/entrada"
[ $# -eq 0 ] && set -- $(cd "$AQUI" && ls -d */ | tr -d /)
LISTA="motor"; for s in "$@"; do [ "$s" = motor ] || LISTA="$LISTA $s"; done
for s in $LISTA; do
  [ -f "$AQUI/$s/SKILL.md" ] || { echo "skill não encontrada: $s (veja a lista em skills/README.md)"; exit 1; }
  rm -rf "$DEST/.claude/skills/$s"
  cp -R "$AQUI/$s" "$DEST/.claude/skills/$s"
  rm -rf "$DEST/.claude/skills/$s/arquivos"
  [ -d "$AQUI/$s/arquivos" ] && cp -R "$AQUI/$s/arquivos/." "$DEST/motor/"
  echo "instalada: $s"
done
chmod +x "$DEST/motor/"*.sh 2>/dev/null || true
echo
echo "Pronto. Agora rode uma vez:  bash \"$DEST/motor/setup.sh\""
echo "Depois abra o Claude Code na pasta \"$DEST\" e digite /comecar (se instalou) ou o comando da skill."
