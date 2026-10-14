# Pesquisa de assets existentes

## Do nome ao plano de buscas (subject.py)
`resolve(nome, contexto)` → entidade da tabela `KNOWN` (Goku, Naruto, Itachi, Madara, Sasuke, Luffy, Vegeta,
Thorfinn, Gojo, Jesus, Neymar, Cristiano Ronaldo, Thor, Batman…) com franquia, tipo (anime/heroi/atleta/religioso),
aliases, cenas famosas e o que EVITAR (ex.: Goku → evitar "Goku Black", Gohan, Vegito). Desambiguação pelo contexto
("Ronaldo" + "fenômeno" → Nazário; "Thor" + "God of War"). Fora da tabela → `confirmar: true`: confirme com
WebSearch e passe `--franquia/--tipo`. Para ampliar a tabela, acrescente em `KNOWN`.

`query_plan` gera buscas por categoria de plano (close, pose, ação, transformação, aberto, silhueta, contemplativo,
clipes) + cenas famosas; `--midia manga` troca por buscas de painel/capítulo/página P&B.

## Fontes
| fonte | módulo | licença |
|---|---|---|
| YouTube (resultados reais + quadros publicados `maxresdefault`, `maxres1..3`) | `search_youtube` | © dos detentores — avisar |
| Wikimedia Commons | `search_commons` (extmetadata: autor, LicenseShortName) | verificada pela API |
| Openverse | `search_openverse` | CC/PD verificada |
| Internet Archive | `search_archive` + `archive_files` (original de maior tamanho) | campo licenseurl/rights |
| The Met Open Access | `search_met` (isPublicDomain) | verificada |
| Art Institute of Chicago | `search_aic` (is_public_domain, IIIF 1686 px) | verificada |
| Google Images / Pinterest / Bing / ArtStation / Pixiv / DeviantArt / oficiais | agente: WebSearch → página original → `aml.py candidato` → `baixar` | ler na página; se não houver, "não verificada" |

Google/Pinterest servem para DESCOBRIR; baixe da página de origem (artista/estúdio/museu) a maior versão
legitimamente disponível. Resposta HTML/login/403 = registrar e procurar outra fonte (nunca contornar).

## Seleção (antes e depois de baixar)
1. Antes: `score_candidates` = relevância do título/canal (nome/alias presente, "evitar", sinais ruins: IA, fan-art,
   reação, tutorial, gameplay, cosplay, edit de terceiros; bons: oficial, raw, 4K, cena, episódio) + resolução +
   licença. `pick_downloads` garante categorias variadas e limita quadros por vídeo.
2. Depois (medido no arquivo): nitidez (variância do Laplaciano), contraste, brilho, cor, `chroma_frac` e
   `hue_spread` (mangá P&B ou tingido de uma cor), duplicatas por dHash, enquadramento pelo recorte
   (close/médio/aberto/silhueta/contemplativo/ação/clipe).
3. Curadoria visual pelo agente na folha numerada (outro personagem, texto, rascunho → reprovar).
4. `select_assets`: tira duplicatas, equilibra enquadramentos, prioriza qualidade + relevância.

## O que aconteceu no teste "Goku, só mangá" (11/out/2026)
- 3 rodadas, ~40 buscas reais no YouTube (única fonte acessível), 500+ candidatos, 150+ quadros baixados.
- "Manga animation" no YouTube = quase sempre colorização de fã → o filtro de matiz reprovou; sobraram 12 imagens
  únicas de traço de mangá do Goku (P&B/tingidas); 1 caiu depois na prévia (Goku + Jiren no mesmo recorte).
- Commons/Openverse/Archive/Google/Pinterest/sites de mangá: bloqueados pela rede (registrado no manifesto).
