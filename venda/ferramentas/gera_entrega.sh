#!/usr/bin/env bash
# Gera o ZIP que o comprador recebe: venda/entrega/saida/Editor-no-Piloto.zip
#   uso: bash venda/ferramentas/gera_entrega.sh      (rodar de novo sempre que mudar alguma skill)
set -e
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
ENT="$RAIZ/venda/entrega"; OUT="$ENT/saida"; P="$OUT/Editor-no-Piloto"
rm -rf "$OUT"; mkdir -p "$P"
node "$RAIZ/venda/ferramentas/pdf.cjs" "$ENT/guia.html" "$P/COMECE-AQUI.pdf"
cp "$ENT/CLAUDE.md" "$ENT/LEIA-ME.txt" "$ENT/TERMOS-DE-USO.txt" "$P/"
cp "$ENT/gitignore" "$P/.gitignore"
cp -R "$RAIZ/skills" "$P/skills"
find "$P" -name .DS_Store -delete
# teste: instala tudo numa cópia e confere que as 30 skills entraram
T="$(mktemp -d)"; cp -R "$P" "$T/canal"; (cd "$T/canal" && bash skills/instalar.sh . >/dev/null)
N=$(ls "$T/canal/.claude/skills" | wc -l); rm -rf "$T"
[ "$N" -ge 30 ] || { echo "ERRO: só $N skills instaladas"; exit 1; }
(cd "$OUT" && zip -qr -X Editor-no-Piloto.zip Editor-no-Piloto)
echo "ok: $N skills · $(du -h "$OUT/Editor-no-Piloto.zip" | cut -f1) · $OUT/Editor-no-Piloto.zip"
