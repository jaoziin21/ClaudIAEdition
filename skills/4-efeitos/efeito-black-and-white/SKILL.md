---
name: efeito-black-and-white
description: Pacote de efeitos "black-and-white": preto e branco DURO de filme puxado — sem cor, contraste extremo (pretos chapados, brancos estourados), grão grosso nos meios-tons, brilho suave nas luzes. Soma com qualquer legenda.
argument-hint: [legenda / vídeo ou pasta do projeto / observações]
---
# Efeito black-and-white

Preto e branco de foto de filme puxado no revelador: quase tudo vira preto ou branco, o grão aparece forte nos meios-tons
(rosto "pontilhado") e os pretos ficam limpos; um brilho suave escapa das luzes.
Partes: `black-white` (e a variação `black-white-claro`). Requer a skill **motor** e uma skill de legenda.
Exemplo: `exemplo.jpg` (com legenda) e `exemplo-detalhe.jpg` (filmagem real).

## Como aplicar
1. No `lado.json` do projeto: `"estilo": "<legenda>"` e `"pacote": "black-and-white"`.
2. CENA ESCURA OU EM CONTRALUZ (rosto virando silhueta preta nos quadros de teste): use `"efeitos": ["black-white-claro"]`
   no lugar do pacote — clareia as sombras antes do contraste. Não usar o "claro" em cena já clara (estoura).
3. Fundo: `cd motor && node faixa.mjs <vídeo de fundo> ../projetos/X` — o efeito substitui o filtro da legenda.
4. Quadros de teste (o rosto deve ficar granulado e legível) → render.
Combina bem com as legendas black-sample, basic-on e bruce.
