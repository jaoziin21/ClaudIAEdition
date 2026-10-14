---
name: fontes
description: Troca a fonte de qualquer legenda por outra (37 fontes prontas ou qualquer fonte do Google Fonts): mostra o mostruário, aplica no projeto e testa. Use quando o usuário pedir outra fonte, letra diferente, "muda a fonte", ou quiser ver as fontes disponíveis.
---
# Fontes

Requer **motor** + a skill da legenda. Mostruário com as 37 fontes instaladas: `mostruario.jpg` nesta pasta (mande ao usuário).

## Trocar a fonte principal da legenda
No `lado.json` do projeto: `"trocaFonte": "bebas-neue"` (o nome em amarelo do mostruário). Quadros de teste, e pronto.
O motor usa o mesmo peso e estilo da original quando a fonte nova tiver; se não tiver, o mais perto.

## Trocar uma parte específica (legendas com mais de uma fonte)
`"trocaFonte": {"GRT": "pirata-one", "CAP": "dm-sans"}` — família da cena → fonte nova:

| Legenda | Famílias (fonte original) |
|---|---|
| Sample Yellow | `RB` (roboto itálico) |
| Dinâmica | `PF` (playfair-display itálico) |
| Street | `CAP` legenda (arimo) · `GRT` gritos gigantes (grenze-gotisch) |
| Rocks | `TN` (tinos) |
| Samplerocks | `AR` (archivo) |
| Invisible | `MONB` (montserrat 900) |
| Red Sharp | `TN` legenda (tinos) · `MONB` impacto (montserrat 900) · `BODI` última palavra (bodoni-moda itálico) |
| Mistury | `DID` `GOT` `ROM` `CON` `BEB` `MON` `BOD` (heróis) · `SCR` `MRD` `GV` (cursivas) |
| 3D Invisível | usa a chave própria `"fonte"`: montserrat-black, outfit, urbanist, montserrat, lexend… |

## Fonte nova (qualquer uma do Google Fonts)
1. Nome em minúsculas com hífen (ex.: "Anton" → `anton`, "Permanent Marker" → `permanent-marker`).
2. `cd motor && npm install @fontsource/<nome>` (precisa de internet; se bloquear, liberar `registry.npmjs.org`).
3. `"trocaFonte": "<nome>"` e quadros de teste. Para o mostruário mostrar a nova, gere a prévia com uma frase do roteiro.

## Dicas
- Legenda pequena e longa: fonte legível (dm-sans, manrope, archivo, roboto). Palavra única gigante: bebas-neue, luckiest-guy, bangers, anton.
- Cursivas (great-vibes, mr-dafoe, yellowtail) só em frases curtas.
- Guarde a escolha aprovada em `regras.md` para os próximos vídeos.
